# 使用说明（中文版）

这份文档面向使用者，而不是开发者。

如果你想知道这个项目现在怎么用、适合什么场景，以及应该优先调用哪些入口，看这份就够了。

## 这是什么

这是一个可被 AI Agent 调用的 PPT 生成后端原型。

它现在最好被理解成两层：

- Python 智能层：负责 planning、revise、source ingestion 和 agent orchestration
- JavaScript 渲染层：负责把 deck JSON 输出为 `.pptx`

也就是：

`需求 + 资料 -> Python planning -> deck JSON -> Node rendering -> PPTX`

## 适合什么场景

现在比较适合这些场景：

- 产品规划汇报
- 管理层汇报
- 销售方案 deck
- 项目复盘 deck
- 培训课件初稿
- 基于官网资料、PDF、DOCX、Markdown 生成演示文稿
- 先生成一版，再反复修订优化

## 默认应该怎么用

**如果你用 Claude Desktop、Cursor 或 Windsurf**，推荐用 MCP 接入，配好之后直接在对话里让它生成 deck。

如果不用 MCP，优先使用 Python 入口：

```bash
npm run generate:source
npm run skill:create
npm run revise:mock
npm run skill:server
```

这些 npm 脚本现在默认都会走 Python 智能层。

## 现在能做什么

### 1. 从现成 JSON 直接生成 PPT

适合你已经有结构化 deck 数据的情况。

```bash
npm run generate
```

### 2. 从自然语言生成 PPT

适合你只有一个大致需求描述的情况。

```bash
npm run generate:mock
```

如果你已经配置了模型，也可以用：

```bash
npm run generate:prompt
```

直接用 Python 的命令示例：

```bash
python py-generate-from-prompt.py --prompt "Create an 8-slide AI product strategy deck for executives in a professional tone"
```

### 3. 带资料来源一起生成 PPT

这是现在更推荐的方式。

```bash
npm run generate:source
```

也可以自己传资料：

```bash
python py-generate-from-prompt.py --mock --prompt "Create an 8-slide strategy deck" --source your-brief.md --source https://example.com/product
```

### 4. 修订已有 deck

适合你已经生成了一版 PPT，接下来想继续优化。

比如你可以要求它：

- 压缩页数
- 更结论导向
- 强调执行计划
- 调整结构
- 让内容更适合管理层汇报

```bash
npm run revise:mock
```

### 5. 作为 skill 被其他 agent 调用

适合你把这个项目接进别的 agent 流程。

```bash
npm run skill:create
npm run skill:revise
```

### 6. 作为 HTTP 服务使用

适合你希望通过本地 API 的方式调用它。

```bash
npm run skill:server
curl http://localhost:3010/health
curl -X POST http://localhost:3010/skill -H "Content-Type: application/json" --data @sample-http-request.json
```

### 7. 通过 MCP 使用（Claude Desktop、Cursor、Windsurf）

这是 AI 原生工作流的推荐接入方式。

在你的 MCP 客户端配置中添加：

```json
{
  "mcpServers": {
    "auto-ppt": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/auto-ppt-prototype"
    }
  }
}
```

然后直接让 AI 助手帮你创建或修订 deck。MCP 服务暴露 `create_deck` 和 `revise_deck` 两个 tool。

远程部署时，MCP 服务器也支持 Streamable HTTP 传输：

```bash
python mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8080
```

### 8. Docker

```bash
# 一键启动 HTTP skill 服务
docker compose up --build

# 或以远程传输模式运行 MCP 服务器
docker run --rm -p 8080:8080 -e OPENAI_API_KEY auto-ppt-prototype \
  python mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8080
```

## 资料来源现在怎么处理

当前支持的来源包括：

- 本地文本文件：`txt`、`md`、`csv`、`json`、`yaml`、`xml`
- 本地 HTML
- 本地 PDF
- 本地 DOCX
- 图片文件引用
- HTTP / HTTPS URL

默认情况下：

- slide 页面正文不显示来源
- presenter notes 里显示来源
- 每一页的来源也会保存在结构化元数据里

## 最推荐的使用方式

如果你想做相对严谨的 PPT，不建议只给一句 prompt。

更推荐的流程是：

1. 明确这次 PPT 的目标
2. 提供资料来源
3. 先生成一版
4. 再做 1 到 3 轮 revise

## 最容易上手的 3 个命令

```bash
npm run generate:source
npm run skill:create
npm run revise:mock
```

## 主要文件是干什么的

### 面向使用者最相关的文件

- `README.md`
- `PRODUCT.en.md`
- `sample-input.json`
- `sample-source-brief.md`
- `sample-agent-request.json`
- `sample-agent-revise-request.json`
- `sample-http-request.json`

### 主要执行文件

- `py-generate-from-prompt.py`
- `py-revise-deck.py`
- `py-agent-skill.py`
- `py-skill-server.py`
- `generate-ppt.js`

### 兼容入口

- `generate-from-prompt.js`
- `revise-deck.js`
- `agent-skill.js`
- `skill-server.js`

## 图表数据处理

当 slide 使用 `chart` 布局时，系统会自动验证图表数据：

- 图表必须有非空的 categories 和含数值数据的 series
- 如果图表数据无效，slide 会自动降级为 bullet 布局
- 系统会扫描资料来源中的数值数据（百分比、金额、指标），并作为图表提示注入 LLM

## 图片和视觉元素支持

v0.5.1 起，每个 slide 的 `visuals` 数组支持三种类型的元素：

- **纯字符串**: 文字描述或建议（例如 `"添加市场背景图表"`）
- **图片对象**: `{"type": "image", "path": "assets/logo.png"}` 或 `{"type": "image", "url": "https://..."}` — 渲染器会插入实际图片
- **占位符对象**: `{"type": "placeholder", "prompt": "工作流程图"}` — 渲染为带标签的框，用于后续图片生成

每个视觉元素支持 `position` 字段：`right`（默认）、`left`、`center`、`full`。

图片安全控制：

- 本地路径必须在项目目录内（路径穿越防护）
- URL 图片拒绝私有/内部网络（SSRF 保护）
- 最大图片大小：10 MB
- 仅接受常见图片格式：PNG、JPG、GIF、BMP、TIFF、SVG、WebP

## 现在还不够强的地方

这个项目已经能跑通完整原型链路，但还不是生产级成品。

当前还不够强的地方包括：

- 不是完整 research agent
- 图片 OCR 和多模态理解还没有真正做完
- slide 级来源绑定还不够精细
- 真正复杂场景下仍然依赖上游模型和 agent 质量

## API 版本控制

v0.6.0 起，所有 API 请求和响应都包含 `apiVersion: "1.0"` 字段。此字段确保 API 演进时的向后兼容性。制作自定义集成请求时，请在 JSON 中包含 `"apiVersion": "1.0"`。

## 一句话总结

现在这个项目已经可以完成：

- `prompt -> deck -> pptx`
- `prompt + sources -> deck -> pptx`
- `existing deck + revise prompt -> revised deck -> pptx`
- `MCP tool call -> deck + pptx`
- `agent request -> skill response`
- `HTTP request -> generated PPT artifacts`

如果你接下来是想真正拿它做产品，最合理的方向是继续强化：

- 资料理解
- 来源追踪
- revise 质量
- 模型接入
