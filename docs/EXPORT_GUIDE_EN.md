# Chat Export Guide

[中文](EXPORT_GUIDE.md) | [English](EXPORT_GUIDE_EN.md)

This project expects **readable chat exports**, not encrypted database files.

Recommended formats:

- `txt`
- `json`
- `html`
- manually cleaned plain text

---

## Preparing WeChat exports

### Recommended tool: WeFlow

For WeChat data, a practical export step is:

- [hicccc77/WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file)

Use it to convert local WeChat data into readable files before feeding them into this project.

### Using WeFlow output in this project

You can directly pass exported:

- `json`
- `txt`
- `html`

Then run:

```bash
python tools/universal_builder.py \
  --name "Your Codename" \
  --slug "your_ex" \
  --target "Chat Nickname" \
  --chat-source "exported_chat_file"
```

If media folders are also available, pass them as well:

```bash
python tools/universal_builder.py \
  --name "Your Codename" \
  --slug "your_ex" \
  --target "Chat Nickname" \
  --chat-source "exported_chat_file" \
  --voice-transcripts "Voices/transcripts.json" \
  --images-dir "images" \
  --emojis-dir "emojis" \
  --videos-dir "videos"
```

---

## Preparing QQ exports

For QQ chat data, the recommended path is the official client export flow or a cleaned `txt` version.

Example:

```text
me: what are you doing
them: just got off work
me: did you eat yet
them: not yet
```

As long as the file makes the speaker boundary clear, this project can continue analyzing it.

---

## Why official WeChat ChatBackup cannot be used directly

If your folder contains:

- `.wechat-deviceId`
- `backup.attr`
- `files/`
- many `.enc / .dat` files

that means you have an official WeChat migration backup, not readable chat text.

So:

1. do not feed it directly into `tools/wechat_parser.py`
2. do not expect it to become readable dialogue automatically
3. convert it into `txt / json / html` first

If you only want an inventory of the backup contents, run:

```bash
python tools/chatbackup_inventory.py \
  --backup-dir "data/ChatBackup" \
  --output-dir "data/processed/chatbackup_inventory"
```

This tool is read-only and does not fabricate missing chat text.

---

## Manual cleanup is also valid

If you do not have any export tool, plain cleaned text still works:

```text
me: are you off work now
them: just got home
me: tired?
them: exhausted
```

For role-pack construction, readable conversation content matters more than the raw database format.

---

## Best practice

These materials usually help the most:

1. late-night chats
2. conflict or argument records
3. conversations around breakup or separation
4. everyday small talk
5. voice transcripts
6. frequently used stickers
