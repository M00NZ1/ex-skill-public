# 示例资料包执行说明

请把当前目录视为一个**脱敏演示资料包**。

你的任务不是扮演某个真实人物，而是理解这个项目的资料结构：

1. `meta.json`：基础资料
2. `memory.md`：关系记忆
3. `persona.md`：人物性格
4. `SYSTEM_PROMPT.md`：通用系统提示词
5. `SKILL.md`：Skill 形式的组合产物

如果用户准备了新的聊天记录，请引导他重新执行：

```bash
python tools/universal_builder.py --help
```

或：

```bash
python tools/project_data_builder.py --init --slug your_ex
```
