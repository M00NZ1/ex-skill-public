# ex-skill-public

> 可将朋友、前任、亲人等聊天记录整理为角色资料包，尽量还原他们的说话方式、交流习惯与陪伴感受。仅供学习与研究参考，严禁用于任何非法用途。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-local%20chat-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI Compatible](https://img.shields.io/badge/API-OpenAI%20Compatible-orange.svg)](#部署依赖)

这是一个**基于 [perkfly/ex-skill](https://github.com/perkfly/ex-skill) 思路继续扩展开发**的公开版仓库。  
当前版本移除了真实聊天记录、媒体文件、运行缓存和私人 API 配置，只保留完整工程代码、文档、通用构建工具和本地聊天应用，方便你用自己的聊天记录继续构建角色资料包。

[开发来源与致谢](#开发来源与致谢) · [项目是什么](#项目是什么) · [功能说明](#功能说明) · [怎么使用](#怎么使用) · [教程](#教程) · [效果示例](#效果示例) · [安装说明](#安装说明) · [部署依赖](#部署依赖) · [隐私说明](#隐私说明)

---

## 开发来源与致谢

本项目的公开版整理与工程化扩展，明确致敬：

- [perkfly/ex-skill](https://github.com/perkfly/ex-skill)

公开版在其原始思路基础上，继续补充了这些方向：

1. 通用宿主资料包构建流程
2. 本地网页聊天应用
3. 本地表情包与语音接口接入层
4. 公开发布所需的脱敏结构

聊天记录准备工具说明中，同时感谢：

- [hicccc77/WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file)

根据 WeFlow 官方 README，它是一个本地微信聊天记录查看、分析与导出工具。对于微信聊天记录整理与导出，这是非常实用的一条路径。

---

## 项目是什么

`ex-skill-public` 是一个**聊天记录角色化工具链**，核心目标是：

1. 读取你自己的聊天记录、语音转写、图片、表情包等材料
2. 将原材料整理成宿主无关的资料包
3. 生成 `memory.md`、`persona.md`、`SYSTEM_PROMPT.md`、`SKILL.md`
4. 提供一个本地网页聊天应用，把提示词、本地表情包和语音接口真正接起来

它不是一个“内置真实数据的成品角色”，而是一套**从私人聊天记录到可用角色资料包**的工程化流程。

---

## 功能说明

### 资料构建

- 支持 `txt / json / html / 纯文本` 聊天导入
- 支持把语音转写、图片、表情、视频整理进 `memories/media/`
- 生成宿主无关资料包，可继续交给不同 AI 宿主补全

### 宿主兼容

- Claude Code / OpenClaw
- Cursor
- Codex
- Gemini CLI
- 其他支持读写文件的代理式工具

### 本地聊天应用

- 本地网页聊天界面
- 左侧表情包面板点击即发送
- 自动表情包三档：`关闭 / 克制 / 贴近原始`
- 浏览器本地保存聊天历史，刷新后恢复
- 拟真回复节奏：连续追发消息会先合并，再按资料包里的回复间隔做缩放延迟
- 可对接 OpenAI 兼容聊天接口
- 可对接 TTS/语音接口

---

## 怎么使用

### 方式一：通用构建模式

适合 Cursor、Codex、Gemini CLI、Claude Code 等环境。

先准备一份可读聊天记录，然后执行：

```bash
python tools/universal_builder.py \
  --name "你的代号" \
  --slug "your_ex" \
  --target "聊天中对方的昵称" \
  --chat-source "你的聊天文件.txt"
```

生成后，核心结果位于：

```text
exes/your_ex/
├── meta.json
├── memory.md
├── persona.md
├── SYSTEM_PROMPT.md
├── SKILL.md
└── AGENT_PROMPT.md
```

### 方式二：项目内工作区模式

如果你想把自己的聊天资料放在项目内管理，先初始化：

```bash
python tools/project_data_builder.py --init --slug your_ex
```

然后把资料按结构放入：

```text
data/chat_records/your_ex/
├── raw/
├── media/
│   ├── images/
│   ├── emojis/
│   ├── voice/
│   └── video/
└── notes/
```

最后构建：

```bash
python tools/project_data_builder.py --slug your_ex --name "你的代号" --target "聊天昵称"
```

### 方式三：本地聊天应用

启动：

```bash
uvicorn apps.local_chat.app:app --host 127.0.0.1 --port 7860 --reload
```

浏览器打开：

[http://127.0.0.1:7860](http://127.0.0.1:7860)

默认公开示例资料包是：

```text
exes/example_xiaoming/
```

你把左侧 `slug` 改成自己的资料包名后，就能直接使用自己的数据。

---

## 教程

### 1. 先准备聊天记录

推荐优先使用这些来源：

- 微信：推荐 [WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file) 导出 `JSON / HTML / TXT` 等格式
- QQ：推荐官方客户端导出，或复制为 `txt`
- 其他平台：手工整理为纯文本也可以

注意：

1. 根据 WeFlow 官方 README，它明确定位为**微信聊天记录导出与分析工具**，并注明“仅支持微信 4.0 及以上版本”。
2. 我不会在文档里把 WeFlow 写成 QQ 提取工具，因为它的官方说明没有这么写。
3. 如果你要处理 QQ，建议仍走 QQ 官方导出、手工整理或其他你自行评估的方案。

### 2. 把媒体也一起准备好

如果你还有这些材料，也建议一起放入：

- `transcripts.json`
- `images/`
- `emojis/`
- `videos/`

这样构建器会把它们整理到 `memories/media/`，提升角色还原度。

### 3. 生成资料包

最简单的命令：

```bash
python tools/universal_builder.py --help
```

或者：

```bash
python tools/project_data_builder.py --init --slug your_ex
```

### 4. 在不同环境里继续使用

- Cursor：让代理读取 `AGENT_PROMPT.md`
- Codex：让代理读取 `AGENT_PROMPT.md` 和 `SYSTEM_PROMPT.md`
- Claude Code：可继续用 Skill 模式
- 本地网页：直接切到你的 `slug`

---

## 效果示例

> 输入设定：`话多、嘴硬心软、晚上活跃、短句连发、常用表情包、偶尔发语音`

### 场景一：日常聊天

```text
用户        > 在干嘛

角色回复     > 刚忙完
            > 你呢
            > 怎么这会儿才来找我
```

### 场景二：连续追发消息

```text
用户        > 睡了吗
用户        > 还在不在
用户        > 我有点想你

角色回复     > 没睡
            > 你今天怎么突然这么黏人
```

### 场景三：手动发表情包

```text
用户在左侧表情包面板点选一张表情包
页面会把这张本地表情包作为一条真实消息发送
后端再根据这条消息生成下一句回复
```

### 场景四：拟真延迟

```text
不会每次按下发送就立刻秒回
连续几条追发会先合并
再按资料包里的回复间隔做缩放延迟
```

---

## 安装说明

### 1. 克隆仓库

```bash
git clone <你的仓库地址>
cd ex-skill-public
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 准备模型配置

可选两种方式：

1. 使用环境变量
2. 在本地创建：

```text
config/providers.local.json
```

你可以参考：

- [config/local_chat.env.example](config/local_chat.env.example)
- [config/providers.local.example.json](config/providers.local.example.json)

### 4. 构建你的资料包

```bash
python tools/project_data_builder.py --init --slug your_ex
```

或：

```bash
python tools/universal_builder.py --help
```

### 5. 启动本地聊天应用

```bash
uvicorn apps.local_chat.app:app --host 127.0.0.1 --port 7860 --reload
```

---

## 部署依赖

### 基础运行依赖

- Python 3.9+
- `requirements.txt` 中的 Python 包

当前主要包括：

- `fastapi`
- `uvicorn`
- `httpx`
- `pydantic`

### 本地聊天应用依赖

- 一个 OpenAI 兼容聊天接口
- 可选的 TTS/语音接口

### 可选辅助工具

- 微信记录提取：推荐 [WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file)
- QQ 记录导出：推荐官方客户端导出

---

## 隐私说明

这个公开版仓库已经移除：

1. 真实聊天记录
2. 真实图片、表情包、语音、视频
3. 本地运行缓存
4. 私人资料包
5. 真实 API Key
6. 私有路径和本机目录引用

你自己的真实数据建议只放在：

- `data/`
- `exes/your_ex/`
- `config/providers.local.json`

并确保这些内容不要提交到 GitHub。

---

## 相关文档

- [INSTALL.md](INSTALL.md)
- [docs/UNIVERSAL_USAGE.md](docs/UNIVERSAL_USAGE.md)
- [docs/EXPORT_GUIDE.md](docs/EXPORT_GUIDE.md)
- [docs/LOCAL_CHAT.md](docs/LOCAL_CHAT.md)
