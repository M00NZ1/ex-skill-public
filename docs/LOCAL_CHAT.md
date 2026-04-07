# 本地聊天应用使用说明

[中文](LOCAL_CHAT.md) | [English](LOCAL_CHAT_EN.md)

## 适用场景

如果你不满足于“只生成提示词”，而是希望：

1. 在网页里直接聊天
2. 显示并手动发送本地表情包
3. 在合适时机自动发表情包
4. 根据语音接口生成可播放音频
5. 保留浏览器本地聊天历史

那么可以直接使用：

```text
apps/local_chat/
```

---

## 目录说明

仓库内提供了一个示例资料包：

```text
exes/example_xiaoming/
```

它只用于演示目录结构和应用加载方式。页面中的 `slug` 切换到本地资料包后，即可加载真实构建结果。

---

## 启动前准备

### 1. 配置模型

支持两种方式：

1. 使用环境变量
2. 在仓库内创建 `config/providers.local.json`

可参考：

- [`config/local_chat.env.example`](../config/local_chat.env.example)
- [`config/providers.local.example.json`](../config/providers.local.example.json)

### 2. 准备你自己的资料包

推荐用这两种方式之一：

1. 执行：

```bash
python tools/project_data_builder.py --init --slug your_ex
```

2. 或执行：

```bash
python tools/universal_builder.py --help
```

构建完成后，会在 `exes/{slug}/` 下生成资料包。

---

## 启动命令

在仓库根目录执行：

```bash
uvicorn apps.local_chat.app:app --host 127.0.0.1 --port 7860 --reload
```

然后访问：

[http://127.0.0.1:7860](http://127.0.0.1:7860)

---

## 当前能力

1. 读取 `exes/{slug}` 资料包
2. 自动表情包三档切换：`关闭 / 克制 / 贴近原始`
3. 左侧表情包面板点击即发送
4. 浏览器本地保存最近聊天历史，刷新后自动恢复
5. 拟真回复节奏：连续追发消息会先合并，再按资料包里的回复间隔做缩放延迟
6. 可选调用语音接口生成音频

---

## 接口分工

本地聊天应用当前采用三路接口结构：

### 1. 文本聊天接口

- 配置前缀：`TEXT_*`
- 负责内容：回复文本、表情策略、语音发送判定
- 调用入口：[app.py](../apps/local_chat/app.py) -> [llm_client.py](../apps/local_chat/services/llm_client.py)

默认优先级：

1. `SiliconFlow (硅基流动)`
2. `DeepSeek Official`
3. `Volcengine (火山引擎/豆包)`

### 2. 资料补全接口

- 配置前缀：`ENRICH_*`
- 负责内容：资料包自动补全、结构化摘要提取
- 调用入口：[profile_autofill.py](../tools/profile_autofill.py)

默认优先级：

1. `DeepSeek Official`
2. `SiliconFlow (硅基流动)`
3. `Volcengine (火山引擎/豆包)`

### 3. 语音输出接口

- 配置前缀：`TTS_*`
- 负责内容：TTS 输出、自定义声线上传、语音文件生成
- 调用入口：[tts_client.py](../apps/local_chat/services/tts_client.py) 与 [voice_profile_manager.py](../apps/local_chat/services/voice_profile_manager.py)

默认模式：

- `siliconflow_clone`
- 可切换到 `openai_compatible`
- 可切换到 `custom_http`
- 也可设为 `none`

---

## 页面行为

1. 左侧 `slug` 用于切换当前加载的资料包
2. “自动表情包”切到 `关闭` 时，页面只保留手动发表情包
3. “拟真回复节奏”开启时，页面会先合并连续消息，再按资料包节奏延迟回复
4. `data/` 与 `exes/{slug}` 属于本地运行层，公开仓库默认只保留代码与模板结构

---

## 注意事项

1. 页面保存的是浏览器本地历史，不是服务端数据库
2. 切换浏览器、清空站点缓存后，本地历史会消失
3. 语音样本默认从 `data/voice_samples/` 读取；该目录属于本地数据层，不进入公开仓库
