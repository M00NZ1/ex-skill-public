# Installation and Deployment Guide

[中文](INSTALL.md) | [English](INSTALL_EN.md)

This document is the English installation entry for the public repository.
Chinese documentation is the primary presentation layer for this repository.

## Scope

This project supports two main usage patterns:

1. Use it only as a role-pack build toolkit
2. Run the local web chat app as well

---

## Requirements

- Python 3.9+
- `pip`
- Optional: Node.js
  Only needed for frontend script checks, not for running the local chat app

---

## Step 1: Clone the repository

```bash
git clone <your-repository-url>
cd ex-skill-public
```

---

## Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

---

## Step 3: Configure model providers

Choose one of the following:

### Option A: Environment variables

Reference:

- [`config/local_chat.env.example`](config/local_chat.env.example)

### Option B: Local config file

Create:

```text
config/providers.local.json
```

Reference template:

- [`config/providers.local.example.json`](config/providers.local.example.json)

### Provider Roles

After installation, runtime configuration is split into three interface groups:

1. `TEXT_*`
   Handles live chat replies and sticker strategy in the local web app.
2. `ENRICH_*`
   Handles role-pack autofill and structured extraction in `tools/profile_autofill.py`.
3. `TTS_*`
   Handles voice output and optional voice cloning.

According to the current code defaults:

- live text chat prefers `SiliconFlow (硅基流动)`
- autofill prefers `DeepSeek Official`
- voice output prefers `SiliconFlow (硅基流动)` and defaults to `siliconflow_clone`

---

## Step 4: Prepare chat exports

Recommended reading:

- [`docs/EXPORT_GUIDE.md`](docs/EXPORT_GUIDE.md)
- [`docs/EXPORT_GUIDE_EN.md`](docs/EXPORT_GUIDE_EN.md)

Import pipeline summary:

1. WeChat data should be converted into readable `json / txt / html`
2. QQ data should preferably come from official export flows or be cleaned into text
3. Official WeChat `ChatBackup` folders must be converted before use

---

## Step 5: Build the role pack

### Option A: Direct build

```bash
python tools/universal_builder.py \
  --name "Your Codename" \
  --slug "your_ex" \
  --target "Chat Nickname" \
  --chat-source "your_chat_file.txt"
```

### Option B: In-project workspace

Initialize first:

```bash
python tools/project_data_builder.py --init --slug your_ex
```

Then build:

```bash
python tools/project_data_builder.py --slug your_ex --name "Your Codename" --target "Chat Nickname"
```

---

## Step 6: Start the local chat app

```bash
uvicorn apps.local_chat.app:app --host 127.0.0.1 --port 7860 --reload
```

Open:

[http://127.0.0.1:7860](http://127.0.0.1:7860)

---

## Deployment Notes

### Build dependencies

- Python
- packages from `requirements.txt`

### Local chat dependencies

- an OpenAI-compatible chat API
- optional TTS or voice API

### Local private data

The local runtime layer reads chat texts, media samples, and private provider settings from:

```text
data/
exes/your_ex/
config/providers.local.json
```

The published repository itself stays in a code-and-template-only form; real texts, media samples, and secret configuration remain local.

---

## FAQ

### 1. Why does the repository not include real chat samples?

This is a public engineering template. Import your own chat exports locally and build your own role pack.

### 2. Why is the default example called `example_xiaoming`?

It is only a structure demo used to show how the app loads a role pack. It does not represent any real person.

### 3. Can I use only the pack files without the local chat app?

Yes. You can hand `SYSTEM_PROMPT.md`, `AGENT_PROMPT.md`, and the other generated files to Cursor, Codex, Claude Code, or Gemini CLI directly.
