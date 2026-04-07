# Universal Host Usage Guide

[中文](UNIVERSAL_USAGE.md) | [English](UNIVERSAL_USAGE_EN.md)

This project supports two runtime paths:

1. **Skill mode**
   For hosts such as Claude Code or OpenClaw that understand Skill frontmatter.
2. **Universal mode**
   For Cursor, Codex, Gemini CLI, and other agent-style tools that can read repository files and continue editing them.

The goal of universal mode is not to recreate a single hard-coded command flow. It is to turn your raw chat materials into a **host-agnostic role pack** that any agent can continue from.

---

## Supported hosts

- Cursor
- Codex
- Gemini CLI
- Claude Code
- OpenClaw
- other agent tools with file read/write capability

---

## Core files

After building, `exes/{slug}/` contains:

- `meta.json`
- `memory.md`
- `persona.md`
- `SYSTEM_PROMPT.md`
- `AGENT_PROMPT.md`
- `SKILL.md`
- `memories/chats/*.md`
- `memories/media/*.md`

In practice:

- `SYSTEM_PROMPT.md` is suitable as a direct system prompt
- `AGENT_PROMPT.md` is suitable for Cursor, Codex, Gemini CLI, and similar agents

---

## Build a role pack in one pass

### 1. Prepare readable chat exports

Recommended formats:

- `txt`
- `json`
- `html`
- manually cleaned plain text

For WeChat, convert the source data with a readable export tool such as [WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file). For QQ, prefer the official export flow or a cleaned `txt` file.

Avoid feeding these directly:

- official WeChat `ChatBackup`
- `.enc`
- `.dat`
- `backup.attr`

Those are backup container files, not readable message text.

### 2. Run the build command

```bash
python tools/universal_builder.py \
  --name "Xiaoxia" \
  --slug "xiaoxia" \
  --target "Xiaoxia" \
  --chat-source "D:\\chat\\xiaoxia.txt" \
  --voice-transcripts "D:\\chat\\Voices\\transcripts.json" \
  --images-dir "D:\\chat\\images" \
  --emojis-dir "D:\\chat\\emojis" \
  --videos-dir "D:\\chat\\videos"
```

If you want to keep all source materials inside this repository, use workspace mode:

```bash
python tools/project_data_builder.py --init --slug wechat-import
python tools/project_data_builder.py --slug wechat-import --name "Codename" --target "Chat Nickname"
```

If you have multiple chat files, pass `--chat-source` more than once.

---

## Using the pack in different hosts

### Cursor

Tell the agent:

```text
Read exes/{slug}/AGENT_PROMPT.md, meta.json, memory.md, persona.md, plus the files under memories/chats/ and memories/media/, then complete the role pack and regenerate SYSTEM_PROMPT.md and SKILL.md.
```

### Codex

Tell the agent:

```text
Follow exes/{slug}/AGENT_PROMPT.md, preserve evidence, avoid fabrication, complete memory.md and persona.md, and regenerate SYSTEM_PROMPT.md and SKILL.md.
```

### Gemini CLI

Tell the agent:

```text
Read the role pack under exes/{slug} and finish the character build. If the chat source is not readable, stop and explain what readable text is still missing.
```

---

## Direct chat usage

If you only want another AI to speak more like the target person:

1. open `exes/{slug}/SYSTEM_PROMPT.md`
2. use it as the system prompt or starting setup
3. start chatting

If you also provide voice transcripts, images, stickers, and videos, the builder will place them under `memories/media/`, which gives the follow-up agent more evidence to work from.

---

## Adding more materials later

When you find additional chat logs:

1. place the new `txt/json` files into your local data directory
2. run `tools/universal_builder.py` again
3. let the agent re-read `AGENT_PROMPT.md` for incremental completion

If you want historical backups, run:

```bash
python tools/version_manager.py --action backup --slug {slug} --base-dir ./exes
```
