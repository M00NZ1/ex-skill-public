"""接口数据结构。"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """前端传入的聊天消息。"""

    role: str = Field(..., description='消息角色')
    content: str = Field(..., description='消息内容')
    emoji_text: str = Field(default='', description='消息中的 emoji 字符')
    sticker_md5: Optional[str] = Field(default=None, description='消息使用的表情包 md5')
    sticker_url: Optional[str] = Field(default=None, description='消息使用的表情包地址')


class ChatRequest(BaseModel):
    """聊天请求。"""

    slug: str = Field(..., description='资料包代号')
    message: str = Field(..., description='用户当前输入')
    history: List[ChatMessage] = Field(default_factory=list, description='历史消息')
    enable_voice: bool = Field(default=False, description='是否尝试生成语音')
    manual_sticker_md5: Optional[str] = Field(default=None, description='用户主动发送的表情包 md5')
    sticker_mode: str = Field(default='light', description='自动表情包模式：off、light、natural')


class StickerCandidate(BaseModel):
    """表情包候选。"""

    md5: str
    count: int
    local_file: str
    url: str


class ReplyProfile(BaseModel):
    """回复节奏配置。"""

    median_reply_seconds: int = 18
    p75_reply_seconds: int = 60
    source: str = 'default'


class ChatResponse(BaseModel):
    """聊天响应。"""

    reply_text: str
    emotion: str
    emoji_text: str
    sticker_md5: Optional[str] = None
    sticker_url: Optional[str] = None
    sticker_reason: str = ''
    send_voice: bool = False
    voice_text: str = ''
    audio_url: Optional[str] = None
    debug_note: str = ''


class ProfileResponse(BaseModel):
    """人物资料响应。"""

    slug: str
    name: str
    summary: str
    sticker_candidates: List[StickerCandidate]
    reply_profile: ReplyProfile


class VoiceProfileResponse(BaseModel):
    """语音声线配置响应。"""

    slug: str
    ready: bool
    provider: str = ''
    model: str = ''
    voice_uri: str = ''
    sample_path: str = ''
    sample_duration: float = 0
    sample_transcript: str = ''
    message: str = ''
