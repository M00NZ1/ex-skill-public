# 聊天记录导入指南

[中文](EXPORT_GUIDE.md) | [English](EXPORT_GUIDE_EN.md)

本项目需要的是**可读聊天记录**，而不是加密数据库本体。

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

它适合作为微信聊天记录的导出前置工具，先将本地数据整理为可读格式，再继续接入本项目的资料构建流程。

### WeFlow 导出后怎么接入

如果已经用 WeFlow 导出了聊天记录，可直接把这些结果用于本项目：

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

QQ 记录推荐优先使用官方客户端导出，或整理为 `txt` 后再接入本项目。

示例：

```text
我：在干嘛
ta：刚下班
我：晚上吃了吗
ta：还没
```

只要文本中能够区分双方说话内容，本项目就可以继续分析和构建资料包。

---

## 微信官方 ChatBackup 为什么不能直接用

如果拿到的是这种目录：

- `.wechat-deviceId`
- `backup.attr`
- `files/`
- 大量 `.enc / .dat`

说明你拿到的是微信官方迁移备份，而不是可直接解析的聊天文本。

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

这个工具只做只读清点，不会伪造聊天正文。

---

## 手工整理也完全可用

如果你没有任何导出工具，也可以直接准备：

```text
我：今天下班了吗
ta：刚到家
我：累不累
ta：累死了
```

对角色构建来说，可读、可区分双方说话内容，比原始数据库更重要。

---

## 最佳实践

优先提供这些内容：

1. 深夜聊天
2. 吵架或冲突记录
3. 分手前后对话
4. 日常闲聊
5. 语音转写
6. 高频表情包

这些内容通常最能提升角色还原度。
