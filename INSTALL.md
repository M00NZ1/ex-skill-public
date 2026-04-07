# 安装与部署说明

[中文](INSTALL.md) | [English](INSTALL_EN.md)

此文档是公开仓库的中文安装入口，适合首次部署或快速确认依赖与运行步骤。
仓库对外展示默认以中文文档作为主要入口。

## 适用范围

本项目支持两条主要使用路径：

1. 仅将其作为资料包构建工具使用
2. 同时启动本地网页聊天应用进行交互

---

## 环境要求

- Python 3.9+
- `pip`
- 可选：Node.js
  仅用于前端脚本检查，不是运行本地聊天应用的硬性要求

---

## 第一步：克隆仓库

```bash
git clone <你的仓库地址>
cd ex-skill-public
```

---

## 第二步：安装依赖

```bash
pip install -r requirements.txt
```

---

## 第三步：配置模型

你可以任选其一：

### 方案 A：环境变量

参考：

- [`config/local_chat.env.example`](config/local_chat.env.example)

### 方案 B：本地配置文件

在仓库中创建：

```text
config/providers.local.json
```

参考模板：

- [`config/providers.local.example.json`](config/providers.local.example.json)

### 接口分工

安装完成后，运行层会按三组接口变量分工：

1. `TEXT_*`
   负责本地聊天页面中的文本回复与表情策略。
2. `ENRICH_*`
   负责 `tools/profile_autofill.py` 的资料补全与结构化提炼。
3. `TTS_*`
   负责本地语音输出与可选声线克隆。

按当前代码默认逻辑：

- 文本聊天优先读取 `SiliconFlow (硅基流动)` 配置
- 资料补全优先读取 `DeepSeek Official` 配置
- 语音输出优先读取 `SiliconFlow (硅基流动)` 配置，并默认走 `siliconflow_clone`

---

## 第四步：准备聊天记录

推荐阅读：

- [`docs/EXPORT_GUIDE.md`](docs/EXPORT_GUIDE.md)
- [`docs/EXPORT_GUIDE_EN.md`](docs/EXPORT_GUIDE_EN.md)

导入链路摘要：

1. 微信可优先整理为 `json / txt / html`
2. QQ 可优先使用官方客户端导出，再整理为可读文本
3. 微信官方 `ChatBackup` 需要先转换为可读内容，再交给本项目

---

## 第五步：构建资料包

### 方案 A：直接构建

```bash
python tools/universal_builder.py \
  --name "你的代号" \
  --slug "your_ex" \
  --target "聊天中的昵称" \
  --chat-source "你的聊天文件.txt"
```

### 方案 B：项目内工作区

先初始化：

```bash
python tools/project_data_builder.py --init --slug your_ex
```

再构建：

```bash
python tools/project_data_builder.py --slug your_ex --name "你的代号" --target "聊天昵称"
```

---

## 第六步：启动本地聊天应用

```bash
uvicorn apps.local_chat.app:app --host 127.0.0.1 --port 7860 --reload
```

浏览器打开：

[http://127.0.0.1:7860](http://127.0.0.1:7860)

---

## 部署依赖说明

### 资料构建依赖

- Python
- `requirements.txt` 中的依赖

### 本地聊天应用依赖

- OpenAI 兼容聊天接口
- 可选 TTS 或语音接口

### 本地私有数据

本地运行层默认从这些位置读取聊天文本、媒体样本与私有配置：

```text
data/
exes/your_ex/
config/providers.local.json
```

公开仓库本身保持代码、模板与说明文档；上述目录中的真实文本、媒体样本与密钥配置不进入公开版本。

---

## 常见问题

### 1. 为什么仓库默认没有聊天样本？

这是一个面向公开发布的工程模板。你需要在本地导入自己的聊天导出，再生成属于自己的资料包。

### 2. 默认示例为什么叫 `example_xiaoming`？

它只是一个结构示例，用于演示目录组织与应用加载方式，不对应任何真实人物。

### 3. 可以只用资料包，不启本地聊天应用吗？

可以。你可以直接将生成后的 `SYSTEM_PROMPT.md`、`AGENT_PROMPT.md` 等交给 Cursor、Codex、Claude Code 或 Gemini CLI 使用。
