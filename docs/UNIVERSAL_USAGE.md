# 通用宿主使用指南

[中文](UNIVERSAL_USAGE.md) | [English](UNIVERSAL_USAGE_EN.md)

本项目支持两条运行路径：

1. **Skill 模式**
   适用于 Claude Code、OpenClaw 这类支持 Skill frontmatter 的宿主。
2. **通用模式**
   适用于 Cursor、Codex、Gemini CLI 以及其他能读取仓库文件并继续补全资料的代理式工具。

通用模式的目标不是复刻某个固定命令，而是把聊天原材料整理为一份**宿主无关资料包**，再交给不同代理继续使用。

---

## 适用宿主

- Cursor
- Codex
- Gemini CLI
- Claude Code
- OpenClaw
- 其他支持文件读写的代理式工具

---

## 核心文件

执行构建器后，会在 `exes/{slug}/` 下生成：

- `meta.json`
- `memory.md`
- `persona.md`
- `SYSTEM_PROMPT.md`
- `AGENT_PROMPT.md`
- `SKILL.md`
- `memories/chats/*.md`
- `memories/media/*.md`

其中：

- `SYSTEM_PROMPT.md` 适合直接作为系统提示词
- `AGENT_PROMPT.md` 适合交给 Cursor、Codex、Gemini CLI 等代理继续补全

---

## 一次性构建资料包

### 1. 准备可读聊天记录

推荐格式：

- `txt`
- `json`
- `html`
- 手工整理的纯文本

如果你处理的是微信数据，推荐先使用 [WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file) 这类工具导出为可读格式；如果你处理的是 QQ 数据，建议优先使用官方客户端导出或自行整理为 `txt`。

不建议直接使用：

- 微信官方 `ChatBackup`
- `.enc`
- `.dat`
- `backup.attr`

因为这些属于官方备份容器，不是当前项目可直接解析的聊天正文。

### 2. 执行构建命令

```bash
python tools/universal_builder.py \
  --name "小夏" \
  --slug "xiaoxia" \
  --target "小夏" \
  --chat-source "D:\\chat\\xiaoxia.txt" \
  --voice-transcripts "D:\\chat\\Voices\\transcripts.json" \
  --images-dir "D:\\chat\\images" \
  --emojis-dir "D:\\chat\\emojis" \
  --videos-dir "D:\\chat\\videos"
```

如果你希望把聊天记录放在本项目内，推荐改用项目内工作区模式：

```bash
python tools/project_data_builder.py --init --slug wechat-import
python tools/project_data_builder.py --slug wechat-import --name "代号" --target "聊天昵称"
```

如果你有多份聊天记录，可以重复传入 `--chat-source`。

---

## 在不同宿主里怎么用

### Cursor

对代理说：

```text
请阅读 exes/{slug}/AGENT_PROMPT.md、meta.json、memory.md、persona.md、memories/chats/ 和 memories/media/ 下的分析文件，补全资料并重新生成 SYSTEM_PROMPT.md 与 SKILL.md。
```

### Codex

对代理说：

```text
按 exes/{slug}/AGENT_PROMPT.md 的要求执行，优先保留证据，不要虚构；补全 memory.md、persona.md，并重新生成 SYSTEM_PROMPT.md 与 SKILL.md。
```

### Gemini CLI

对代理说：

```text
请读取 exes/{slug} 下的资料包并完成角色构建；如果聊天来源不可直接解析，请停止编造并指出缺少的可读聊天文本。
```

---

## 如何直接聊天

如果你只是想让任意 AI 尽量模拟对方的说话方式，最直接的做法是：

1. 打开 `exes/{slug}/SYSTEM_PROMPT.md`
2. 把它作为系统提示词或开场设定
3. 再开始对话

如果你已经导出了语音转写、图片、表情和视频，建议一并传入。构建器会把这些材料整理到 `memories/media/`，后续代理就能基于更多证据继续补全。

---

## 追加资料

当你找到新的聊天记录时：

1. 把新的 `txt/json` 放到自己的资料目录
2. 重新执行 `tools/universal_builder.py`
3. 让代理再次读取 `AGENT_PROMPT.md` 做增量补全

如果你希望保留历史版本，可以执行：

```bash
python tools/version_manager.py --action backup --slug {slug} --base-dir ./exes
```
