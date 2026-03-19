# 接入说明（中文版）

这份文档面向接入方。

如果你想把这个项目接入自己的 AI Agent、工作流系统、脚本、后端服务或者本地工具链，重点看这里。

## 这个项目在接入链路里的角色

这个项目现在更适合被描述成：

- Python-first 的 PPT generation backend
- deck planning and rendering engine
- local skill service
- agent-callable PPT workflow

它不负责完整的 research agent 能力，而是负责把上游提供的输入转成：

- deck JSON
- `.pptx`

推荐接入模型是：

1. 上游 agent 负责收集需求和资料
2. 上游 agent 调用 Python 智能层
3. 这个项目输出 deck JSON 和 PPTX
4. 上游 agent 根据用户反馈再次调用 revise 流程

## 当前支持的接入方式

## 1. MCP 接入（推荐用于 AI 环境）

如果你使用 Claude Desktop、Cursor、Windsurf 或其他 MCP 兼容客户端，MCP 是最简单的接入方式。MCP 服务器将 `create_deck` 和 `revise_deck` 暴露为原生 MCP 工具，AI 助手可以直接调用，无需管理文件或搭建 HTTP 服务。

### Claude Desktop 配置

添加到 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）或 `%APPDATA%\Claude\claude_desktop_config.json`（Windows）：

```json
{
  "mcpServers": {
    "auto-ppt": {
      "command": "python",
      "args": ["/absolute/path/to/auto-ppt-prototype/mcp_server.py"]
    }
  }
}
```

### Cursor / Windsurf 配置

在项目根目录创建 `.cursor/mcp.json` 或 `.windsurf/mcp.json`：

```json
{
  "mcpServers": {
    "auto-ppt": {
      "command": "python",
      "args": ["/absolute/path/to/auto-ppt-prototype/mcp_server.py"]
    }
  }
}
```

### 可用 MCP 工具

| 工具 | 参数 | 描述 |
|------|------|------|
| `create_deck` | `prompt`（必填）、`sources`、`mock`、`research`、`output_dir` | 创建新的演示文稿 |
| `revise_deck` | `prompt`（必填）、`deck_path`（必填）、`sources`、`mock`、`research`、`output_dir` | 修订现有演示文稿 |

## 2. CLI 接入

这是最简单的接入方式，适合：

- Claude Code 类工具
- 本地自动化脚本
- shell / PowerShell 工作流
- CI 中的命令调用

### Create

```bash
python py-generate-from-prompt.py --prompt "Create an 8-slide product strategy deck"
```

### Create with sources

```bash
python py-generate-from-prompt.py --mock --prompt "Create an 8-slide product strategy deck" --source sample-source-brief.md
```

### Revise

```bash
python py-revise-deck.py --deck output/py-generated-deck.json --prompt "Compress this deck to 6 slides"
```

### Agent skill request mode

```bash
python py-agent-skill.py --request sample-agent-request.json --response output/py-agent-response.json
```

## 3. JSON skill 接入

这是当前最适合 agent 的接入方式之一。

你的 agent 只需要：

1. 写一个 request JSON
2. 调用 `py-agent-skill.py`
3. 读取 response JSON

### Create 请求格式

```json
{
  "action": "create",
  "prompt": "Create an 8-slide AI agent product strategy deck for executives in a professional tone",
  "mock": true,
  "research": false,
  "engine": "python-smart-layer",
  "contextFiles": [],
  "sources": [
    {
      "path": "sample-source-brief.md",
      "type": "text",
      "label": "Sample product brief",
      "trustLevel": "user-provided",
      "priority": "high"
    }
  ],
  "outputJson": "output/py-agent-generated-deck.json",
  "outputPptx": "output/py-agent-generated-deck.pptx"
}
```

### Revise 请求格式

```json
{
  "action": "revise",
  "prompt": "Compress this deck, make it more conclusion-driven, and emphasize the execution plan",
  "mock": true,
  "research": false,
  "engine": "python-smart-layer",
  "deckPath": "output/py-generated-deck.json",
  "contextFiles": [],
  "sources": [
    {
      "path": "sample-source-brief.md",
      "type": "text",
      "label": "Sample product brief",
      "trustLevel": "user-provided",
      "priority": "high"
    }
  ],
  "outputJson": "output/py-agent-revised-deck.json",
  "outputPptx": "output/py-agent-revised-deck.pptx"
}
```

### 调用命令

```bash
python py-agent-skill.py --request sample-agent-request.json --response output/py-agent-response.json
```

### 响应格式

```json
{
  "ok": true,
  "engine": "python-smart-layer",
  "action": "create",
  "prompt": "string",
  "deckJsonPath": "absolute path",
  "pptxPath": "absolute path",
  "slideCount": 8,
  "assumptions": [],
  "sourcesUsed": []
}
```

## 4. HTTP 接入

如果你的上游系统更适合通过 API 调用，这个项目也支持本地 HTTP 服务。

### 启动服务

```bash
npm run skill:server
```

### 健康检查

```bash
curl http://localhost:3010/health
```

### 调用 skill

```bash
curl -X POST http://localhost:3010/skill -H "Content-Type: application/json" --data @sample-http-request.json
```

### HTTP 路由

- `GET /health`
- `POST /skill`

## 输入项说明

## 1. `prompt`

作用：

- 定义这次演示文稿的目标
- 说明目标受众、风格、页数、用途

## 2. `contextFiles`

作用：

- 提供额外上下文材料

## 3. `sources`

作用：

- 提供可信资料来源
- 在 planning 前先转换成上下文
- 保留 slide 级来源元数据
- 默认导出到 presenter notes

支持的来源类型：

- text
- json
- html
- pdf
- docx
- image
- url

建议来源优先级：

1. 用户上传材料
2. 官方网址
3. 官方文档
4. 投资者材料
5. 其他外部来源

## 4. `mock`

作用：

- 是否使用本地 mock planner

## 5. `research`

作用：

- 是否启用轻量 research

当前说明：

- 只有配置 Tavily 时才会工作
- 更适合演示，不适合作为严谨事实来源的最终方案

## deck 输出里现在有什么

生成后的 deck JSON 现在包含：

- `sourceDisplayMode`
- `slides[].sources`
- `slides[].speakerNotes`

默认行为：

- `sourceDisplayMode = notes`

这表示：

- 来源不出现在 slide 页面正文
- 来源出现在 presenter notes
- 来源同时保留在结构化元数据里

## 你接入时最推荐的模式

如果你是做 AI Agent 集成，我建议优先使用这条链路：

1. agent 收集用户目标
2. agent 收集资料来源
3. agent 组织成 request JSON
4. 调 `py-agent-skill.py`
5. 读取 response JSON
6. 把生成结果回给用户
7. 如需优化，再走 revise

也就是说，你最好把它当作一个：

- 本地 skill
- 本地 deck backend
- agent tool

## 不同接入方的建议

## 对 Claude Code / Coding Agent 类工具

最推荐：

- CLI 调用
- 或 JSON request + `py-agent-skill.py`

## 对服务化系统

最推荐：

- HTTP 调用

## 对本地自动化脚本

最推荐：

- CLI 模式

## 当前边界和注意事项

## 1. 它不是完整 research agent

不要指望它自己完成官网发现、多源比对、证据冲突处理或多模态分析。

这些应由上游 agent 完成。

## 兼容说明

`generate-from-prompt.js`、`revise-deck.js`、`agent-skill.js`、`skill-server.js` 仍然保留，用于兼容旧接入，但现在它们会转发到 Python 智能层。新接入应把 Python 入口视为主入口。

## 2. 图片目前只是“引用”，不是完整视觉理解

图片会进入来源链路，但当前项目本身不会做真正 OCR 或图像推理。

## 3. slide 级来源已存在，但还不够细

当前已经有：

- `slides[].sources`

但还没细到：

- 哪一个 bullet 对应哪一个 source fragment
- 哪个 chart 点位来自哪段数据

## 4. 版式和品牌控制仍然是原型级

如果你要企业级模板控制，还要继续做。

## 5. 图表数据验证与降级

v0.4.1 起，系统会自动验证图表 slide：

- 图表必须有非空的 `categories` 和含数值的 `series` 数据
- 无效图表会自动降级为 `bullet` 布局，原始内容保留
- 系统会扫描资料来源中的数值数据（百分比、金额、指标）作为图表提示注入 LLM
- 降级决策会记录在 deck 的 `assumptions` 字段中

## 关键文件

- `mcp_server.py`: MCP 服务入口（Claude Desktop、Cursor、Windsurf）
- `py-agent-skill.py`: JSON skill 接入入口
- `py-skill-server.py`: HTTP 服务入口
- `skill-manifest.json`: skill 契约说明
- `py-generate-from-prompt.py`: create CLI
- `py-revise-deck.py`: revise CLI
- `python_backend/source_loader.py`: 资料加载层
- `python_backend/smart_layer.py`: 核心规划引擎
- `generate-ppt.js`: PPT 渲染器
- `deck-schema.json`: deck 结构约束

## 一句话接入建议

如果你现在就要接，最稳的路径是：

**如果用 Claude Desktop、Cursor 或 Windsurf：直接用 MCP。否则先用 JSON skill 模式接入，再根据需要升级到 HTTP 模式。**
