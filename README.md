# ex-skill-public

[中文](README.md) | [English](README_EN.md)

> 可将朋友、前任、亲人等聊天记录整理为角色资料包，尽量还原他们的说话方式、交流习惯与陪伴感受。仅供学习与研究参考，严禁用于任何非法用途。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-local%20chat-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI Compatible](https://img.shields.io/badge/API-OpenAI%20Compatible-orange.svg)](#部署依赖)

本项目基于 [perkfly/ex-skill](https://github.com/perkfly/ex-skill) 的角色资料包思路继续扩展开发，补充了通用构建流程、本地网页聊天界面、本地表情包发送、语音接口接入与公开发布所需的脱敏结构。

仓库面向公开发布，默认不附带个人聊天样本、私有媒体与本地模型配置。导入你自己的聊天导出后，即可生成角色资料包，并在 Cursor、Codex、Gemini CLI、Claude Code 或本地网页中继续使用。

[开发来源与致谢](#开发来源与致谢) · [项目是什么](#项目是什么) · [功能说明](#功能说明) · [快速开始](#快速开始) · [使用流程](#使用流程) · [效果示例](#效果示例) · [安装部署](#安装部署) · [隐私与合规](#隐私与合规) · [相关文档](#相关文档)

---

## 开发来源与致谢

本项目的核心思路来自：

- [perkfly/ex-skill](https://github.com/perkfly/ex-skill)

在此基础上，当前公开版继续补充了这些方向：

1. 宿主无关的资料包构建流程
2. 适配 Cursor、Codex、Gemini CLI、Claude Code 的统一资料结构
3. 本地网页聊天应用与表情包发送面板
4. 浏览器本地历史保存与拟真回复节奏
5. 对接 OpenAI 兼容聊天接口与可选语音接口

微信聊天记录整理流程中，推荐配合：

- [hicccc77/WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file)

用于先将微信数据整理为可读的 `json / txt / html`，再接入本项目继续构建。

---

## 项目是什么

`ex-skill-public` 是一套面向聊天记录角色化的工程化工具链，核心目标是把你手中的聊天文本、语音转写、图片、表情包和视频等材料，整理为可继续使用的角色资料包。

资料包构建完成后，仓库会生成：

- `meta.json`
- `memory.md`
- `persona.md`
- `SYSTEM_PROMPT.md`
- `SKILL.md`
- `AGENT_PROMPT.md`

这些文件既可以交给代理式工具继续补全，也可以直接作为本地聊天应用的配置基础。

---

## 功能说明

### 资料构建

- 支持 `txt / json / html / 纯文本` 聊天导入
- 支持整理语音转写、图片、表情包、视频到 `memories/media/`
- 支持项目内工作区模式与直接命令构建模式
- 生成宿主无关资料包，方便在不同 AI 工具间复用

### 宿主兼容

- Cursor
- Codex
- Gemini CLI
- Claude Code
- OpenClaw
- 其他支持读取仓库文件的代理式工具

### 本地聊天应用

- 基于 FastAPI 的本地网页聊天界面
- 左侧表情包面板点击即发送
- 自动表情包三档：`关闭 / 克制 / 贴近原始`
- 浏览器本地保存最近聊天历史
- 根据资料包中的回复节奏做拟真延迟与追发合并
- 可选接入 TTS 与语音接口

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 构建角色资料包

```bash
python tools/universal_builder.py \
  --name "你的代号" \
  --slug "your_ex" \
  --target "聊天中的昵称" \
  --chat-source "你的聊天文件.txt"
```

### 3. 启动本地聊天应用

```bash
uvicorn apps.local_chat.app:app --host 127.0.0.1 --port 7860 --reload
```

### 4. 在浏览器中打开

[http://127.0.0.1:7860](http://127.0.0.1:7860)

---

## 使用流程

### 1. 准备聊天导出

推荐输入格式：

- `txt`
- `json`
- `html`
- 手工整理的纯文本

推荐来源：

- 微信：推荐使用 [WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file) 导出可读结果
- QQ：推荐使用官方客户端导出为可读文本，再接入本项目
- 其他平台：手工整理为纯文本也可使用

如果拿到的是微信官方迁移备份目录，例如 `.enc`、`.dat`、`backup.attr`、`files/` 这类内容，需要先转换为可读文本或结构化导出，再交给本项目处理。

### 2. 准备媒体材料

如果你还有这些内容，也建议一起导入：

- `transcripts.json`
- `images/`
- `emojis/`
- `videos/`

这样构建器会在 `memories/media/` 下生成语音、图片、表情包和视频报告，后续资料补全会更稳定。

### 3. 生成资料包

直接模式：

```bash
python tools/universal_builder.py \
  --name "你的代号" \
  --slug "your_ex" \
  --target "聊天昵称" \
  --chat-source "导出的聊天文件"
```

项目内工作区模式：

```bash
python tools/project_data_builder.py --init --slug your_ex
python tools/project_data_builder.py --slug your_ex --name "你的代号" --target "聊天昵称"
```

### 4. 在不同宿主中使用

- Cursor：让代理读取 `AGENT_PROMPT.md`
- Codex：让代理读取 `AGENT_PROMPT.md`、`memory.md`、`persona.md`
- Gemini CLI：让代理按资料包补全并生成最终提示词
- Claude Code：可继续沿用 Skill 模式
- 本地网页：直接在页面中输入对应 `slug`

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
页面会将这张本地表情包作为一条真实消息发送
后端再根据这条消息生成下一句回复
```

### 场景四：拟真延迟

```text
不会每次按下发送就立刻秒回
连续几条追发会先合并
再按资料包里的回复间隔做缩放延迟
```

---

## 安装部署

### 基础依赖

- Python 3.9+
- `requirements.txt` 中的依赖包

当前主要包括：

- `fastapi`
- `uvicorn`
- `httpx`
- `pydantic`

### 模型配置方式

支持两种常见方式：

1. 环境变量
2. 本地配置文件 `config/providers.local.json`

可参考：

- [config/local_chat.env.example](config/local_chat.env.example)
- [config/providers.local.example.json](config/providers.local.example.json)

### 详细说明

- 中文安装说明：[INSTALL.md](INSTALL.md)
- English Installation Guide: [INSTALL_EN.md](INSTALL_EN.md)

---

## 隐私与合规

本项目仅建议用于整理本人有权处理的聊天导出数据，用于学习、研究、界面开发或个人项目实验。

请注意：

1. 不要处理未经授权的他人隐私数据
2. 不要将个人聊天记录、媒体文件或私有配置直接提交到公开仓库
3. 本地使用时，建议将个人资料放在 `data/`、`exes/your_ex/`、`config/providers.local.json`

---

## 相关文档

### 中文

- [安装与部署](INSTALL.md)
- [通用宿主使用指南](docs/UNIVERSAL_USAGE.md)
- [聊天记录导入指南](docs/EXPORT_GUIDE.md)
- [本地聊天应用说明](docs/LOCAL_CHAT.md)

### English

- [README_EN.md](README_EN.md)
- [INSTALL_EN.md](INSTALL_EN.md)
- [Universal Usage Guide](docs/UNIVERSAL_USAGE_EN.md)
- [Chat Export Guide](docs/EXPORT_GUIDE_EN.md)
- [Local Chat Guide](docs/LOCAL_CHAT_EN.md)
