# 安装与部署说明

## 适用范围

这个公开版支持两种主要使用方式：

1. 只把它当成资料构建工具
2. 同时启动本地网页聊天应用

---

## 环境要求

- Python 3.9+
- `pip`
- 可选：Node.js
  用于前端脚本检查，不是运行本地聊天应用的硬性要求

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

在仓库里新建：

```text
config/providers.local.json
```

参考模板：

- [`config/providers.local.example.json`](config/providers.local.example.json)

这个文件已经被 `.gitignore` 忽略，不会默认提交到 GitHub。

---

## 第四步：准备聊天记录

推荐阅读：

- [`docs/EXPORT_GUIDE.md`](docs/EXPORT_GUIDE.md)

简要结论：

1. 微信推荐使用 [WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file) 导出可读格式
2. QQ 推荐使用官方客户端导出，或手工复制整理为 `txt`
3. 微信官方 `ChatBackup` 不能直接喂给本项目

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
- 可选 TTS/语音接口

### 语音克隆依赖

公开版只保留接口接入能力，不内置真实样本。  
如果你要接入自己的声线样本，请把文件放到：

```text
data/voice_samples/
```

不要提交到 GitHub。

---

## 常见问题

### 1. 公开版为什么没有真实聊天记录？

因为公开版是给 GitHub 使用的，真实聊天记录、媒体和缓存都已经移除。

### 2. 默认示例为什么叫 `example_xiaoming`？

这是一个脱敏演示资料包，只为了保证仓库开箱可读，不代表任何真实人物。

### 3. 我可以只用资料包，不启本地聊天应用吗？

可以。你只需要把生成后的 `SYSTEM_PROMPT.md`、`AGENT_PROMPT.md` 等交给 Cursor、Codex、Claude Code 或 Gemini CLI 使用即可。
