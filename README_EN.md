# ex-skill-public

[中文](README.md) | [English](README_EN.md)

> Turn chat exports from friends, exes, or family into a reusable role pack that tries to preserve their tone, habits, and conversational presence. For learning and research only. Do not use this project for any illegal purpose.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-local%20chat-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI Compatible](https://img.shields.io/badge/API-OpenAI%20Compatible-orange.svg)](#deployment)

This project extends the role-pack workflow inspired by [perkfly/ex-skill](https://github.com/perkfly/ex-skill) and adds a host-agnostic build pipeline, a local web chat app, local sticker sending, voice interface hooks, and a repository layout suitable for public release.

This repository is organized around a simple split: public code stays in the repository, personal chat data stays local. The public edition ships with the toolchain, templates, a sanitized example pack, and the local web chat app; real chat exports, media samples, and local model credentials are connected locally and then used in Cursor, Codex, Gemini CLI, Claude Code, or the bundled web chat.
Chinese documentation remains the primary presentation layer for this repository.

[Credits](#credits) · [What It Is](#what-it-is) · [Features](#features) · [Quick Start](#quick-start) · [Workflow](#workflow) · [Examples](#examples) · [Deployment](#deployment) · [Privacy and Compliance](#privacy-and-compliance) · [Docs](#docs)

---

## Credits

The main product idea is inspired by:

- [perkfly/ex-skill](https://github.com/perkfly/ex-skill)

This public edition expands that direction with:

1. A host-agnostic role-pack build flow
2. A shared structure for Cursor, Codex, Gemini CLI, and Claude Code
3. A local web chat app with a sticker panel
4. Browser-side chat history and paced reply behavior
5. OpenAI-compatible chat support and optional voice hooks

For WeChat export workflows, this project also recommends:

- [hicccc77/WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file)

Use it to convert local WeChat data into readable `json / txt / html` exports before feeding them into this project.

---

## What It Is

`ex-skill-public` is an engineering toolkit for turning private chat materials into reusable role packs.

The build process can combine:

- chat logs
- voice transcripts
- images
- stickers
- videos

After building, the project generates:

- `meta.json`
- `memory.md`
- `persona.md`
- `SYSTEM_PROMPT.md`
- `SKILL.md`
- `AGENT_PROMPT.md`

These files can be consumed by agent tools directly or loaded by the local chat app.

---

## Features

### Build Pipeline

- Supports `txt / json / html / plain text` imports
- Organizes media evidence into `memories/media/`
- Supports both direct CLI builds and in-project workspace builds
- Produces reusable host-independent role packs

### Host Compatibility

- Cursor
- Codex
- Gemini CLI
- Claude Code
- OpenClaw
- Other agent-style tools that can read repository files

### Local Chat App

- FastAPI-based local web UI
- Click-to-send local sticker panel
- Three automatic sticker modes: `off / restrained / closer-to-original`
- Browser-local chat history restore
- Simulated reply pacing based on role-pack timing signals
- Optional TTS / voice interface integration

### Provider Roles

The project currently separates model interfaces into three channels:

1. `TEXT_*`
   Used for live chat replies, sticker decisions, and response pacing in the web app; implemented in [app.py](apps/local_chat/app.py) and [llm_client.py](apps/local_chat/services/llm_client.py).
2. `ENRICH_*`
   Used for role-pack autofill and structured extraction; implemented in [profile_autofill.py](tools/profile_autofill.py).
3. `TTS_*`
   Used for voice output and optional voice cloning; implemented in [tts_client.py](apps/local_chat/services/tts_client.py) and [voice_profile_manager.py](apps/local_chat/services/voice_profile_manager.py).

The built-in provider map currently includes:

- `DeepSeek Official`
- `SiliconFlow (硅基流动)`
- `Volcengine (火山引擎/豆包)`

The default priority in code is:

1. live text chat prefers `SiliconFlow (硅基流动)`, then falls back to `DeepSeek Official`, then `Volcengine`
2. autofill prefers `DeepSeek Official`, then falls back to `SiliconFlow (硅基流动)`, then `Volcengine`
3. voice output prefers `SiliconFlow (硅基流动)` and defaults to the `siliconflow_clone` path; it can also be switched to `openai_compatible`, `custom_http`, or `none`

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Build a role pack

```bash
python tools/universal_builder.py \
  --name "Your Codename" \
  --slug "your_ex" \
  --target "Chat Nickname" \
  --chat-source "your_chat_file.txt"
```

### 3. Start the local chat app

```bash
uvicorn apps.local_chat.app:app --host 127.0.0.1 --port 7860 --reload
```

### 4. Open the browser

[http://127.0.0.1:7860](http://127.0.0.1:7860)

---

## Workflow

### 1. Prepare readable chat exports

Recommended formats:

- `txt`
- `json`
- `html`
- manually cleaned plain text

Recommended sources:

- WeChat: export readable data with [WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file)
- QQ: use the official export flow or clean the content into plain text
- Other platforms: manually cleaned plain text is also acceptable

If all you have is an official WeChat migration backup with `.enc`, `.dat`, `backup.attr`, or `files/`, convert it into readable text or structured exports first.

### 2. Add media materials

The role pack can also take these media inputs:

- `transcripts.json`
- `images/`
- `emojis/`
- `videos/`

This allows the builder to produce richer reports under `memories/media/`.

### 3. Generate the pack

Direct mode:

```bash
python tools/universal_builder.py \
  --name "Your Codename" \
  --slug "your_ex" \
  --target "Chat Nickname" \
  --chat-source "exported_chat_file"
```

Workspace mode:

```bash
python tools/project_data_builder.py --init --slug your_ex
python tools/project_data_builder.py --slug your_ex --name "Your Codename" --target "Chat Nickname"
```

### 4. Use it in different hosts

- Cursor: ask the agent to read `AGENT_PROMPT.md`
- Codex: ask the agent to read `AGENT_PROMPT.md`, `memory.md`, and `persona.md`
- Gemini CLI: ask the agent to complete the role pack from the generated files
- Claude Code: keep using the Skill-oriented flow
- Local web UI: switch the page `slug` to your own pack

---

## Examples

> Input profile: `talkative, soft-hearted behind a tough tone, active at night, short burst replies, frequent stickers, occasional voice messages`

### Scenario 1: Casual chat

```text
User         > what are you doing

Role reply   > just finished up
             > what about you
             > why did you only come to me now
```

### Scenario 2: Rapid consecutive messages

```text
User         > are you asleep
User         > are you still there
User         > I kinda miss you

Role reply   > not asleep
             > why are you suddenly this clingy today
```

### Scenario 3: Manual sticker send

```text
The user clicks a local sticker in the left panel
The page sends that sticker as a real message
The backend then generates the next reply based on it
```

### Scenario 4: Paced replies

```text
Replies do not have to appear instantly
Consecutive user messages can be merged first
Then the final reply is delayed using timing signals from the role pack
```

---

## Deployment

### Base dependencies

- Python 3.9+
- packages listed in `requirements.txt`

Main packages include:

- `fastapi`
- `uvicorn`
- `httpx`
- `pydantic`

### Model configuration

Two common options are supported:

1. environment variables
2. local config file at `config/providers.local.json`

References:

- [config/local_chat.env.example](config/local_chat.env.example)
- [config/providers.local.example.json](config/providers.local.example.json)

Detailed guides:

- Chinese install guide: [INSTALL.md](INSTALL.md)
- English install guide: [INSTALL_EN.md](INSTALL_EN.md)

---

## Privacy and Compliance

The public repository is meant to contain only engineering code, templates, docs, and sanitized example structure. Real chat exports, media samples, absolute local paths, and private credentials belong to the local runtime layer rather than the published repository.

The default local integration points are:

- `data/`
- `exes/your_ex/`
- `config/providers.local.json`

When the project is published publicly, repository contents should stay in a code-and-template-only state, without real chat text, media samples, path references, or secret configuration.

---

## Docs

### Chinese

- [README.md](README.md)
- [INSTALL.md](INSTALL.md)
- [docs/UNIVERSAL_USAGE.md](docs/UNIVERSAL_USAGE.md)
- [docs/EXPORT_GUIDE.md](docs/EXPORT_GUIDE.md)
- [docs/LOCAL_CHAT.md](docs/LOCAL_CHAT.md)

### English

- [README_EN.md](README_EN.md)
- [INSTALL_EN.md](INSTALL_EN.md)
- [docs/UNIVERSAL_USAGE_EN.md](docs/UNIVERSAL_USAGE_EN.md)
- [docs/EXPORT_GUIDE_EN.md](docs/EXPORT_GUIDE_EN.md)
- [docs/LOCAL_CHAT_EN.md](docs/LOCAL_CHAT_EN.md)
