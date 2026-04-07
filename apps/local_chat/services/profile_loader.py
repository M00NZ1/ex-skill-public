"""读取资料包与媒体候选。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List


def _read_text(path: Path) -> str:
    if not path.exists():
        return ''
    return path.read_text(encoding='utf-8')


def _read_json(path: Path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def _extract_reply_profile(memory: str, persona: str) -> Dict:
    """从资料文本中提取回复节奏统计。"""
    combined = '\n'.join([memory, persona])
    median_match = re.search(r'中位(?:回复)?间隔约\s*(\d+)\s*秒', combined)
    p75_match = re.search(r'75\s*分位约\s*(\d+)\s*秒', combined)

    median = int(median_match.group(1)) if median_match else 18
    p75 = int(p75_match.group(1)) if p75_match else max(60, median * 3)
    source = 'memory' if (median_match or p75_match) else 'default'
    return {
        'median_reply_seconds': median,
        'p75_reply_seconds': p75,
        'source': source,
    }


def load_profile(repo_root: Path, exes_dir: Path, slug: str) -> Dict:
    """加载一个资料包。"""
    skill_dir = exes_dir / slug
    if not skill_dir.exists():
        raise FileNotFoundError(f'资料包不存在：{skill_dir}')

    meta = _read_json(skill_dir / 'meta.json')
    system_prompt = _read_text(skill_dir / 'SYSTEM_PROMPT.md')
    memory = _read_text(skill_dir / 'memory.md')
    persona = _read_text(skill_dir / 'persona.md')
    media_manifest = _read_json(skill_dir / 'memories' / 'media' / 'media_manifest.json')
    emoji_top = _read_json(skill_dir / 'memories' / 'media' / 'emoji_usage_top50.json')

    sticker_candidates: List[Dict] = []
    emojis_root = repo_root / 'data' / 'emojis'
    emoji_count_map: Dict[str, int] = {}
    if isinstance(emoji_top, list):
        for item in emoji_top:
            md5 = str(item.get('md5', '') or '').strip()
            if not md5:
                continue
            emoji_count_map[md5] = int(item.get('count', 0) or 0)

    if emojis_root.exists():
        for emoji_path in sorted(
            (item for item in emojis_root.rglob('*') if item.is_file()),
            key=lambda item: (
                -emoji_count_map.get(item.stem, 0),
                item.suffix.lower(),
                item.name.lower(),
            ),
        ):
            local_file = str(emoji_path.relative_to(emojis_root)).replace('\\', '/')
            sticker_candidates.append({
                'md5': emoji_path.stem,
                'count': emoji_count_map.get(emoji_path.stem, 0),
                'local_file': local_file,
                'url': f'/emoji-assets/{local_file}',
            })

    summary = '\n'.join([
        f"名字：{meta.get('name', slug)}",
        f"印象：{meta.get('impression', '') or '[未填写]'}",
        f"关系摘要：在一起 {meta.get('profile', {}).get('together_duration', '') or '[未填写]'}，分开 {meta.get('profile', {}).get('apart_since', '') or '[未填写]'}",
        f"媒体摘要：{json.dumps(meta.get('media_summary', {}), ensure_ascii=False)}",
    ])

    return {
        'slug': slug,
        'name': meta.get('name', slug),
        'meta': meta,
        'system_prompt': system_prompt,
        'memory': memory,
        'persona': persona,
        'media_manifest': media_manifest,
        'sticker_candidates': sticker_candidates,
        'auto_sticker_candidates': [item for item in sticker_candidates if item.get('count', 0) > 0][:24] or sticker_candidates[:24],
        'reply_profile': _extract_reply_profile(memory, persona),
        'summary': summary,
    }
