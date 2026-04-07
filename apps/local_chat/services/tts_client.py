"""语音合成服务。"""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx


def _save_audio(runtime_dir: Path, slug: str, audio_bytes: bytes, suffix: str = '.mp3') -> str:
    """把音频保存到运行目录并返回相对 URL。"""
    audio_dir = runtime_dir / 'audio' / slug
    audio_dir.mkdir(parents=True, exist_ok=True)
    filename = datetime.now().strftime('%Y%m%d_%H%M%S_%f') + suffix
    target = audio_dir / filename
    target.write_bytes(audio_bytes)
    return f'/runtime-audio/{slug}/{filename}'


def synthesize_voice(
    *,
    provider: str,
    runtime_dir: Path,
    slug: str,
    text: str,
    api_base_url: str,
    api_key: str,
    model: str,
    voice: str,
    timeout: int,
    custom_endpoint: str,
    voice_reference_dir: str,
    voice_override: str = '',
) -> Optional[str]:
    """合成语音，返回可访问 URL。"""
    if not text.strip() or provider == 'none':
        return None

    selected_voice = voice_override or voice

    if provider in {'openai_compatible', 'siliconflow_clone'}:
        if not api_key:
            return None
        url = api_base_url.rstrip('/') + '/audio/speech'
        payload = {
            'model': model,
            'voice': selected_voice,
            'input': text,
            'format': 'mp3',
        }
        headers = {'Authorization': f'Bearer {api_key}'}
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        return _save_audio(runtime_dir, slug, response.content, '.mp3')

    if provider == 'custom_http' and custom_endpoint:
        payload = {
            'text': text,
            'slug': slug,
            'voice_reference_dir': voice_reference_dir,
        }
        with httpx.Client(timeout=timeout) as client:
            response = client.post(custom_endpoint, json=payload)
            response.raise_for_status()

        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            data = response.json()
            if data.get('audio_base64'):
                audio_bytes = base64.b64decode(data['audio_base64'])
                suffix = data.get('suffix', '.wav')
                return _save_audio(runtime_dir, slug, audio_bytes, suffix)
            return data.get('audio_url')

        suffix = '.wav' if 'wav' in content_type else '.mp3'
        return _save_audio(runtime_dir, slug, response.content, suffix)

    return None
