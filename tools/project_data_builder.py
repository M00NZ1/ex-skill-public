#!/usr/bin/env python3
"""项目内聊天资料工作区构建器。

目标：
- 在项目内统一存放聊天记录、媒体、补充说明
- 用一个固定命令完成资料包构建

典型用法：
    python tools/project_data_builder.py --init --slug xiaoxia
    python tools/project_data_builder.py --slug xiaoxia --name 小夏 --target 小夏
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from skill_writer import combine_skill, init_skill
from universal_builder import (
    aggregate_results,
    build_agent_prompt,
    build_manual_notes,
    build_memory_md,
    build_media_summary,
    build_persona_md,
    parse_wechat_source,
    slugify,
    write_media_reports,
    write_source_reports,
)


WORKSPACE_ROOT = Path('./data/chat_records')
SUPPORTED_CHAT_SUFFIXES = {'.txt', '.json', '.html', '.htm', '.csv', '.db', '.sqlite'}
SUPPORTED_NOTE_SUFFIXES = {'.txt', '.md'}


def init_workspace(slug: str) -> Path:
    """初始化项目内聊天资料目录。"""
    base_dir = WORKSPACE_ROOT / slug
    dirs = [
        base_dir / 'raw',
        base_dir / 'media' / 'images',
        base_dir / 'media' / 'emojis',
        base_dir / 'media' / 'voice',
        base_dir / 'media' / 'video',
        base_dir / 'notes',
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)

    readme_path = base_dir / 'README.md'
    if not readme_path.exists():
        readme_path.write_text(
            f"""# {slug} 聊天资料目录

## 放置规则
- `raw/`：放可读聊天导出，例如 `txt / json / html`
- `media/images/`：放聊天相关图片
- `media/emojis/`：放导出的表情包文件
- `media/voice/`：放语音文件或语音转写
- `media/video/`：放视频说明或导出视频
- `notes/`：放你的补充说明，支持 `txt / md`

## 构建命令
```bash
python tools/project_data_builder.py --slug {slug} --name "代号" --target "聊天昵称"
```

## 重要提醒
- 微信官方 `ChatBackup` 目录不能直接解析为聊天文本
- 原始备份建议保留在外部归档目录，不要只留项目内这一份
""",
            encoding='utf-8',
        )

    return base_dir


def discover_chat_sources(raw_dir: Path) -> List[str]:
    """发现 raw 目录下可用的聊天来源。"""
    sources: List[str] = []

    if not raw_dir.exists():
        return sources

    for child in sorted(raw_dir.iterdir()):
        if child.is_file() and child.suffix.lower() in SUPPORTED_CHAT_SUFFIXES:
            sources.append(str(child.resolve()))
        elif child.is_dir():
            sources.append(str(child.resolve()))

    return sources


def discover_note_files(notes_dir: Path) -> List[str]:
    """发现 notes 目录下的说明文件。"""
    if not notes_dir.exists():
        return []
    return [
        str(path.resolve())
        for path in sorted(notes_dir.iterdir())
        if path.is_file() and path.suffix.lower() in SUPPORTED_NOTE_SUFFIXES
    ]


def discover_media_inputs(workspace_dir: Path) -> Dict[str, str]:
    """发现项目内工作区中的媒体输入。"""
    media_dir = workspace_dir / 'media'
    voice_dir = media_dir / 'voice'

    voice_transcripts = ''
    if voice_dir.exists():
        preferred = voice_dir / 'transcripts.json'
        if preferred.exists():
            voice_transcripts = str(preferred.resolve())
        else:
            json_files = sorted([path for path in voice_dir.iterdir() if path.is_file() and path.suffix.lower() == '.json'])
            if json_files:
                voice_transcripts = str(json_files[0].resolve())

    return {
        'voice_transcripts': voice_transcripts,
        'images_dir': str((media_dir / 'images').resolve()) if (media_dir / 'images').exists() else '',
        'emojis_dir': str((media_dir / 'emojis').resolve()) if (media_dir / 'emojis').exists() else '',
        'videos_dir': str((media_dir / 'video').resolve()) if (media_dir / 'video').exists() else '',
    }


def build_from_workspace(
    slug: str,
    name: str,
    target: str,
    together_duration: str,
    apart_since: str,
    occupation: str,
    city: str,
    mbti: str,
    zodiac: str,
    impression: str,
):
    """从项目内工作区构建最终资料包。"""
    workspace_dir = init_workspace(slug)
    raw_dir = workspace_dir / 'raw'
    notes_dir = workspace_dir / 'notes'

    chat_sources = discover_chat_sources(raw_dir)
    note_files = discover_note_files(notes_dir)
    media_inputs = discover_media_inputs(workspace_dir)

    results = [parse_wechat_source(path, target) for path in chat_sources]
    aggregated = aggregate_results(results)
    manual_notes = build_manual_notes(note_files, [])
    media_summary = build_media_summary(
        chat_sources,
        target,
        voice_transcripts_path=media_inputs['voice_transcripts'],
        images_dir=media_inputs['images_dir'],
        emojis_dir=media_inputs['emojis_dir'],
        videos_dir=media_inputs['videos_dir'],
    )

    base_dir = os.path.abspath('./exes')
    skill_dir = os.path.join(base_dir, slug)
    init_skill(base_dir, slug)

    meta = {
        'name': name,
        'slug': slug,
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'updated_at': datetime.now().isoformat(timespec='seconds'),
        'version': 'v1',
        'profile': {
            'together_duration': together_duration,
            'apart_since': apart_since,
            'occupation': occupation,
            'city': city,
            'mbti': mbti,
            'zodiac': zodiac,
        },
        'impression': impression,
        'memory_sources': chat_sources,
        'media_sources': media_inputs,
        'corrections_count': 0,
        'build_mode': 'project_workspace',
        'workspace_dir': str(workspace_dir.resolve()),
    }

    meta_path = Path(skill_dir) / 'meta.json'
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')

    memory_path = Path(skill_dir) / 'memory.md'
    memory_path.write_text(build_memory_md(meta, aggregated, results, manual_notes, media_summary), encoding='utf-8')

    persona_path = Path(skill_dir) / 'persona.md'
    persona_path.write_text(build_persona_md(meta, aggregated, media_summary), encoding='utf-8')

    agent_prompt_path = Path(skill_dir) / 'AGENT_PROMPT.md'
    agent_prompt_path.write_text(build_agent_prompt(meta), encoding='utf-8')

    write_source_reports(skill_dir, results)
    write_media_reports(skill_dir, media_summary)
    combine_skill(base_dir, slug)

    print(f'聊天资料目录：{workspace_dir.resolve()}')
    print(f'最终资料包：{skill_dir}')
    print('如果 raw 目录里放的是可读聊天导出，现在已经可以直接给 Cursor / Codex / Gemini / Claude 使用。')


def main():
    parser = argparse.ArgumentParser(description='项目内聊天资料工作区构建器')
    parser.add_argument('--init', action='store_true', help='仅初始化项目内聊天资料目录')
    parser.add_argument('--slug', required=True, help='代号目录名')
    parser.add_argument('--name', help='前任代号/名字，构建时必填')
    parser.add_argument('--target', help='聊天中用于识别 ta 的昵称/备注，构建时必填')
    parser.add_argument('--together-duration', default='', help='在一起时长')
    parser.add_argument('--apart-since', default='', help='分开时长')
    parser.add_argument('--occupation', default='', help='职业')
    parser.add_argument('--city', default='', help='城市')
    parser.add_argument('--mbti', default='', help='MBTI')
    parser.add_argument('--zodiac', default='', help='星座')
    parser.add_argument('--impression', default='', help='一句话印象')

    args = parser.parse_args()

    slug = slugify(args.slug)

    if args.init:
        workspace_dir = init_workspace(slug)
        print(f'已初始化聊天资料目录：{workspace_dir.resolve()}')
        return

    if not args.name or not args.target:
        parser.error('非 --init 模式下必须提供 --name 和 --target')

    build_from_workspace(
        slug=slug,
        name=args.name,
        target=args.target,
        together_duration=args.together_duration,
        apart_since=args.apart_since,
        occupation=args.occupation,
        city=args.city,
        mbti=args.mbti,
        zodiac=args.zodiac,
        impression=args.impression,
    )


if __name__ == '__main__':
    main()
