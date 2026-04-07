# 通用宿主使用指南

本项目现在支持两条运行路径：

1. **Skill 模式**
   适用于 Claude Code / OpenClaw 这类支持 Skill frontmatter 的宿主。
2. **通用模式**
   适用于 Cursor、Codex、Gemini CLI 以及其他“能读取仓库文件并直接修改文件”的代理。

通用模式的目标不是复刻 `/create-ex` 命令，而是把原材料整理成一个**宿主无关资料包**，然后交给任意代理继续补全。

---

## 适用宿主

- Cursor
- Codex
- Gemini CLI
- Claude Code
- OpenClaw
- 其他支持文件读写的代理式编码工具

---

## 核心文件

执行通用构建器后，会在 `exes/{slug}/` 下生成这些文件：

- `meta.json`
  基础资料与来源清单
- `memory.md`
  关系记忆草稿
- `persona.md`
  人物性格草稿
- `SYSTEM_PROMPT.md`
  宿主无关系统提示词，可直接粘贴到任意 AI
- `AGENT_PROMPT.md`
  给 Cursor / Codex / Gemini CLI 的统一执行说明
- `memories/chats/source_manifest.json`
  聊天来源清单
- `memories/chats/*.md`
  每个来源的分析报告
- `memories/media/*.md`
  语音、图片、表情、视频的媒体分析报告

---

## 一次性构建资料包

### 1. 准备可读聊天记录

推荐格式：

- `txt`
- `json`（留痕 / WeFlow 导出）
- 手工整理的纯文本

如果你是微信数据，推荐优先使用 [WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file) 这类能导出可读格式的工具；  
如果你是 QQ 数据，仍建议优先使用官方客户端导出或手工整理为 `txt`。

不推荐直接喂：

- 微信官方 `ChatBackup` 目录
- `.enc`
- `.dat`
- `backup.attr`

原因：这些是官方备份容器，不是当前项目可直接解析的可读聊天文本。

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
  --videos-dir "D:\\chat\\videos" \
  --together-duration "2年" \
  --apart-since "8个月" \
  --occupation "产品经理" \
  --mbti "ENFP" \
  --impression "话多，嘴硬心软，深夜容易emo"
```

如果你希望直接把聊天记录放在本项目里，推荐改用项目内工作区模式：

```bash
python tools/project_data_builder.py --init --slug wechat-import
```

初始化后目录结构是：

```text
data/chat_records/wechat-import/
├── raw/
├── media/
│   ├── images/
│   ├── emojis/
│   ├── voice/
│   └── video/
└── notes/
```

构建命令：

```bash
python tools/project_data_builder.py --slug wechat-import --name "代号" --target "聊天昵称"
```

如果你有多份聊天记录，可以重复传入 `--chat-source`：

```bash
python tools/universal_builder.py \
  --name "小夏" \
  --target "小夏" \
  --chat-source "D:\\chat\\xiaoxia_1.txt" \
  --chat-source "D:\\chat\\xiaoxia_2.json" \
  --notes-text "她生气时会突然很安静，但第二天会假装没事"
```

---

## 在不同宿主里怎么用

### Cursor

在仓库根目录打开项目后，对代理说：

```text
请阅读 exes/{slug}/AGENT_PROMPT.md、meta.json、memory.md、persona.md、memories/chats/ 和 memories/media/ 下的分析文件，直接补全资料并重新生成 SYSTEM_PROMPT.md 与 SKILL.md。
```

### Codex

在仓库根目录执行或打开会话后，对代理说：

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

如果你只是想让任意 AI “像 ta 一样说话”，最直接的做法是：

1. 打开 `exes/{slug}/SYSTEM_PROMPT.md`
2. 把它作为系统提示词或开场设定
3. 再开始对话

这条路径最通用，基本不依赖具体宿主的 Skill 机制。

如果你已经导出了语音转写、图片、表情和视频，建议一并传入。构建器会把这些材料整理到 `memories/media/`，后续代理就能基于媒体证据补全人设，而不是只看纯文本聊天。

---

## 追加资料

当你找到新的聊天记录时：

1. 把新的 `txt/json` 放到你自己的资料目录
2. 重新执行一次 `tools/universal_builder.py`，或手动把分析结果补进 `memory.md`
3. 让代理再次读取 `AGENT_PROMPT.md` 做增量补全

如果你希望保留历史版本，可以再执行：

```bash
python tools/version_manager.py --action backup --slug {slug} --base-dir ./exes
```

---

## 关于微信官方 ChatBackup

如果你的资料目录长这样：

- `.wechat-deviceId`
- `backup.attr`
- `files/1/...`
- 大量 `.enc` / `.dat`

那说明你拿到的是**微信官方迁移备份**。这类备份当前只能被识别，不能被本项目直接解析成聊天文本。

这时正确做法是：

1. 先把聊天转换成 `txt` / `json`
2. 或者在电脑微信里复制关键聊天为纯文本
3. 再交给 `tools/universal_builder.py`

不要把 `.enc` 分片直接喂给代理，否则只会得到错误推断。
