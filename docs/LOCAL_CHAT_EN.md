# Local Chat App Guide

[中文](LOCAL_CHAT.md) | [English](LOCAL_CHAT_EN.md)

## When to use it

Use the local chat app if you want more than prompt generation and need:

1. direct chatting in a browser
2. local sticker display and manual sending
3. optional automatic sticker sending
4. playable audio generated from a voice interface
5. browser-local chat history

The app lives under:

```text
apps/local_chat/
```

---

## Repository structure

The repository ships with one example pack:

```text
exes/example_xiaoming/
```

It exists only to demonstrate the expected structure and loading flow. Once the page `slug` is switched to a local pack, the app will load the real build output.

---

## Before launch

### 1. Configure providers

Two supported approaches:

1. environment variables
2. `config/providers.local.json`

References:

- [`config/local_chat.env.example`](../config/local_chat.env.example)
- [`config/providers.local.example.json`](../config/providers.local.example.json)

### 2. Prepare your own role pack

Use one of these flows:

1. run:

```bash
python tools/project_data_builder.py --init --slug your_ex
```

2. or run:

```bash
python tools/universal_builder.py --help
```

After building, your pack will appear under `exes/{slug}/`.

---

## Launch command

Run from the repository root:

```bash
uvicorn apps.local_chat.app:app --host 127.0.0.1 --port 7860 --reload
```

Then open:

[http://127.0.0.1:7860](http://127.0.0.1:7860)

---

## Current capabilities

1. load `exes/{slug}` role packs
2. switch automatic sticker behavior between `off / restrained / closer-to-original`
3. send local stickers by clicking the left panel
4. restore recent chat history from browser local storage
5. simulate reply pacing by merging rapid user messages and delaying replies
6. optionally request audio from a voice API

---

## Provider Roles

The local chat app uses three interface lanes:

### 1. Text chat interface

- config prefix: `TEXT_*`
- responsible for: reply text, sticker strategy, voice-send decision
- entry path: [app.py](../apps/local_chat/app.py) -> [llm_client.py](../apps/local_chat/services/llm_client.py)

Default priority:

1. `SiliconFlow (硅基流动)`
2. `DeepSeek Official`
3. `Volcengine (火山引擎/豆包)`

### 2. Pack enrichment interface

- config prefix: `ENRICH_*`
- responsible for: autofill and structured role-pack extraction
- entry path: [profile_autofill.py](../tools/profile_autofill.py)

Default priority:

1. `DeepSeek Official`
2. `SiliconFlow (硅基流动)`
3. `Volcengine (火山引擎/豆包)`

### 3. Voice output interface

- config prefix: `TTS_*`
- responsible for: TTS output, custom voice upload, audio file generation
- entry path: [tts_client.py](../apps/local_chat/services/tts_client.py) and [voice_profile_manager.py](../apps/local_chat/services/voice_profile_manager.py)

Default modes:

- `siliconflow_clone`
- `openai_compatible`
- `custom_http`
- `none`

---

## Runtime Behavior

1. the left-side `slug` switches the currently loaded role pack
2. when automatic stickers are set to `off`, the UI keeps only manual sticker sending
3. when paced replies are enabled, rapid user messages are merged before the delayed reply is shown
4. `data/` and `exes/{slug}` belong to the local runtime layer; the public repository keeps only code and template structure

---

## Notes

1. history is stored in browser local storage, not in a server database
2. switching browsers or clearing site storage removes local history
3. voice samples are read from `data/voice_samples/`; that directory belongs to the local data layer rather than the published repository
