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

It exists only to demonstrate the expected structure and loading flow. Replace the page `slug` with your own pack when using real data locally.

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

## Usage suggestions

1. change the left-side `slug` to your own pack first
2. if you only want manual stickers, set automatic stickers to `off`
3. keep paced replies enabled if you want less robotic turn-taking
4. review `data/` and `exes/{slug}` before publishing anything publicly

---

## Notes

1. history is stored in browser local storage, not in a server database
2. switching browsers or clearing site storage removes local history
3. if you connect voice cloning, store samples under `data/voice_samples/` and manage those files privately
