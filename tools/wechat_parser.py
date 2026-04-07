#!/usr/bin/env python3
"""微信聊天记录解析器
支持的输入格式：
- txt / csv（带时间戳的聊天记录文本）
- html / htm（带样式的聊天记录页面）
- json（结构化聊天数据）
- sqlite / db（数据库文件）
- 纯文本（手动复制粘贴）
- 微信官方迁移/备份目录（仅识别并给出提示，不能直接解析）

Usage:
    python3 wechat_parser.py --file <path> --target <name> --output <output_path> [--format auto]
"""

import argparse
import json
import re
import os
import sys
from pathlib import Path
from datetime import datetime


RMFH_MAGIC = b'RMFH'


def is_wechat_official_backup_dir(file_path: str) -> bool:
    """识别微信官方聊天记录迁移/备份目录。

    常见特征：
    - 顶层存在 .wechat-deviceId
    - 或目录内存在 backup.attr + files/ 组合
    """
    path = Path(file_path)
    if not path.is_dir():
        return False

    if (path / '.wechat-deviceId').exists():
        return True

    if (path / 'backup.attr').exists() and (path / 'files').is_dir():
        return True

    for child in path.iterdir():
        if child.is_dir() and (child / 'backup.attr').exists() and (child / 'files').is_dir():
            return True

    return False


def has_rmfh_header(file_path: str) -> bool:
    """识别微信官方备份分片文件头。"""
    try:
        with open(file_path, 'rb') as f:
            return f.read(4) == RMFH_MAGIC
    except OSError:
        return False


def detect_format(file_path: str) -> str:
    """自动检测文件格式"""
    if os.path.isdir(file_path):
        if is_wechat_official_backup_dir(file_path):
            return 'wechat_official_backup'
        return 'directory'

    ext = Path(file_path).suffix.lower()
    
    if ext == '.json':
        return 'liuhen'  # 留痕导出
    elif ext == '.csv':
        return 'wechatmsg_csv'
    elif ext == '.html' or ext == '.htm':
        return 'wechatmsg_html'
    elif ext == '.db' or ext == '.sqlite':
        return 'pywxdump'
    elif ext in {'.enc', '.dat', '.attr'} and has_rmfh_header(file_path):
        return 'wechat_official_backup_blob'
    elif ext == '.txt':
        # 尝试区分 WeChatMsg txt 和纯文本
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_lines = f.read(2000)
        # WeChatMsg 格式通常有时间戳模式
        if re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', first_lines):
            return 'wechatmsg_txt'
        return 'plaintext'
    else:
        return 'plaintext'


def explain_official_backup(file_path: str, target_name: str) -> dict:
    """解释为何微信官方备份目录/分片无法直接使用。"""
    return {
        'target_name': target_name,
        'format': 'wechat_official_backup',
        'direct_usable': False,
        'analysis': {
            'note': (
                '检测到微信官方迁移/备份目录（ChatBackup / RMFH 分片）。'
                '这类数据是官方备份容器，不是 ex-skill 当前可直接解析的可读聊天文本。'
            ),
            'suggestions': [
                '先使用能导出可读文本的工具转换为 txt / json，再导入本项目',
                '或者先把关键聊天在电脑微信中复制为 txt',
                '不要把 .enc / .dat / backup.attr 直接喂给解析器'
            ]
        }
    }


def parse_wechatmsg_txt(file_path: str, target_name: str) -> dict:
    """解析 WeChatMsg 导出的 txt 格式
    
    典型格式：
    2024-01-15 20:30:45 张三
    今天好累啊
    
    2024-01-15 20:31:02 我
    怎么了？
    """
    messages = []
    current_msg = None
    
    # WeChatMsg 时间戳 + 发送者模式
    msg_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.+)$')
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.rstrip('\n')
            match = msg_pattern.match(line)
            if match:
                if current_msg:
                    messages.append(current_msg)
                timestamp, sender = match.groups()
                current_msg = {
                    'timestamp': timestamp,
                    'sender': sender.strip(),
                    'content': ''
                }
            elif current_msg and line.strip():
                if current_msg['content']:
                    current_msg['content'] += '\n'
                current_msg['content'] += line
    
    if current_msg:
        messages.append(current_msg)
    
    return analyze_messages(messages, target_name)


def parse_liuhen_json(file_path: str, target_name: str) -> dict:
    """解析留痕 / WeFlow 导出的 JSON 格式"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    messages = []
    session_info = data.get('session', {}) if isinstance(data, dict) else {}

    # 留痕 / WeFlow 格式可能有多种结构，尝试常见的字段
    msg_list = data if isinstance(data, list) else data.get('messages', data.get('data', []))

    for msg in msg_list:
        timestamp = (
            msg.get('formattedTime')
            or msg.get('time')
            or msg.get('timestamp')
            or ''
        )

        if not timestamp and msg.get('createTime'):
            try:
                timestamp = datetime.fromtimestamp(int(msg['createTime'])).strftime('%Y-%m-%d %H:%M:%S')
            except (TypeError, ValueError, OSError):
                timestamp = ''

        sender = (
            msg.get('senderDisplayName')
            or msg.get('sender')
            or msg.get('nickname')
            or msg.get('from')
            or ''
        )

        # WeFlow 常见字段：发送给自己时 senderDisplayName 可能缺失，用 isSend 兜底。
        if not sender and 'isSend' in msg:
            if int(msg.get('isSend') or 0) == 1:
                sender = '我'
            else:
                sender = (
                    session_info.get('remark')
                    or session_info.get('displayName')
                    or session_info.get('nickname')
                    or target_name
                )

        content = (
            msg.get('content')
            or msg.get('message')
            or msg.get('text')
            or ''
        )

        if not content:
            msg_type = msg.get('type')
            if msg_type:
                content = f'[{msg_type}]'

        messages.append({
            'timestamp': timestamp,
            'sender': sender,
            'content': content,
            'message_type': msg.get('type', ''),
        })

    return analyze_messages(messages, target_name)


def parse_plaintext(file_path: str, target_name: str) -> dict:
    """解析纯文本粘贴的聊天记录"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    return {
        'raw_text': content,
        'target_name': target_name,
        'format': 'plaintext',
        'direct_usable': True,
        'message_count': 0,
        'analysis': {
            'note': '纯文本格式，需要人工辅助分析'
        }
    }


def analyze_messages(messages: list, target_name: str) -> dict:
    """分析消息列表，提取关键特征"""
    target_msgs = [m for m in messages if target_name in m.get('sender', '')]
    user_msgs = [m for m in messages if target_name not in m.get('sender', '')]
    
    # 提取口头禅（高频词分析）
    all_target_text = ' '.join([m['content'] for m in target_msgs if m.get('content')])
    
    # 提取语气词
    particles = re.findall(r'[哈嗯哦噢嘿唉呜啊呀吧嘛呢吗么]+', all_target_text)
    particle_freq = {}
    for p in particles:
        particle_freq[p] = particle_freq.get(p, 0) + 1
    top_particles = sorted(particle_freq.items(), key=lambda x: -x[1])[:10]
    
    # 提取 emoji
    emoji_pattern = re.compile(
        r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF'
        r'\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF'
        r'\U00002702-\U000027B0\U0000FE00-\U0000FE0F'
        r'\U0001F900-\U0001F9FF]+', re.UNICODE
    )
    emojis = emoji_pattern.findall(all_target_text)
    emoji_freq = {}
    for e in emojis:
        emoji_freq[e] = emoji_freq.get(e, 0) + 1
    top_emojis = sorted(emoji_freq.items(), key=lambda x: -x[1])[:10]
    
    # 消息长度统计
    msg_lengths = [len(m['content']) for m in target_msgs if m.get('content')]
    avg_length = sum(msg_lengths) / len(msg_lengths) if msg_lengths else 0
    
    # 标点习惯
    punctuation_counts = {
        '句号': all_target_text.count('。'),
        '感叹号': all_target_text.count('！') + all_target_text.count('!'),
        '问号': all_target_text.count('？') + all_target_text.count('?'),
        '省略号': all_target_text.count('...') + all_target_text.count('…'),
        '波浪号': all_target_text.count('～') + all_target_text.count('~'),
    }
    
    return {
        'target_name': target_name,
        'total_messages': len(messages),
        'target_messages': len(target_msgs),
        'user_messages': len(user_msgs),
        'direct_usable': True,
        'analysis': {
            'top_particles': top_particles,
            'top_emojis': top_emojis,
            'avg_message_length': round(avg_length, 1),
            'punctuation_habits': punctuation_counts,
            'message_style': 'short_burst' if avg_length < 20 else 'long_form',
        },
        'sample_messages': [m['content'] for m in target_msgs[:50] if m.get('content')],
    }


def main():
    parser = argparse.ArgumentParser(description='微信聊天记录解析器')
    parser.add_argument('--file', required=True, help='输入文件或目录路径')
    parser.add_argument('--target', required=True, help='前任的名字/昵称')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument(
        '--format',
        default='auto',
        help='文件格式 (auto/wechatmsg_txt/liuhen/pywxdump/plaintext/wechat_official_backup)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"错误：文件不存在 {args.file}", file=sys.stderr)
        sys.exit(1)
    
    fmt = args.format
    if fmt == 'auto':
        fmt = detect_format(args.file)
        print(f"自动检测格式：{fmt}")
    
    parsers = {
        'wechatmsg_txt': parse_wechatmsg_txt,
        'liuhen': parse_liuhen_json,
        'plaintext': parse_plaintext,
        'wechat_official_backup': explain_official_backup,
        'wechat_official_backup_blob': explain_official_backup,
        'directory': explain_official_backup,
    }
    
    parse_func = parsers.get(fmt, parse_plaintext)
    result = parse_func(args.file, args.target)
    
    # 输出分析结果
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(f"# 微信聊天记录分析 — {args.target}\n\n")
        f.write(f"来源文件：{args.file}\n")
        f.write(f"检测格式：{fmt}\n")
        f.write(f"可直接导入：{'是' if result.get('direct_usable') else '否'}\n")
        f.write(f"总消息数：{result.get('total_messages', 'N/A')}\n")
        f.write(f"ta的消息数：{result.get('target_messages', 'N/A')}\n\n")
        
        analysis = result.get('analysis', {})

        if analysis.get('note'):
            f.write("## 说明\n")
            f.write(f"- {analysis['note']}\n\n")

        if analysis.get('suggestions'):
            f.write("## 建议处理方式\n")
            for item in analysis['suggestions']:
                f.write(f"- {item}\n")
            f.write("\n")
        
        if analysis.get('top_particles'):
            f.write("## 高频语气词\n")
            for word, count in analysis['top_particles']:
                f.write(f"- {word}: {count}次\n")
            f.write("\n")
        
        if analysis.get('top_emojis'):
            f.write("## 高频 Emoji\n")
            for emoji, count in analysis['top_emojis']:
                f.write(f"- {emoji}: {count}次\n")
            f.write("\n")
        
        if analysis.get('punctuation_habits'):
            f.write("## 标点习惯\n")
            for punct, count in analysis['punctuation_habits'].items():
                f.write(f"- {punct}: {count}次\n")
            f.write("\n")
        
        style = analysis.get('message_style')
        if style == 'short_burst':
            style_text = '短句连发型'
        elif style == 'long_form':
            style_text = '长段落型'
        else:
            style_text = '未知 / 待人工判断'

        f.write(f"## 消息风格\n")
        f.write(f"- 平均消息长度：{analysis.get('avg_message_length', 'N/A')} 字\n")
        f.write(f"- 风格：{style_text}\n\n")
        
        if result.get('sample_messages'):
            f.write("## 消息样本（前50条）\n")
            for i, msg in enumerate(result['sample_messages'], 1):
                f.write(f"{i}. {msg}\n")
    
    print(f"分析完成，结果已写入 {args.output}")


if __name__ == '__main__':
    main()
