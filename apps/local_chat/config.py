"""本地聊天应用配置。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXTERNAL_CONFIG_CANDIDATES = [
    REPO_ROOT / 'config' / 'providers.local.json',
]

EXTERNAL_PROVIDER_MAP = {
    'DeepSeek Official': {
        'api_key': 'api_key_deepseek',
        'base_url': 'base_url_deepseek',
        'model': 'model_deepseek',
    },
    'SiliconFlow (硅基流动)': {
        'api_key': 'api_key_siliconflow',
        'base_url': 'base_url_siliconflow',
        'model': 'model_siliconflow',
    },
    'Volcengine (火山引擎/豆包)': {
        'api_key': 'api_key_volcengine',
        'base_url': 'base_url_volcengine',
        'model': 'model_volcengine',
    },
}


def discover_external_config_path() -> Path:
    """发现外部配置文件。"""
    override = os.getenv('EXTERNAL_PROVIDER_CONFIG', '').strip()
    if override:
        return Path(override)

    for candidate in DEFAULT_EXTERNAL_CONFIG_CANDIDATES:
        if candidate.exists():
            return candidate

    return Path('')


def load_external_provider_configs() -> Dict[str, Dict[str, str]]:
    """加载本地多提供商配置。"""
    config_path = discover_external_config_path()
    if not config_path or not config_path.exists():
        return {}

    try:
        data = json.loads(config_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}

    providers: Dict[str, Dict[str, str]] = {}
    for provider_name, key_map in EXTERNAL_PROVIDER_MAP.items():
        providers[provider_name] = {
            'api_key': str(data.get(key_map['api_key'], '') or '').strip(),
            'base_url': str(data.get(key_map['base_url'], '') or '').strip(),
            'model': str(data.get(key_map['model'], '') or '').strip(),
        }

    active_provider = str(data.get('provider', '') or '').strip()
    if active_provider:
        providers['_meta'] = {'active_provider': active_provider, 'config_path': str(config_path)}
    else:
        providers['_meta'] = {'active_provider': '', 'config_path': str(config_path)}
    return providers


def pick_provider_config(
    provider_configs: Dict[str, Dict[str, str]],
    preferred_provider: str,
    fallback_order: list[str],
) -> Dict[str, str]:
    """按优先级挑选一组可用配置。"""
    names = [preferred_provider] + [item for item in fallback_order if item != preferred_provider]
    for name in names:
        cfg = provider_configs.get(name, {})
        if cfg.get('api_key') and cfg.get('base_url'):
            result = cfg.copy()
            result['provider_name'] = name
            return result

    return {'provider_name': ''}


provider_configs = load_external_provider_configs()
text_provider = pick_provider_config(
    provider_configs,
    preferred_provider='SiliconFlow (硅基流动)',
    fallback_order=['DeepSeek Official', 'Volcengine (火山引擎/豆包)'],
)
enrich_provider = pick_provider_config(
    provider_configs,
    preferred_provider='DeepSeek Official',
    fallback_order=['SiliconFlow (硅基流动)', 'Volcengine (火山引擎/豆包)'],
)
tts_provider_config = pick_provider_config(
    provider_configs,
    preferred_provider='SiliconFlow (硅基流动)',
    fallback_order=['Volcengine (火山引擎/豆包)', 'DeepSeek Official'],
)


@dataclass
class Settings:
    """运行配置。"""

    repo_root: Path = REPO_ROOT
    exes_dir: Path = REPO_ROOT / 'exes'
    runtime_dir: Path = REPO_ROOT / 'data' / 'runtime' / 'local_chat'
    default_slug: str = os.getenv('EX_SKILL_DEFAULT_SLUG', 'example_xiaoming')
    external_config_path: str = provider_configs.get('_meta', {}).get('config_path', '')

    text_provider_name: str = os.getenv('TEXT_PROVIDER_NAME', text_provider.get('provider_name', ''))
    text_api_base_url: str = os.getenv('TEXT_API_BASE_URL', text_provider.get('base_url', 'https://api.deepseek.com'))
    text_api_key: str = os.getenv('TEXT_API_KEY', text_provider.get('api_key', ''))
    text_model_name: str = os.getenv('TEXT_MODEL_NAME', text_provider.get('model', 'deepseek-chat'))
    text_timeout: int = int(os.getenv('TEXT_TIMEOUT', '60'))
    text_temperature: float = float(os.getenv('TEXT_TEMPERATURE', '0.8'))

    enrich_provider_name: str = os.getenv('ENRICH_PROVIDER_NAME', enrich_provider.get('provider_name', ''))
    enrich_api_base_url: str = os.getenv('ENRICH_API_BASE_URL', enrich_provider.get('base_url', 'https://api.deepseek.com'))
    enrich_api_key: str = os.getenv('ENRICH_API_KEY', enrich_provider.get('api_key', ''))
    enrich_model_name: str = os.getenv('ENRICH_MODEL_NAME', enrich_provider.get('model', 'deepseek-chat'))
    enrich_timeout: int = int(os.getenv('ENRICH_TIMEOUT', '120'))
    enrich_temperature: float = float(os.getenv('ENRICH_TEMPERATURE', '0.2'))

    tts_provider: str = os.getenv('TTS_PROVIDER', 'siliconflow_clone' if tts_provider_config.get('provider_name') == 'SiliconFlow (硅基流动)' else 'none')
    tts_provider_name: str = os.getenv('TTS_PROVIDER_NAME', tts_provider_config.get('provider_name', ''))
    tts_api_base_url: str = os.getenv('TTS_API_BASE_URL', tts_provider_config.get('base_url', 'https://api.siliconflow.cn/v1'))
    tts_api_key: str = os.getenv('TTS_API_KEY', tts_provider_config.get('api_key', ''))
    tts_model: str = os.getenv('TTS_MODEL', 'FunAudioLLM/CosyVoice2-0.5B')
    tts_voice: str = os.getenv('TTS_VOICE', 'FunAudioLLM/CosyVoice2-0.5B:anna')
    tts_timeout: int = int(os.getenv('TTS_TIMEOUT', '90'))
    tts_custom_endpoint: str = os.getenv('TTS_CUSTOM_ENDPOINT', '')
    voice_reference_dir: str = os.getenv('VOICE_REFERENCE_DIR', str(REPO_ROOT / 'data' / 'voice_samples'))


settings = Settings()
