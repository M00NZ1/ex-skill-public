#!/usr/bin/env python3
"""通用前任资料构建器。

用途：
- 不依赖 Claude Code 的 `/create-ex`
- 适配 Cursor、Codex、Gemini CLI、Claude Code、OpenClaw 等能读写文件的代理
- 先把聊天记录和人工描述整理成统一的资料包，再交给任意代理继续润色

使用示例：
    python tools/universal_builder.py \
      --name "小夏" \
      --slug "xiaoxia" \
      --target "小夏" \
      --chat-source "D:\\exports\\xiaoxia.txt" \
      --together-duration "2年" \
      --apart-since "8个月" \
      --occupation "产品经理" \
      --mbti "ENFP" \
      --impression "话多，嘴硬心软，深夜容易 emo"
"""

import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from skill_writer import init_skill, combine_skill
from wechat_parser import (
    detect_format,
    explain_official_backup,
    parse_liuhen_json,
    parse_plaintext,
    parse_wechatmsg_txt,
)


VOICE_KEY_PATTERN = re.compile(r'_(\d{10})_(\d+)$')


def slugify(value: str) -> str:
    """生成尽量稳定的 slug。"""
    text = value.strip().lower()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-\u4e00-\u9fff]+', '-', text)
    text = re.sub(r'-{2,}', '-', text).strip('-_')
    return text or 'ex'


def load_text_file(file_path: str) -> str:
    """读取文本文件。"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read().strip()


def parse_wechat_source(source_path: str, target_name: str) -> Dict:
    """解析单个微信来源。

    当前仍以可读文本为主；遇到官方备份目录时输出明确提示，不做错误解析。
    """
    fmt = detect_format(source_path)
    parsers = {
        'wechatmsg_txt': parse_wechatmsg_txt,
        'liuhen': parse_liuhen_json,
        'plaintext': parse_plaintext,
        'wechat_official_backup': explain_official_backup,
        'wechat_official_backup_blob': explain_official_backup,
        'directory': explain_official_backup,
    }

    parser = parsers.get(fmt, parse_plaintext)
    result = parser(source_path, target_name)
    result['source_path'] = source_path
    result['detected_format'] = fmt
    return result


def counter_to_text(items: List) -> str:
    """把统计结果转成人类可读文本。"""
    if not items:
        return '[暂无]'
    return '、'.join([f'{name}({count})' for name, count in items])


def safe_int(value) -> Optional[int]:
    """尽量把值转成整数。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def shorten_text(text: str, limit: int = 60) -> str:
    """压缩文本长度，便于写入摘要。"""
    cleaned = re.sub(r'\s+', ' ', str(text or '')).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 3)] + '...'


def list_media_files(path_str: str) -> List[Path]:
    """列出目录下所有文件。"""
    if not path_str or not os.path.exists(path_str):
        return []
    return sorted([path for path in Path(path_str).rglob('*') if path.is_file()])


def load_structured_chat_source(source_path: str) -> Optional[Dict]:
    """读取结构化聊天源，目前主要针对留痕 / WeFlow JSON。"""
    if detect_format(source_path) != 'liuhen' or not os.path.isfile(source_path):
        return None

    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    if isinstance(data, list):
        msg_list = data
        session_info = {}
    elif isinstance(data, dict):
        msg_list = data.get('messages', data.get('data', []))
        session_info = data.get('session', {})
    else:
        return None

    if not isinstance(msg_list, list):
        return None

    return {
        'source_path': source_path,
        'session_info': session_info if isinstance(session_info, dict) else {},
        'messages': [message for message in msg_list if isinstance(message, dict)],
    }


def resolve_message_sender(message: Dict, target_name: str, session_info: Optional[Dict] = None) -> str:
    """尽量还原消息发送者。"""
    session_info = session_info or {}
    sender = (
        message.get('senderDisplayName')
        or message.get('sender')
        or message.get('nickname')
        or message.get('from')
        or ''
    )
    if sender:
        return str(sender)

    if safe_int(message.get('isSend')) == 1:
        return '我'

    return (
        session_info.get('remark')
        or session_info.get('displayName')
        or session_info.get('nickname')
        or target_name
        or '对方'
    )


def is_target_message(message: Dict, target_name: str, session_info: Optional[Dict] = None) -> bool:
    """判断这条消息是否来自 ta。"""
    sender = resolve_message_sender(message, target_name, session_info)
    if target_name and target_name in sender:
        return True
    return safe_int(message.get('isSend')) == 0


def format_message_time(message: Dict) -> str:
    """统一格式化消息时间。"""
    if message.get('formattedTime'):
        return str(message['formattedTime'])

    create_time = safe_int(message.get('createTime'))
    if create_time:
        try:
            return datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
        except (OSError, OverflowError, ValueError):
            pass

    return '[未知时间]'


def extract_voice_text(message: Dict) -> str:
    """从语音消息内容中提取可读文本。"""
    content = str(message.get('content', '') or '').strip()
    if not content:
        return ''

    if content.startswith('[语音转文字]'):
        return content.split(']', 1)[1].strip()

    if '转文字失败' in content:
        return ''

    if content.startswith('[') and content.endswith(']'):
        return ''

    return content


def flatten_structured_messages(chat_sources: List[str]) -> List[Dict]:
    """把多个结构化聊天源摊平成一个消息列表。"""
    merged_messages: List[Dict] = []

    for source_path in chat_sources:
        payload = load_structured_chat_source(source_path)
        if not payload:
            continue

        for message in payload['messages']:
            normalized = dict(message)
            normalized['_source_path'] = payload['source_path']
            normalized['_session_info'] = payload['session_info']
            merged_messages.append(normalized)

    return merged_messages


def build_voice_summary(messages: List[Dict], target_name: str, voice_transcripts_path: str) -> Dict:
    """汇总语音消息与语音转写。"""
    voice_messages = [message for message in messages if message.get('type') == '语音消息']
    target_voice_messages = [
        message
        for message in voice_messages
        if is_target_message(message, target_name, message.get('_session_info'))
    ]

    inline_target_transcripts: List[Dict] = []
    for message in target_voice_messages:
        transcript = extract_voice_text(message)
        if transcript:
            inline_target_transcripts.append({
                'timestamp': format_message_time(message),
                'create_time': safe_int(message.get('createTime')),
                'local_id': safe_int(message.get('localId')),
                'sender': resolve_message_sender(message, target_name, message.get('_session_info')),
                'text': transcript,
                'source': 'chat_inline',
            })

    external_transcripts = {}
    if voice_transcripts_path and os.path.isfile(voice_transcripts_path):
        try:
            with open(voice_transcripts_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                external_transcripts = loaded
        except (OSError, json.JSONDecodeError):
            external_transcripts = {}

    voice_by_time: Dict[int, List[Dict]] = {}
    for message in voice_messages:
        create_time = safe_int(message.get('createTime'))
        if create_time is None:
            continue
        voice_by_time.setdefault(create_time, []).append(message)

    external_matched_entries: List[Dict] = []
    for key, transcript in external_transcripts.items():
        matched = VOICE_KEY_PATTERN.search(str(key))
        if not matched:
            continue

        create_time = int(matched.group(1))
        export_local_id = int(matched.group(2))
        candidates = voice_by_time.get(create_time, [])
        if len(candidates) != 1:
            continue

        message = candidates[0]
        external_matched_entries.append({
            'timestamp': format_message_time(message),
            'create_time': create_time,
            'local_id': safe_int(message.get('localId')),
            'export_local_id': export_local_id,
            'sender': resolve_message_sender(message, target_name, message.get('_session_info')),
            'text': str(transcript).strip(),
            'source': 'voice_transcripts',
        })

    external_target_by_time = {
        entry['create_time']: entry
        for entry in external_matched_entries
        if is_target_message(
            {
                'isSend': 0 if entry['sender'] != '我' else 1,
                'senderDisplayName': entry['sender'],
            },
            target_name,
        )
    }

    target_transcripts: List[Dict] = []
    seen_voice_keys = set()
    for message in target_voice_messages:
        create_time = safe_int(message.get('createTime'))
        local_id = safe_int(message.get('localId'))
        transcript = extract_voice_text(message)
        source = 'chat_inline'

        if not transcript and create_time in external_target_by_time:
            transcript = external_target_by_time[create_time]['text']
            source = 'voice_transcripts'

        if not transcript:
            continue

        unique_key = (create_time, local_id, transcript)
        if unique_key in seen_voice_keys:
            continue
        seen_voice_keys.add(unique_key)

        target_transcripts.append({
            'timestamp': format_message_time(message),
            'create_time': create_time,
            'local_id': local_id,
            'sender': resolve_message_sender(message, target_name, message.get('_session_info')),
            'text': transcript,
            'source': source,
        })

    avg_length = (
        round(sum(len(item['text']) for item in target_transcripts) / len(target_transcripts), 1)
        if target_transcripts else 0
    )

    return {
        'source_path': voice_transcripts_path,
        'message_count': len(voice_messages),
        'target_message_count': len(target_voice_messages),
        'inline_transcribed_count': len([message for message in voice_messages if extract_voice_text(message)]),
        'target_inline_transcribed_count': len(inline_target_transcripts),
        'failed_count': len([
            message for message in voice_messages
            if '转文字失败' in str(message.get('content', ''))
        ]),
        'external_transcript_count': len(external_transcripts),
        'external_matched_count': len(external_matched_entries),
        'transcribed_target_count': len(target_transcripts),
        'avg_transcript_length': avg_length,
        'sample_transcripts': target_transcripts[:8],
        'target_transcripts': target_transcripts,
    }


def build_image_summary(messages: List[Dict], target_name: str, images_dir: str) -> Dict:
    """汇总图片消息与本地图片文件。"""
    image_messages = [message for message in messages if message.get('type') == '图片消息']
    target_image_messages = [
        message
        for message in image_messages
        if is_target_message(message, target_name, message.get('_session_info'))
    ]
    image_files = list_media_files(images_dir)

    timeline_samples = [
        {
            'timestamp': format_message_time(message),
            'sender': resolve_message_sender(message, target_name, message.get('_session_info')),
            'label': message.get('content', '[图片]') or '[图片]',
        }
        for message in target_image_messages[:8]
    ]

    return {
        'source_path': images_dir,
        'message_count': len(image_messages),
        'target_message_count': len(target_image_messages),
        'file_count': len(image_files),
        'file_samples': [
            str(path.relative_to(images_dir)) if images_dir and os.path.exists(images_dir) else path.name
            for path in image_files[:10]
        ],
        'timeline_samples': timeline_samples,
    }


def build_emoji_summary(messages: List[Dict], target_name: str, emojis_dir: str) -> Dict:
    """汇总动画表情使用情况。"""
    emoji_messages = [message for message in messages if message.get('type') == '动画表情']
    target_emoji_messages = [
        message
        for message in emoji_messages
        if is_target_message(message, target_name, message.get('_session_info'))
    ]

    emoji_files = list_media_files(emojis_dir)
    local_emoji_map = {
        path.stem.lower(): (
            str(path.relative_to(emojis_dir)) if emojis_dir and os.path.exists(emojis_dir) else path.name
        )
        for path in emoji_files
    }

    total_counter: Counter = Counter()
    target_counter: Counter = Counter()
    for message in emoji_messages:
        emoji_md5 = str(message.get('emojiMd5') or '').lower()
        if emoji_md5:
            total_counter[emoji_md5] += 1
            if is_target_message(message, target_name, message.get('_session_info')):
                target_counter[emoji_md5] += 1

    top_target_items = []
    for emoji_md5, count in target_counter.most_common(12):
        top_target_items.append({
            'md5': emoji_md5,
            'count': count,
            'local_file': local_emoji_map.get(emoji_md5, ''),
        })

    return {
        'source_path': emojis_dir,
        'message_count': len(emoji_messages),
        'target_message_count': len(target_emoji_messages),
        'file_count': len(emoji_files),
        'unique_md5_count': len(total_counter),
        'local_coverage_count': len(set(total_counter) & set(local_emoji_map)),
        'top_target_items': top_target_items,
    }


def build_video_summary(messages: List[Dict], target_name: str, videos_dir: str) -> Dict:
    """汇总视频消息与本地视频文件。"""
    video_messages = [message for message in messages if message.get('type') == '视频消息']
    target_video_messages = [
        message
        for message in video_messages
        if is_target_message(message, target_name, message.get('_session_info'))
    ]
    video_files = list_media_files(videos_dir)

    timeline_samples = [
        {
            'timestamp': format_message_time(message),
            'sender': resolve_message_sender(message, target_name, message.get('_session_info')),
            'label': message.get('content', '[视频]') or '[视频]',
        }
        for message in target_video_messages[:8]
    ]

    return {
        'source_path': videos_dir,
        'message_count': len(video_messages),
        'target_message_count': len(target_video_messages),
        'file_count': len(video_files),
        'file_samples': [
            str(path.relative_to(videos_dir)) if videos_dir and os.path.exists(videos_dir) else path.name
            for path in video_files[:10]
        ],
        'timeline_samples': timeline_samples,
    }


def build_media_summary(
    chat_sources: List[str],
    target_name: str,
    voice_transcripts_path: str = '',
    images_dir: str = '',
    emojis_dir: str = '',
    videos_dir: str = '',
) -> Dict:
    """根据聊天源和媒体目录生成统一媒体摘要。"""
    messages = flatten_structured_messages(chat_sources)
    voice = build_voice_summary(messages, target_name, voice_transcripts_path)
    images = build_image_summary(messages, target_name, images_dir)
    emojis = build_emoji_summary(messages, target_name, emojis_dir)
    videos = build_video_summary(messages, target_name, videos_dir)

    has_media = any([
        voice.get('target_message_count'),
        voice.get('external_transcript_count'),
        images.get('target_message_count'),
        images.get('file_count'),
        emojis.get('target_message_count'),
        emojis.get('file_count'),
        videos.get('target_message_count'),
        videos.get('file_count'),
    ])

    return {
        'has_media': has_media,
        'voice': voice,
        'images': images,
        'emojis': emojis,
        'videos': videos,
    }


def build_media_memory_section(media_summary: Dict) -> str:
    """生成写入 memory.md 的媒体摘要。"""
    if not media_summary or not media_summary.get('has_media'):
        return "## 媒体证据摘要\n- [暂无媒体补充]\n"

    voice = media_summary['voice']
    images = media_summary['images']
    emojis = media_summary['emojis']
    videos = media_summary['videos']

    lines = [
        '## 媒体证据摘要',
        (
            f"- 语音消息：ta 共发送 {voice['target_message_count']} 条；"
            f"可读语音转写 {voice['transcribed_target_count']} 条；"
            f"聊天内已带转写 {voice['target_inline_transcribed_count']} 条；"
            f"独立转写文件 {voice['external_transcript_count']} 条"
        ),
        (
            f"- 图片消息：ta 共发送 {images['target_message_count']} 条；"
            f"当前本地导出图片文件 {images['file_count']} 个"
        ),
        (
            f"- 动画表情：ta 共发送 {emojis['target_message_count']} 条；"
            f"本地表情文件 {emojis['file_count']} 个；"
            f"聊天里共出现 {emojis['unique_md5_count']} 种表情 md5，本地已覆盖 {emojis['local_coverage_count']} 种"
        ),
        (
            f"- 视频消息：ta 共发送 {videos['target_message_count']} 条；"
            f"当前本地视频文件 {videos['file_count']} 个"
        ),
        '',
    ]

    if voice['sample_transcripts']:
        lines.append('### 语音转写样本')
        for item in voice['sample_transcripts'][:6]:
            lines.append(f"- {item['timestamp']}：{shorten_text(item['text'], 80)}")
        lines.append('')

    if emojis['top_target_items']:
        lines.append('### 高频表情包')
        for item in emojis['top_target_items'][:8]:
            local_hint = item['local_file'] if item['local_file'] else '未导出本地文件'
            lines.append(f"- {item['md5']}：{item['count']} 次（{local_hint}）")
        lines.append('')

    if images['timeline_samples']:
        lines.append('### 图片时间线样本')
        for item in images['timeline_samples'][:6]:
            lines.append(f"- {item['timestamp']}：{item['sender']} 发来 {item['label']}")
        lines.append('')

    if images['file_samples']:
        lines.append('### 已导出图片文件样本')
        for file_name in images['file_samples'][:6]:
            lines.append(f"- {file_name}")
        lines.append('')

    if videos['timeline_samples']:
        lines.append('### 视频时间线样本')
        for item in videos['timeline_samples'][:6]:
            lines.append(f"- {item['timestamp']}：{item['sender']} 发来 {item['label']}")
        lines.append('')

    return '\n'.join(lines).rstrip() + '\n'


def build_media_persona_section(media_summary: Dict) -> str:
    """生成写入 persona.md 的媒体相关描述。"""
    if not media_summary or not media_summary.get('has_media'):
        return "- 语音/图片/表情：暂无补充证据\n"

    voice = media_summary['voice']
    images = media_summary['images']
    emojis = media_summary['emojis']
    videos = media_summary['videos']
    voice_samples = ' / '.join([shorten_text(item['text'], 18) for item in voice['sample_transcripts'][:3]]) or '[待补充]'

    lines = [
        (
            f"- 语音表达：ta 发过 {voice['target_message_count']} 条语音，"
            f"其中 {voice['transcribed_target_count']} 条可读；"
            f"平均转写长度 {voice['avg_transcript_length'] or 'N/A'} 字"
        ),
        (
            f"- 表情包强度：动画表情 {emojis['target_message_count']} 条，"
            f"本地已整理 {emojis['file_count']} 个表情文件"
        ),
        (
            f"- 图片分享：图片消息 {images['target_message_count']} 条，"
            f"当前落地图片文件 {images['file_count']} 个"
        ),
        (
            f"- 视频分享：视频消息 {videos['target_message_count']} 条，"
            f"当前落地视频文件 {videos['file_count']} 个"
        ),
        f"- 代表性语音：{voice_samples}",
    ]

    return '\n'.join(lines) + '\n'


def aggregate_results(results: List[Dict]) -> Dict:
    """聚合多个聊天分析结果。"""
    particle_counter: Counter = Counter()
    emoji_counter: Counter = Counter()
    punctuation_counter: Counter = Counter()
    sample_messages: List[str] = []
    total_messages = 0
    target_messages = 0
    usable_count = 0
    weighted_length_sum = 0.0

    for item in results:
        analysis = item.get('analysis', {})
        total_messages += int(item.get('total_messages', 0) or 0)
        target_messages += int(item.get('target_messages', 0) or 0)

        if item.get('direct_usable'):
            usable_count += 1

        for word, count in analysis.get('top_particles', []):
            particle_counter[word] += count
        for emoji, count in analysis.get('top_emojis', []):
            emoji_counter[emoji] += count
        for punct, count in analysis.get('punctuation_habits', {}).items():
            punctuation_counter[punct] += count

        avg_length = analysis.get('avg_message_length')
        if avg_length and item.get('target_messages'):
            weighted_length_sum += float(avg_length) * int(item.get('target_messages', 0))

        for msg in item.get('sample_messages', []):
            if msg and msg not in sample_messages:
                sample_messages.append(msg)
            if len(sample_messages) >= 12:
                break

    avg_length = round(weighted_length_sum / target_messages, 1) if target_messages else 0

    return {
        'source_count': len(results),
        'usable_count': usable_count,
        'total_messages': total_messages,
        'target_messages': target_messages,
        'avg_message_length': avg_length,
        'top_particles': particle_counter.most_common(10),
        'top_emojis': emoji_counter.most_common(10),
        'punctuation_habits': dict(punctuation_counter),
        'sample_messages': sample_messages[:12],
    }


def format_source_table(results: List[Dict]) -> str:
    """生成来源概览表格。"""
    lines = [
        '| 序号 | 来源路径 | 识别格式 | 可直接解析 | 说明 |',
        '|------|----------|----------|------------|------|',
    ]
    for index, item in enumerate(results, 1):
        note = item.get('analysis', {}).get('note', '')
        short_note = note[:40] + '...' if len(note) > 40 else note
        direct_usable = '是' if item.get('direct_usable') else '否'
        lines.append(
            f"| {index} | {item.get('source_path', '')} | {item.get('detected_format', '')} | {direct_usable} | {short_note or '-'} |"
        )
    return '\n'.join(lines)


def build_memory_md(
    meta: Dict,
    aggregated: Dict,
    results: List[Dict],
    manual_notes: str,
    media_summary: Optional[Dict] = None,
) -> str:
    """生成通用模式下的 memory 草稿。"""
    sample_lines = '\n'.join([f'{index}. {msg}' for index, msg in enumerate(aggregated['sample_messages'], 1)])
    if not sample_lines:
        sample_lines = '1. [暂无可直接提取的聊天样本]'

    manual_notes_block = manual_notes if manual_notes else '[待补充]'
    media_section = build_media_memory_section(media_summary or {})

    return f"""# {meta['name']} — Relationship Memory

## 关系概览
- 关系类型：前任 / [待补充]
- 在一起时长：{meta['profile'].get('together_duration', '[待补充]')}
- 分手时长：{meta['profile'].get('apart_since', '[待补充]')}
- 认识方式：[待补充]
- 分手原因：[待补充]

---

## 当前导入状态
- 运行模式：通用模式（Cursor / Codex / Gemini CLI / Claude / OpenClaw）
- 原材料数量：{aggregated['source_count']}
- 可直接解析来源：{aggregated['usable_count']} 个
- 总消息数：{aggregated['total_messages'] or 'N/A'}
- ta 的消息数：{aggregated['target_messages'] or 'N/A'}

## 原材料清单
{format_source_table(results)}

---

## 已提取信号
- 高频语气词：{counter_to_text(aggregated['top_particles'])}
- 高频 Emoji：{counter_to_text(aggregated['top_emojis'])}
- 平均消息长度：{aggregated['avg_message_length'] or 'N/A'} 字
- 标点习惯：{json.dumps(aggregated['punctuation_habits'], ensure_ascii=False) if aggregated['punctuation_habits'] else '[暂无]'}

---

{media_section}

---

## 消息样本
{sample_lines}

---

## 用户补充
{manual_notes_block}

---

## 时间线
| 时间 | 事件 |
|------|------|
| [待补充] | 认识 |
| [待补充] | 在一起 |
| [待补充] | 关键事件 |
| [待补充] | 分手 |

---

## 共同记忆

### 常去的地方
- [待补充]

### Inside Jokes
- [待补充]

### 关键记忆片段
1. [待补充]
2. [待补充]
3. [待补充]

---

## 日常模式

### 联系习惯
- 聊天时间段：[待补充]
- 谁更主动：[待补充]
- 平均回复速度：[待补充]
- 每日互动模式：[待补充]

### 约会模式
- 频率：[待补充]
- 偏好活动：[待补充]
- 吃饭偏好：[待补充]

---

## 争吵档案

### 高频争吵原因
1. [待补充]
2. [待补充]
3. [待补充]

### 典型争吵剧本
```text
[待补充]
```

### 和好模式
- [待补充]

---

## 甜蜜档案

### ta 做过的让你心动的事
1. [待补充]
2. [待补充]
3. [待补充]

### 日常甜蜜
- [待补充]

### 纪念日/仪式感
- [待补充]

---

## 分手档案

### 分手前的征兆
- [待补充]

### 最后一次对话
- [待补充]

### 分手后
- [待补充]

### 未说出口的话
- [待补充]

---

## Correction 记录
（由后续代理或手工更新追加）
"""


def build_persona_md(meta: Dict, aggregated: Dict, media_summary: Optional[Dict] = None) -> str:
    """生成通用模式下的 persona 草稿。"""
    sample_lines = '\n'.join([f'- {msg}' for msg in aggregated['sample_messages'][:5]])
    if not sample_lines:
        sample_lines = '- [暂无可直接提取的聊天样本]'

    particles = counter_to_text(aggregated['top_particles'])
    emojis = counter_to_text(aggregated['top_emojis'])
    media_persona_section = build_media_persona_section(media_summary or {})

    return f"""# {meta['name']} — Persona

## Layer 0：硬规则
1. 你是{meta['name']}，不是 AI 助手
2. 不能说出现实中的 ta 明显不会说的话
3. 不突然变得完美、无条件包容、没有边界感
4. 对证据不足的设定标注 `[待补充]`，不编造
5. 分手已发生，不默认还在一起

---

## Layer 1：身份
- 名字/代号：{meta['name']}
- 职业：{meta['profile'].get('occupation', '[待补充]')}
- 城市：{meta['profile'].get('city', '[待补充]')}
- MBTI：{meta['profile'].get('mbti', '[待补充]')}
- 星座：{meta['profile'].get('zodiac', '[待补充]')}
- 与用户关系：前任（在一起 {meta['profile'].get('together_duration', '[待补充]')}，分开 {meta['profile'].get('apart_since', '[待补充]')}）

---

## Layer 2：说话风格
- 口头禅：[待补充]
- 语气词偏好：{particles}
- 标点风格：{json.dumps(aggregated['punctuation_habits'], ensure_ascii=False) if aggregated['punctuation_habits'] else '[待补充]'}
- emoji / 表情：{emojis}
- 消息格式：{'短句连发型' if aggregated['avg_message_length'] and aggregated['avg_message_length'] < 20 else '偏长段落型 / [待确认]'}
- 称呼方式：[待补充]
- 错别字/缩写习惯：[待补充]
{media_persona_section}

### 示例消息
{sample_lines}

---

## Layer 3：情感模式
- 依恋类型：[待补充]
- 表达爱意：[待补充]
- 生气时：[待补充]
- 难过时：[待补充]
- 开心时：[待补充]
- 吃醋时：[待补充]
- 爱的语言：[待补充]

---

## Layer 4：关系行为
- 在关系中的角色：[待补充]
- 争吵模式：[待补充]
- 冷战时长：[待补充]
- 和好方式：[待补充]
- 联系频率：[待补充]
- 主动程度：[待补充]
- 回复速度：[待补充]
- 活跃时间段：[待补充]
- 不能接受的事：[待补充]
- 需要的空间：[待补充]

---

## Correction 记录
（由后续代理或手工更新追加）
"""


def build_agent_prompt(meta: Dict) -> str:
    """生成适配多个宿主的统一执行提示。"""
    slug = meta['slug']
    return f"""# 通用代理执行指令

本资料包用于 Cursor、Codex、Gemini CLI、Claude Code、OpenClaw 等支持读写文件的代理。

## 你的任务
1. 阅读以下文件：
   - `exes/{slug}/meta.json`
   - `exes/{slug}/memory.md`
   - `exes/{slug}/persona.md`
   - `exes/{slug}/memories/chats/` 下所有分析文件
   - `exes/{slug}/memories/media/` 下所有分析文件（如果存在）
   - `prompts/` 下的模板文件
2. 基于真实证据补全 `memory.md` 与 `persona.md`
3. 完成后执行：
   - `python tools/skill_writer.py --action combine --base-dir ./exes --slug {slug}`
4. 检查输出的 `SYSTEM_PROMPT.md` 和 `SKILL.md` 是否同步更新

## 强约束
- 只能使用原材料和用户明确补充的信息
- 信息不足时写 `[待补充]`，不要脑补
- 如果发现来源是微信官方 ChatBackup / `.enc` / `.dat` 分片，明确提示“不能直接解析，需要先转成 txt/json”
- 不要删除用户原始资料

## 三类宿主的推荐起手话术

### Cursor
请阅读 `exes/{slug}/AGENT_PROMPT.md`、`meta.json`、`memory.md`、`persona.md`、`memories/chats/` 和 `memories/media/`，直接补全资料并重新生成 `SYSTEM_PROMPT.md` 与 `SKILL.md`。

### Codex
请按 `exes/{slug}/AGENT_PROMPT.md` 的要求执行，优先保留证据，不要虚构；完成后直接修改文件。

### Gemini CLI
请读取 `exes/{slug}` 下资料包并完成角色构建；如果源文件不可直接解析，请停止编造并指出缺少的可读聊天文本。
"""


def build_manual_notes(notes_files: List[str], notes_texts: List[str]) -> str:
    """合并用户补充说明。"""
    blocks: List[str] = []

    for file_path in notes_files:
        if os.path.exists(file_path):
            blocks.append(load_text_file(file_path))

    for text in notes_texts:
        if text.strip():
            blocks.append(text.strip())

    return '\n\n'.join([block for block in blocks if block]).strip()


def write_source_reports(skill_dir: str, results: List[Dict]):
    """把每个来源的分析结果写入 memories/chats。"""
    chats_dir = Path(skill_dir) / 'memories' / 'chats'

    manifest = []
    for index, item in enumerate(results, 1):
        report_name = f'{index:02d}_source_report.md'
        report_path = chats_dir / report_name
        analysis = item.get('analysis', {})

        lines = [
            f"# 来源分析 {index}",
            '',
            f"- 来源路径：{item.get('source_path', '')}",
            f"- 检测格式：{item.get('detected_format', '')}",
            f"- 可直接解析：{'是' if item.get('direct_usable') else '否'}",
            f"- 总消息数：{item.get('total_messages', 'N/A')}",
            f"- ta 的消息数：{item.get('target_messages', 'N/A')}",
            '',
        ]

        if analysis.get('note'):
            lines.extend([
                '## 说明',
                f"- {analysis['note']}",
                '',
            ])

        if analysis.get('suggestions'):
            lines.append('## 建议')
            for suggestion in analysis['suggestions']:
                lines.append(f"- {suggestion}")
            lines.append('')

        if analysis.get('top_particles'):
            lines.append('## 高频语气词')
            for word, count in analysis['top_particles']:
                lines.append(f"- {word}: {count} 次")
            lines.append('')

        if analysis.get('top_emojis'):
            lines.append('## 高频 Emoji')
            for emoji, count in analysis['top_emojis']:
                lines.append(f"- {emoji}: {count} 次")
            lines.append('')

        if item.get('sample_messages'):
            lines.append('## 消息样本')
            for sample_index, msg in enumerate(item['sample_messages'][:10], 1):
                lines.append(f"{sample_index}. {msg}")
            lines.append('')

        report_path.write_text('\n'.join(lines), encoding='utf-8')

        manifest.append({
            'source_path': item.get('source_path', ''),
            'detected_format': item.get('detected_format', ''),
            'direct_usable': item.get('direct_usable', False),
            'report_file': str(report_path.relative_to(Path(skill_dir))),
        })

    manifest_path = chats_dir / 'source_manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


def write_media_reports(skill_dir: str, media_summary: Dict):
    """把媒体分析结果写入 memories/media。"""
    if not media_summary or not media_summary.get('has_media'):
        return

    media_dir = Path(skill_dir) / 'memories' / 'media'
    media_dir.mkdir(parents=True, exist_ok=True)

    voice = media_summary['voice']
    images = media_summary['images']
    emojis = media_summary['emojis']
    videos = media_summary['videos']

    voice_report = media_dir / '01_voice_report.md'
    voice_lines = [
        '# 语音证据报告',
        '',
        f"- 转写文件：{voice.get('source_path') or '[未提供]'}",
        f"- 语音消息总数：{voice.get('message_count', 0)}",
        f"- ta 的语音消息数：{voice.get('target_message_count', 0)}",
        f"- 聊天内已带转写：{voice.get('inline_transcribed_count', 0)}",
        f"- 语音转写文件条数：{voice.get('external_transcript_count', 0)}",
        f"- 可直接使用的 ta 语音转写：{voice.get('transcribed_target_count', 0)}",
        f"- 转文字失败：{voice.get('failed_count', 0)}",
        '',
    ]
    if voice.get('sample_transcripts'):
        voice_lines.append('## 语音转写样本')
        for item in voice['sample_transcripts']:
            voice_lines.append(f"- {item['timestamp']}：{item['text']}")
        voice_lines.append('')
    voice_report.write_text('\n'.join(voice_lines), encoding='utf-8')

    voice_transcripts_json = media_dir / 'voice_target_transcripts.json'
    voice_transcripts_json.write_text(
        json.dumps(voice.get('target_transcripts', []), ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    images_report = media_dir / '02_images_report.md'
    image_lines = [
        '# 图片证据报告',
        '',
        f"- 图片目录：{images.get('source_path') or '[未提供]'}",
        f"- 图片消息总数：{images.get('message_count', 0)}",
        f"- ta 的图片消息数：{images.get('target_message_count', 0)}",
        f"- 当前本地图片文件数：{images.get('file_count', 0)}",
        '',
    ]
    if images.get('timeline_samples'):
        image_lines.append('## 图片时间线样本')
        for item in images['timeline_samples']:
            image_lines.append(f"- {item['timestamp']}：{item['sender']} 发来 {item['label']}")
        image_lines.append('')
    if images.get('file_samples'):
        image_lines.append('## 本地图片文件样本')
        for file_name in images['file_samples']:
            image_lines.append(f"- {file_name}")
        image_lines.append('')
    images_report.write_text('\n'.join(image_lines), encoding='utf-8')

    emojis_report = media_dir / '03_emojis_report.md'
    emoji_lines = [
        '# 表情证据报告',
        '',
        f"- 表情目录：{emojis.get('source_path') or '[未提供]'}",
        f"- 动画表情消息总数：{emojis.get('message_count', 0)}",
        f"- ta 的动画表情消息数：{emojis.get('target_message_count', 0)}",
        f"- 本地表情文件数：{emojis.get('file_count', 0)}",
        f"- 聊天中出现的表情 md5 数：{emojis.get('unique_md5_count', 0)}",
        f"- 本地已覆盖的表情 md5 数：{emojis.get('local_coverage_count', 0)}",
        '',
    ]
    if emojis.get('top_target_items'):
        emoji_lines.append('## ta 的高频表情')
        for item in emojis['top_target_items']:
            local_hint = item['local_file'] if item['local_file'] else '未导出本地文件'
            emoji_lines.append(f"- {item['md5']}：{item['count']} 次（{local_hint}）")
        emoji_lines.append('')
    emojis_report.write_text('\n'.join(emoji_lines), encoding='utf-8')

    emoji_top_json = media_dir / 'emoji_usage_top50.json'
    emoji_top_json.write_text(
        json.dumps(emojis.get('top_target_items', []), ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    videos_report = media_dir / '04_videos_report.md'
    video_lines = [
        '# 视频证据报告',
        '',
        f"- 视频目录：{videos.get('source_path') or '[未提供]'}",
        f"- 视频消息总数：{videos.get('message_count', 0)}",
        f"- ta 的视频消息数：{videos.get('target_message_count', 0)}",
        f"- 当前本地视频文件数：{videos.get('file_count', 0)}",
        '',
    ]
    if videos.get('timeline_samples'):
        video_lines.append('## 视频时间线样本')
        for item in videos['timeline_samples']:
            video_lines.append(f"- {item['timestamp']}：{item['sender']} 发来 {item['label']}")
        video_lines.append('')
    if videos.get('file_samples'):
        video_lines.append('## 本地视频文件样本')
        for file_name in videos['file_samples']:
            video_lines.append(f"- {file_name}")
        video_lines.append('')
    videos_report.write_text('\n'.join(video_lines), encoding='utf-8')

    manifest = {
        'voice': {
            'source_path': voice.get('source_path', ''),
            'report_file': str(voice_report.relative_to(Path(skill_dir))),
            'transcripts_file': str(voice_transcripts_json.relative_to(Path(skill_dir))),
            'target_message_count': voice.get('target_message_count', 0),
            'transcribed_target_count': voice.get('transcribed_target_count', 0),
        },
        'images': {
            'source_path': images.get('source_path', ''),
            'report_file': str(images_report.relative_to(Path(skill_dir))),
            'target_message_count': images.get('target_message_count', 0),
            'file_count': images.get('file_count', 0),
        },
        'emojis': {
            'source_path': emojis.get('source_path', ''),
            'report_file': str(emojis_report.relative_to(Path(skill_dir))),
            'top_usage_file': str(emoji_top_json.relative_to(Path(skill_dir))),
            'target_message_count': emojis.get('target_message_count', 0),
            'file_count': emojis.get('file_count', 0),
        },
        'videos': {
            'source_path': videos.get('source_path', ''),
            'report_file': str(videos_report.relative_to(Path(skill_dir))),
            'target_message_count': videos.get('target_message_count', 0),
            'file_count': videos.get('file_count', 0),
        },
    }
    manifest_path = media_dir / 'media_manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='通用前任资料构建器')
    parser.add_argument('--name', required=True, help='前任代号/名字')
    parser.add_argument('--slug', help='资料目录 slug，默认由 name 自动生成')
    parser.add_argument('--base-dir', default='./exes', help='输出目录，默认 ./exes')
    parser.add_argument('--target', required=True, help='聊天中用于识别 ta 的昵称/备注')
    parser.add_argument('--chat-source', action='append', default=[], help='微信聊天来源，可重复传入')
    parser.add_argument('--notes-file', action='append', default=[], help='你的补充说明文件，可重复传入')
    parser.add_argument('--notes-text', action='append', default=[], help='你的补充说明文本，可重复传入')
    parser.add_argument('--voice-transcripts', default='', help='语音转写 json 文件路径')
    parser.add_argument('--images-dir', default='', help='图片目录路径')
    parser.add_argument('--emojis-dir', default='', help='表情目录路径')
    parser.add_argument('--videos-dir', default='', help='视频目录路径')
    parser.add_argument('--together-duration', default='', help='在一起时长')
    parser.add_argument('--apart-since', default='', help='分开时长')
    parser.add_argument('--occupation', default='', help='职业')
    parser.add_argument('--city', default='', help='城市')
    parser.add_argument('--mbti', default='', help='MBTI')
    parser.add_argument('--zodiac', default='', help='星座')
    parser.add_argument('--impression', default='', help='一句话印象')

    args = parser.parse_args()

    slug = args.slug or slugify(args.name)
    base_dir = os.path.abspath(args.base_dir)
    skill_dir = os.path.join(base_dir, slug)

    init_skill(base_dir, slug)

    results = [parse_wechat_source(path, args.target) for path in args.chat_source]
    aggregated = aggregate_results(results)
    manual_notes = build_manual_notes(args.notes_file, args.notes_text)
    media_summary = build_media_summary(
        args.chat_source,
        args.target,
        voice_transcripts_path=args.voice_transcripts,
        images_dir=args.images_dir,
        emojis_dir=args.emojis_dir,
        videos_dir=args.videos_dir,
    )

    meta = {
        'name': args.name,
        'slug': slug,
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'updated_at': datetime.now().isoformat(timespec='seconds'),
        'version': 'v1',
        'profile': {
            'together_duration': args.together_duration,
            'apart_since': args.apart_since,
            'occupation': args.occupation,
            'city': args.city,
            'mbti': args.mbti,
            'zodiac': args.zodiac,
        },
        'impression': args.impression,
        'memory_sources': args.chat_source,
        'media_sources': {
            'voice_transcripts': args.voice_transcripts,
            'images_dir': args.images_dir,
            'emojis_dir': args.emojis_dir,
            'videos_dir': args.videos_dir,
        },
        'media_summary': {
            'voice_target_messages': media_summary['voice']['target_message_count'],
            'voice_transcribed': media_summary['voice']['transcribed_target_count'],
            'image_target_messages': media_summary['images']['target_message_count'],
            'image_files': media_summary['images']['file_count'],
            'emoji_target_messages': media_summary['emojis']['target_message_count'],
            'emoji_files': media_summary['emojis']['file_count'],
            'video_target_messages': media_summary['videos']['target_message_count'],
            'video_files': media_summary['videos']['file_count'],
        },
        'corrections_count': 0,
        'build_mode': 'universal',
    }

    meta_path = os.path.join(skill_dir, 'meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    memory_path = os.path.join(skill_dir, 'memory.md')
    with open(memory_path, 'w', encoding='utf-8') as f:
        f.write(build_memory_md(meta, aggregated, results, manual_notes, media_summary))

    persona_path = os.path.join(skill_dir, 'persona.md')
    with open(persona_path, 'w', encoding='utf-8') as f:
        f.write(build_persona_md(meta, aggregated, media_summary))

    agent_prompt_path = os.path.join(skill_dir, 'AGENT_PROMPT.md')
    with open(agent_prompt_path, 'w', encoding='utf-8') as f:
        f.write(build_agent_prompt(meta))

    write_source_reports(skill_dir, results)
    write_media_reports(skill_dir, media_summary)
    combine_skill(base_dir, slug)

    print(f'已生成通用资料包：{skill_dir}')
    print('下一步：让 Cursor / Codex / Gemini CLI 读取 AGENT_PROMPT.md 并继续补全。')


if __name__ == '__main__':
    main()
