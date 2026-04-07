# 工具脚本目录

此目录存放聊天记录解析、资料包构建、版本备份与辅助分析脚本。
仓库展示层默认以中文文档为主，英文文档仅作补充入口。

主要脚本包括：

- `universal_builder.py`：通用资料包构建器
- `project_data_builder.py`：项目内工作区构建器
- `wechat_parser.py`：微信聊天记录解析
- `qq_parser.py`：QQ 聊天记录解析
- `chatbackup_inventory.py`：微信官方备份只读清点
- `skill_writer.py`：资料包合并与输出

如果你想扩展导入流程或增加新的数据源，通常从这里开始。
