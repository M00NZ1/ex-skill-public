# ex-skill-public

[中文](README.md) | [English](README_EN.md)

> Turn chat exports from friends, exes, or family into a reusable role pack that tries to preserve their tone, habits, and conversational presence. For learning and research only. Do not use this project for any illegal purpose.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-local%20chat-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI Compatible](https://img.shields.io/badge/API-OpenAI%20Compatible-orange.svg)](#deployment)

This project extends the role-pack workflow inspired by [perkfly/ex-skill](https://github.com/perkfly/ex-skill) and adds a host-agnostic build pipeline, a local web chat app, local sticker sending, voice interface hooks, and a repository layout suitable for public release.

The repository is designed for public publishing, so it does not ship with personal chat samples, private media, or local model credentials. Import your own chat exports locally, build a role pack, and continue using it in Cursor, Codex, Gemini CLI, Claude Code, or the bundled local web chat.

It is best understood as a public template repository that separates project code from personal chat data.

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

If available, also prepare:

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

Use this project only with chat data you are authorized to handle for learning, research, interface experiments, or personal projects.

Please keep the following in mind:

1. Do not process private data without authorization
2. Do not publish personal chat logs, media files, or private credentials in a public repository
3. Store your own role-pack data locally under `data/`, `exes/your_ex/`, and `config/providers.local.json`
4. Before publishing, re-check all real text, media files, paths, and secrets

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
