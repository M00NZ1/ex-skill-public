# 聊天记录存放区

这个目录用于存放你自己的聊天原材料。

推荐初始化方式：

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

公开仓库里不要提交这些真实内容。
