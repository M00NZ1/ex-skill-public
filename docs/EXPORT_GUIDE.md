# 聊天记录导入指南

本项目需要的是**可读聊天记录**，不是加密数据库本体。

推荐优先准备这些格式：

- `txt`
- `json`
- `html`
- 手工整理的纯文本

---

## 微信聊天记录怎么准备

### 推荐方案：WeFlow

对于微信，推荐优先使用：

- [hicccc77/WeFlow](https://github.com/hicccc77/WeFlow?tab=readme-ov-file)

根据其官方 README，WeFlow 是一个**完全本地的微信聊天记录查看、分析与导出工具**，支持将聊天记录导出成多种可读格式，还提供本地 HTTP API。

这非常适合本项目，因为本项目需要的是：

1. 可读的聊天内容
2. 尽量结构化的导出结果
3. 能进一步整理为 `memory.md / persona.md` 的原材料

### WeFlow 导出后怎么接入

如果你已经用 WeFlow 导出聊天记录，可以直接把这些结果用于本项目：

- `json`
- `txt`
- `html`

然后执行：

```bash
python tools/universal_builder.py \
  --name "你的代号" \
  --slug "your_ex" \
  --target "聊天昵称" \
  --chat-source "导出的聊天文件"
```

如果还有媒体目录，也建议一起传入：

```bash
python tools/universal_builder.py \
  --name "你的代号" \
  --slug "your_ex" \
  --target "聊天昵称" \
  --chat-source "导出的聊天文件" \
  --voice-transcripts "Voices/transcripts.json" \
  --images-dir "images" \
  --emojis-dir "emojis" \
  --videos-dir "videos"
```

---

## QQ 聊天记录怎么准备

这里要明确一点：

1. WeFlow 官方说明写的是**微信**聊天记录工具
2. 它的 README 没有把自己定义成 QQ 导出工具
3. 所以本项目文档不会把 WeFlow 写成 QQ 提取方案

如果你要导入 QQ，推荐这两条路径：

### 方案一：QQ 官方导出

使用 QQ 客户端的聊天记录导出能力，导出为可读文本后再交给本项目。

### 方案二：手工复制整理

把关键对话复制到 `txt` 中，例如：

```text
我：在干嘛
ta：刚下班
我：晚上吃了吗
ta：还没
```

---

## 微信官方 ChatBackup 为什么不能直接用

如果你拿到的是这种目录：

- `.wechat-deviceId`
- `backup.attr`
- `files/`
- 大量 `.enc / .dat`

那说明你拿到的是**微信官方迁移备份**，不是可直接解析的聊天文本。

结论很直接：

1. 不能直接喂给 `tools/wechat_parser.py`
2. 不能直接期待它变成聊天正文
3. 应该先转换为 `txt / json / html`

如果你只是想先清点备份里有哪些元信息，可以执行：

```bash
python tools/chatbackup_inventory.py \
  --backup-dir "data/ChatBackup" \
  --output-dir "data/processed/chatbackup_inventory"
```

这个工具只做只读清点，不会伪造正文。

---

## 手工整理也完全可用

如果你没有任何导出工具，也可以直接准备：

```text
我：今天下班了吗
ta：刚到家
我：累不累
ta：累死了
```

本项目并不强制要求一定要数据库级导出。  
对角色构建来说，可读、可区分双方说话内容，比“原始数据库”更重要。

---

## 最佳实践

优先提供这些内容：

1. 深夜聊天
2. 吵架/冲突记录
3. 分手前后对话
4. 日常闲聊
5. 语音转写
6. 高频表情包

这些内容通常最能提升角色还原度。
