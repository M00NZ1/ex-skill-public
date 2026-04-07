"""本地部署聊天应用。"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .schemas import (
    ChatRequest,
    ChatResponse,
    ProfileResponse,
    ReplyProfile,
    StickerCandidate,
    VoiceProfileResponse,
)
from .services.llm_client import chat_with_model
from .services.profile_loader import load_profile
from .services.tts_client import synthesize_voice
from .services.voice_profile_manager import (
    load_cached_voice_profile,
    upload_reference_voice_to_siliconflow,
)


app = FastAPI(title='前任本地聊天应用', version='0.1.0')

STATIC_DIR = Path(__file__).resolve().parent / 'static'
settings.runtime_dir.mkdir(parents=True, exist_ok=True)
(settings.runtime_dir / 'audio').mkdir(parents=True, exist_ok=True)

app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')
if (settings.repo_root / 'data' / 'emojis').exists():
    app.mount('/emoji-assets', StaticFiles(directory=str(settings.repo_root / 'data' / 'emojis')), name='emoji-assets')
if (settings.repo_root / 'data' / 'images').exists():
    app.mount('/image-assets', StaticFiles(directory=str(settings.repo_root / 'data' / 'images')), name='image-assets')
app.mount('/runtime-audio', StaticFiles(directory=str(settings.runtime_dir / 'audio')), name='runtime-audio')


def ensure_voice_profile(slug: str) -> dict:
    """确保当前资料包存在可用的自定义声线。"""
    cached = load_cached_voice_profile(settings.runtime_dir, slug)
    if cached.get('voice_uri'):
        return cached

    if settings.tts_provider != 'siliconflow_clone':
        return {}

    return upload_reference_voice_to_siliconflow(
        runtime_dir=settings.runtime_dir,
        repo_root=settings.repo_root,
        slug=slug,
        api_base_url=settings.tts_api_base_url,
        api_key=settings.tts_api_key,
        model=settings.tts_model,
    )


@app.get('/')
def index():
    """返回前端页面。"""
    return FileResponse(STATIC_DIR / 'index.html')


@app.get('/api/profile/{slug}', response_model=ProfileResponse)
def get_profile(slug: str):
    """读取一个资料包。"""
    try:
        profile = load_profile(settings.repo_root, settings.exes_dir, slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ProfileResponse(
        slug=profile['slug'],
        name=profile['name'],
        summary=profile['summary'],
        sticker_candidates=[StickerCandidate(**item) for item in profile['sticker_candidates']],
        reply_profile=ReplyProfile(**profile['reply_profile']),
    )


@app.post('/api/voice-profile/{slug}', response_model=VoiceProfileResponse)
def build_voice_profile(slug: str):
    """构建或返回资料包的自定义声线。"""
    try:
        load_profile(settings.repo_root, settings.exes_dir, slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        payload = ensure_voice_profile(slug)
    except Exception as exc:  # noqa: BLE001
        return VoiceProfileResponse(
            slug=slug,
            ready=False,
            message=f'构建声线失败：{exc}',
        )

    if not payload.get('voice_uri'):
        return VoiceProfileResponse(
            slug=slug,
            ready=False,
            message='当前未启用自定义声线提供商，或缺少可用语音样本。',
        )

    return VoiceProfileResponse(
        slug=slug,
        ready=True,
        provider=str(payload.get('provider', '')),
        model=str(payload.get('model', '')),
        voice_uri=str(payload.get('voice_uri', '')),
        sample_path=str(payload.get('sample_path', '')),
        sample_duration=float(payload.get('sample_duration', 0) or 0),
        sample_transcript=str(payload.get('sample_transcript', '')),
        message='声线已就绪',
    )


@app.post('/api/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    """执行一次聊天。"""
    try:
        profile = load_profile(settings.repo_root, settings.exes_dir, request.slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        model_result = chat_with_model(
            base_url=settings.text_api_base_url,
            api_key=settings.text_api_key,
            model=settings.text_model_name,
            timeout=settings.text_timeout,
            temperature=settings.text_temperature,
            profile=profile,
            user_message=request.message,
            history=[item.model_dump() for item in request.history],
            sticker_mode=request.sticker_mode,
            manual_sticker_md5=str(request.manual_sticker_md5 or '').strip(),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'聊天模型调用失败：{exc}') from exc

    sticker_md5 = str(model_result.get('sticker_md5', '') or '').strip()
    sticker_url = None
    if model_result.get('use_sticker') and sticker_md5:
        for item in profile['sticker_candidates']:
            if item['md5'] == sticker_md5 and item['url']:
                sticker_url = item['url']
                break

    voice_text = str(model_result.get('voice_text', '') or '').strip()
    send_voice = bool(model_result.get('send_voice')) and request.enable_voice and bool(voice_text)
    audio_url = None
    voice_profile = {}
    if send_voice:
        try:
            if settings.tts_provider == 'siliconflow_clone':
                voice_profile = ensure_voice_profile(request.slug)
            audio_url = synthesize_voice(
                provider=settings.tts_provider,
                runtime_dir=settings.runtime_dir,
                slug=request.slug,
                text=voice_text,
                api_base_url=settings.tts_api_base_url,
                api_key=settings.tts_api_key,
                model=settings.tts_model,
                voice=settings.tts_voice,
                timeout=settings.tts_timeout,
                custom_endpoint=settings.tts_custom_endpoint,
                voice_reference_dir=settings.voice_reference_dir,
                voice_override=str(voice_profile.get('voice_uri', '') or ''),
            )
        except Exception as exc:  # noqa: BLE001
            audio_url = None
            model_result['sticker_reason'] = f"{model_result.get('sticker_reason', '')} 语音合成失败：{exc}".strip()

    return ChatResponse(
        reply_text=str(model_result.get('reply_text', '') or '').strip(),
        emotion=str(model_result.get('emotion', '') or '').strip(),
        emoji_text=str(model_result.get('emoji_text', '') or '').strip(),
        sticker_md5=sticker_md5 or None,
        sticker_url=sticker_url,
        sticker_reason=str(model_result.get('sticker_reason', '') or '').strip(),
        send_voice=send_voice,
        voice_text=voice_text,
        audio_url=audio_url,
        debug_note=(
            f"文本模型：{settings.text_provider_name or settings.text_model_name}；"
            f"语音提供商：{settings.tts_provider_name or settings.tts_provider}；"
            f"自动表情包模式：{request.sticker_mode}。"
        ),
    )
