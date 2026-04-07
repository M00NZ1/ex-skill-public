#!/usr/bin/env python3
"""基于现有证据自动补全资料包。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from apps.local_chat.config import settings
from tools.skill_writer import combine_skill


def read_text(path: Path) -> str:
    """读取文本。"""
    if not path.exists():
        return ''
    return path.read_text(encoding='utf-8')


def backup_file(path: Path):
    """备份文件。"""
    if not path.exists():
        return
    backup_dir = path.parent / 'versions'
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f'{timestamp}_{path.name}'
    backup_path.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')


def build_prompt(slug_dir: Path) -> list[dict]:
    """构建补全提示。"""
    memory = read_text(slug_dir / 'memory.md')
    persona = read_text(slug_dir / 'persona.md')
    meta = read_text(slug_dir / 'meta.json')
    chat_reports = []
    chats_dir = slug_dir / 'memories' / 'chats'
    if chats_dir.exists():
        for item in sorted(chats_dir.glob('*.md')):
            chat_reports.append(f'## {item.name}\n{read_text(item)}')

    media_reports = []
    media_dir = slug_dir / 'memories' / 'media'
    if media_dir.exists():
        for item in sorted(media_dir.glob('*.md')):
            media_reports.append(f'## {item.name}\n{read_text(item)}')

    evidence = '\n\n'.join([
        '### meta.json',
        meta,
        '### 当前 memory.md',
        memory,
        '### 当前 persona.md',
        persona,
        '### 聊天分析报告',
        '\n\n'.join(chat_reports) or '[无]',
        '### 媒体分析报告',
        '\n\n'.join(media_reports) or '[无]',
    ])

    system_prompt = """你是“前任资料包补全器”。

你的目标：
1. 只根据输入证据，重写 memory.md 与 persona.md。
2. 允许做“证据支撑下的归纳”，但禁止编造具体事实。
3. 没证据的地方必须保留 `[待补充]`。
4. 优先补这些常见空缺：
   - 认识时间 / 第一条聊天时间
   - 联系活跃时间段
   - 回复节奏、语音使用、表情包使用、图片分享强度
   - 说话风格、常用语气、消息长度、互动模式
   - 可从证据中看出的关系行为
5. 保持 Markdown 可直接落盘，不要输出解释性废话。

输出要求：
- 只返回 JSON 对象
- 字段：
  - memory_md
  - persona_md
  - summary
"""

    user_prompt = f"""请基于下面证据重写资料包。

证据开始：
{evidence}
证据结束。

请返回 JSON。
"""

    return [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt},
    ]


def run_autofill(slug: str, base_dir: str):
    """执行自动补全。"""
    slug_dir = Path(base_dir) / slug
    if not slug_dir.exists():
        raise FileNotFoundError(f'资料包不存在：{slug_dir}')

    if not settings.enrich_api_key:
        raise RuntimeError('缺少补全模型 API Key，无法执行自动补全')

    payload = {
        'model': settings.enrich_model_name,
        'temperature': settings.enrich_temperature,
        'messages': build_prompt(slug_dir),
        'response_format': {'type': 'json_object'},
    }
    headers = {
        'Authorization': f'Bearer {settings.enrich_api_key}',
        'Content-Type': 'application/json',
    }
    url = settings.enrich_api_base_url.rstrip('/') + '/chat/completions'

    with httpx.Client(timeout=settings.enrich_timeout) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data['choices'][0]['message']['content']
    parsed = json.loads(content)
    memory_md = str(parsed.get('memory_md', '') or '').strip()
    persona_md = str(parsed.get('persona_md', '') or '').strip()
    summary = str(parsed.get('summary', '') or '').strip()

    if not memory_md or not persona_md:
        raise RuntimeError('补全模型未返回有效的 memory_md / persona_md')

    memory_path = slug_dir / 'memory.md'
    persona_path = slug_dir / 'persona.md'
    backup_file(memory_path)
    backup_file(persona_path)
    memory_path.write_text(memory_md + '\n', encoding='utf-8')
    persona_path.write_text(persona_md + '\n', encoding='utf-8')
    combine_skill(os.path.abspath(base_dir), slug)
    return summary


def main():
    parser = argparse.ArgumentParser(description='资料包自动补全器')
    parser.add_argument('--slug', required=True, help='资料包 slug')
    parser.add_argument('--base-dir', default='./exes', help='资料包根目录')
    args = parser.parse_args()

    summary = run_autofill(args.slug, args.base_dir)
    print('自动补全完成。')
    if summary:
        print(summary)


if __name__ == '__main__':
    main()
