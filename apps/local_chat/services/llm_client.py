"""大模型聊天调用。"""

from __future__ import annotations

import json
from typing import Dict, List

import httpx


OUTPUT_SCHEMA_DESCRIPTION = """你必须只返回一个 JSON 对象，不要输出 Markdown，不要输出代码块。
字段要求：
- reply_text: 字符串，真正发给用户的话
- emotion: 字符串，当前情绪标签
- emoji_text: 字符串，可以是 0 到 1 个 emoji 字符，没有就返回空字符串
- use_sticker: 布尔值，是否需要发本地表情包
- sticker_md5: 字符串，如果 use_sticker=true，则从候选表情 md5 中选择一个；否则返回空字符串
- sticker_reason: 字符串，为什么选这个表情包
- send_voice: 布尔值，是否建议发送语音
- voice_text: 字符串，如果 send_voice=true，给出更适合语音播报的文本；否则返回空字符串
"""

STICKER_MODE_PROMPTS = {
    'off': '当前用户关闭了自动表情包。你必须返回 use_sticker=false，sticker_md5=""。',
    'light': '当前用户要求自动表情包走“克制模式”：大多数回复不发表情包，只有明显适合撒娇、卖萌、委屈、起床、晚安、哄人、逗趣这类场景时才考虑。',
    'natural': '当前用户要求自动表情包走“贴近聊天记录模式”：可以参考原始习惯，但依然不要连续两条都发表情包，也不要长文本配表情包。',
}

STICKER_MODE_RULES = {
    'off': {
        'enabled': False,
        'min_gap': 999,
        'max_recent': 0,
        'max_reply_length': 0,
        'emoji_max_reply_length': 0,
    },
    'light': {
        'enabled': True,
        'min_gap': 4,
        'max_recent': 1,
        'max_reply_length': 18,
        'emoji_max_reply_length': 16,
    },
    'natural': {
        'enabled': True,
        'min_gap': 2,
        'max_recent': 2,
        'max_reply_length': 26,
        'emoji_max_reply_length': 22,
    },
}


def _extract_json_text(raw_text: str) -> str:
    """从模型回复中尽量提取 JSON。"""
    raw_text = raw_text.strip()
    if raw_text.startswith('{') and raw_text.endswith('}'):
        return raw_text

    if '```json' in raw_text:
        raw_text = raw_text.split('```json', 1)[1]
        raw_text = raw_text.split('```', 1)[0]
        return raw_text.strip()

    if '```' in raw_text:
        raw_text = raw_text.split('```', 1)[1]
        raw_text = raw_text.split('```', 1)[0]
        return raw_text.strip()

    start = raw_text.find('{')
    end = raw_text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return raw_text[start:end + 1]

    raise ValueError('模型没有返回可解析的 JSON')


def _history_item_to_prompt_text(item: Dict) -> str:
    """把前端历史消息还原成适合喂给模型的文本。"""
    parts = []
    content = str(item.get('content', '') or '').strip()
    emoji_text = str(item.get('emoji_text', '') or '').strip()
    sticker_md5 = str(item.get('sticker_md5', '') or '').strip()

    if content:
        parts.append(content)
    if emoji_text and emoji_text not in content:
        parts.append(f'[emoji={emoji_text}]')
    if sticker_md5:
        parts.append(f'[本条消息带了表情包 md5={sticker_md5}]')

    return '\n'.join(parts) if parts else '[空消息]'


def _recent_assistant_messages(history: List[Dict], limit: int = 6) -> List[Dict]:
    """提取最近几条助手消息，供媒体节流判断。"""
    result: List[Dict] = []
    for item in reversed(history):
        if item.get('role') != 'assistant':
            continue
        result.append(item)
        if len(result) >= limit:
            break
    return result


def _turns_since_last_assistant_sticker(history: List[Dict]) -> int:
    """计算距离上一条带表情包的助手消息有多少轮。"""
    turns = 0
    for item in reversed(history):
        if item.get('role') != 'assistant':
            continue
        sticker_md5 = str(item.get('sticker_md5', '') or '').strip()
        if sticker_md5:
            return turns
        turns += 1
    return 999


def _apply_local_media_policy(profile: Dict, history: List[Dict], parsed: Dict, sticker_mode: str) -> Dict:
    """在模型结果外再做一层本地节流，避免句句带表情包。"""
    mode = sticker_mode if sticker_mode in STICKER_MODE_RULES else 'light'
    rules = STICKER_MODE_RULES[mode]
    recent_assistants = _recent_assistant_messages(history, limit=6)
    recent_sticker_count = sum(
        1 for item in recent_assistants if str(item.get('sticker_md5', '') or '').strip()
    )
    turns_since_last_sticker = _turns_since_last_assistant_sticker(history)
    allowed_md5_set = {
        str(item.get('md5', '') or '').strip()
        for item in profile.get('sticker_candidates', [])
        if str(item.get('md5', '') or '').strip()
    }

    parsed['reply_text'] = str(parsed.get('reply_text', '') or '').strip()
    parsed['emotion'] = str(parsed.get('emotion', '') or '').strip()
    parsed['emoji_text'] = str(parsed.get('emoji_text', '') or '').strip()
    parsed['use_sticker'] = bool(parsed.get('use_sticker'))
    parsed['sticker_md5'] = str(parsed.get('sticker_md5', '') or '').strip()
    parsed['sticker_reason'] = str(parsed.get('sticker_reason', '') or '').strip()
    parsed['send_voice'] = bool(parsed.get('send_voice'))
    parsed['voice_text'] = str(parsed.get('voice_text', '') or '').strip()

    sticker_block_reasons = []
    if not rules['enabled']:
        sticker_block_reasons.append('当前已关闭自动表情包')
    if parsed['send_voice']:
        sticker_block_reasons.append('当前回复已选择语音')
    if len(parsed['reply_text']) > rules['max_reply_length']:
        sticker_block_reasons.append('当前回复偏长')
    if recent_assistants and str(recent_assistants[0].get('sticker_md5', '') or '').strip():
        sticker_block_reasons.append('上一条助手消息已带表情包')
    if turns_since_last_sticker < rules['min_gap']:
        sticker_block_reasons.append('距离上次表情包太近')
    if recent_sticker_count >= rules['max_recent']:
        sticker_block_reasons.append('最近几条助手消息里表情包偏多')
    if parsed['sticker_md5'] and parsed['sticker_md5'] not in allowed_md5_set:
        sticker_block_reasons.append('模型选择了本地不存在的表情包')

    if parsed['use_sticker'] and sticker_block_reasons:
        parsed['use_sticker'] = False
        parsed['sticker_md5'] = ''
        parsed['sticker_reason'] = '；'.join(sticker_block_reasons)

    emoji_block = False
    if parsed['send_voice']:
        emoji_block = True
    elif len(parsed['reply_text']) > rules['emoji_max_reply_length']:
        emoji_block = True
    elif recent_assistants and str(recent_assistants[0].get('emoji_text', '') or '').strip() and mode == 'light':
        emoji_block = True

    if emoji_block:
        parsed['emoji_text'] = ''

    return parsed


def _build_messages(profile: Dict, user_message: str, history: List[Dict], sticker_mode: str, manual_sticker_md5: str) -> List[Dict]:
    """构建发给模型的消息。"""
    sticker_lines = []
    for item in profile.get('auto_sticker_candidates', [])[:24]:
        sticker_lines.append(
            f"- md5={item['md5']} count={item['count']} local_file={item['local_file'] or '[缺失]'}"
        )

    system_prompt = '\n\n'.join([
        profile['system_prompt'],
        '以下是本地聊天应用的额外规则：',
        '1. 你是在一个真实聊天界面里回复，不是写分析报告。',
        '2. 如果适合发文字，就正常回复；emoji_text 只有在非常自然时才填，绝大多数回复应留空。',
        '3. 如果适合发表情包，只能从候选 md5 中选择，不要虚构文件名。',
        '4. 长文本一般不配表情包；语音和表情包通常二选一。',
        '5. 即使历史里她表情包很多，你也不能机械地每句都发。',
        STICKER_MODE_PROMPTS.get(sticker_mode, STICKER_MODE_PROMPTS['light']),
        OUTPUT_SCHEMA_DESCRIPTION,
        '可用表情包候选：',
        '\n'.join(sticker_lines) if sticker_lines else '- 当前没有可用本地表情包候选',
    ])

    messages = [{'role': 'system', 'content': system_prompt}]
    for item in history[-12:]:
        role = 'assistant' if item.get('role') == 'assistant' else 'user'
        messages.append({'role': role, 'content': _history_item_to_prompt_text(item)})

    current_parts = []
    if user_message.strip():
        current_parts.append(user_message.strip())
    if manual_sticker_md5:
        current_parts.append(f'[用户刚刚主动发送了一个本地表情包，md5={manual_sticker_md5}]')
    messages.append({'role': 'user', 'content': '\n'.join(current_parts) if current_parts else '[用户发送了一条空消息]'})
    return messages


def chat_with_model(
    *,
    base_url: str,
    api_key: str,
    model: str,
    timeout: int,
    temperature: float,
    profile: Dict,
    user_message: str,
    history: List[Dict],
    sticker_mode: str,
    manual_sticker_md5: str = '',
) -> Dict:
    """调用 OpenAI 兼容聊天接口。"""
    if not api_key:
        raise RuntimeError('缺少 MODEL_API_KEY，无法调用聊天模型')

    payload = {
        'model': model,
        'temperature': temperature,
        'messages': _build_messages(profile, user_message, history, sticker_mode, manual_sticker_md5),
        'response_format': {'type': 'json_object'},
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    url = base_url.rstrip('/') + '/chat/completions'
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data['choices'][0]['message']['content']
    parsed = json.loads(_extract_json_text(content))
    parsed.setdefault('reply_text', '')
    parsed.setdefault('emotion', '')
    parsed.setdefault('emoji_text', '')
    parsed.setdefault('use_sticker', False)
    parsed.setdefault('sticker_md5', '')
    parsed.setdefault('sticker_reason', '')
    parsed.setdefault('send_voice', False)
    parsed.setdefault('voice_text', '')
    return _apply_local_media_policy(profile, history, parsed, sticker_mode)
