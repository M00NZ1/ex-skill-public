"""语音样本选择与自定义声线上传。"""

from __future__ import annotations

import json
import re
import wave
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx


TIME_PATTERN = re.compile(r'_(\d{10})_(\d+)$')


def _safe_duration_seconds(path: Path) -> float:
    """读取 wav 时长。"""
    try:
        with wave.open(str(path), 'rb') as wf:
            return wf.getnframes() / float(wf.getframerate())
    except Exception:  # noqa: BLE001
        return 0.0


def _load_target_transcripts(skill_dir: Path) -> List[Dict]:
    """读取资料包中的 ta 语音转写。"""
    path = skill_dir / 'memories' / 'media' / 'voice_target_transcripts.json'
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return []
    return [item for item in data if isinstance(item, dict)]


def _build_voice_file_index(voice_dir: Path) -> Dict[int, List[Path]]:
    """按 create_time 建立语音文件索引。"""
    index: Dict[int, List[Path]] = {}
    for wav in voice_dir.glob('*.wav'):
        match = TIME_PATTERN.search(wav.stem)
        if not match:
            continue
        create_time = int(match.group(1))
        index.setdefault(create_time, []).append(wav)
    return index


def pick_reference_voice_sample(repo_root: Path, slug: str) -> Optional[Dict]:
    """从本地语音中挑选最适合作为声线参考的一条。"""
    skill_dir = repo_root / 'exes' / slug
    voice_dir = repo_root / 'data' / 'Voices'
    if not skill_dir.exists() or not voice_dir.exists():
        return None

    target_transcripts = _load_target_transcripts(skill_dir)
    voice_index = _build_voice_file_index(voice_dir)

    candidates = []
    for item in target_transcripts:
        create_time = item.get('create_time')
        transcript = str(item.get('text', '') or '').strip()
        if not create_time or not transcript:
            continue
        for wav in voice_index.get(int(create_time), []):
            duration = _safe_duration_seconds(wav)
            if duration <= 0:
                continue
            score = (
                abs(duration - 9.5),
                0 if 8 <= duration <= 12 else 1,
                0 if 20 <= len(transcript) <= 120 else 1,
                -len(transcript),
            )
            candidates.append({
                'score': score,
                'duration': round(duration, 2),
                'path': wav,
                'transcript': transcript,
                'timestamp': item.get('timestamp', ''),
                'create_time': create_time,
            })

    if not candidates:
        return None

    candidates.sort(key=lambda item: item['score'])
    best = candidates[0].copy()
    best.pop('score', None)
    best['path'] = str(best['path'])
    return best


def _voice_cache_path(runtime_dir: Path, slug: str) -> Path:
    return runtime_dir / 'voice_profiles' / f'{slug}.json'


def load_cached_voice_profile(runtime_dir: Path, slug: str) -> Dict:
    """读取缓存的声线配置。"""
    path = _voice_cache_path(runtime_dir, slug)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}


def save_cached_voice_profile(runtime_dir: Path, slug: str, payload: Dict):
    """保存声线缓存。"""
    path = _voice_cache_path(runtime_dir, slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def upload_reference_voice_to_siliconflow(
    *,
    runtime_dir: Path,
    repo_root: Path,
    slug: str,
    api_base_url: str,
    api_key: str,
    model: str,
) -> Dict:
    """上传本地语音样本到 SiliconFlow，得到可复用 voice uri。"""
    if not api_key:
        raise RuntimeError('缺少 SiliconFlow API Key，无法上传声线样本')

    cached = load_cached_voice_profile(runtime_dir, slug)
    if cached.get('voice_uri') and Path(str(cached.get('sample_path', ''))).exists():
        return cached

    sample = pick_reference_voice_sample(repo_root, slug)
    if not sample:
        raise RuntimeError('没有找到可用的本地语音样本，无法构建自定义声线')

    sample_path = Path(sample['path'])
    upload_url = api_base_url.rstrip('/') + '/uploads/audio/voice'
    custom_name = f'{slug}-auto-{datetime.now().strftime("%Y%m%d%H%M%S")}'

    with open(sample_path, 'rb') as handle:
        files = {'file': (sample_path.name, handle, 'audio/wav')}
        data = {
            'model': model,
            'customName': custom_name,
            'text': sample['transcript'],
        }
        response = httpx.post(
            upload_url,
            headers={'Authorization': f'Bearer {api_key}'},
            files=files,
            data=data,
            timeout=180,
        )
        response.raise_for_status()
        body = response.json()

    payload = {
        'provider': 'SiliconFlow',
        'model': model,
        'voice_uri': body.get('uri', ''),
        'sample_path': str(sample_path),
        'sample_duration': sample['duration'],
        'sample_transcript': sample['transcript'],
        'sample_timestamp': sample['timestamp'],
        'uploaded_at': datetime.now().isoformat(timespec='seconds'),
    }
    save_cached_voice_profile(runtime_dir, slug, payload)
    return payload
