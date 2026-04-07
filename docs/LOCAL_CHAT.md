# 本地聊天应用使用说明

## 适用场景

如果你不满足于“只生成提示词”，而是希望：

1. 在网页里直接聊天
2. 显示本地表情包
3. 在合适时机自动发表情包
4. 根据语音接口生成可播放音频
5. 保留浏览器本地聊天历史

那么可以直接使用：

```text
apps/local_chat/
```

---

## 公开版说明

这个公开版仓库已经移除：

1. 真实聊天记录
2. 真实媒体文件
3. 本地运行缓存
4. 私人资料包
5. 私有 API 配置

仓库中保留了一个脱敏示例资料包：

```text
exes/example_xiaoming/
```

它只用于演示目录结构和应用加载方式，不代表任何真实人物。

---

## 启动前准备

### 1. 配置模型

有两种方式：

1. 直接用环境变量配置
2. 在仓库内新建 `config/providers.local.json`

可参考：

[`config/local_chat.env.example`](../config/local_chat.env.example)

以及：

[`config/providers.local.example.json`](../config/providers.local.example.json)

### 2. 准备你自己的资料包

推荐用这两种方式之一：

1. 先执行：
```bash
python tools/project_data_builder.py --init --slug your_ex
```

2. 或直接执行：
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

## 使用建议

1. 第一次启动时，先把左侧 `slug` 改成你自己的资料包名
2. 如果你只想手动发表情包，把“自动表情包”切到 `关闭`
3. 如果你不想它句句都回，保持“拟真回复节奏”开启
4. 如果你需要公开发布仓库，不要把 `data/` 和你自己的 `exes/{slug}` 提交上去

---

## 注意事项

1. 这个页面保存的是浏览器本地历史，不是服务端数据库
2. 切换浏览器、清空站点缓存后，本地历史会消失
3. 如果你要接入语音克隆，请把本地样本放到 `data/voice_samples/`，不要提交到 GitHub
