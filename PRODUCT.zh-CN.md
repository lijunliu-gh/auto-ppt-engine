# 产品概览

## 当前产品定位

Auto PPT Prototype 是一个面向 AI Agent 的开源 PowerPoint 后端。

它现在采用明确的双层架构：

- Python 智能层：负责 planning、revise、source handling、model orchestration 和 agent 接入
- JavaScript 渲染层：负责把 deck JSON 稳定输出为 `.pptx`

## 它是什么

它本质上是一个面向 agent 的 planning-and-rendering backend。

更准确地说，它适合放在一个上游 AI Agent 后面，由上游 agent 负责：

- 收集需求
- 追问缺失信息
- 获取可信资料
- 读取用户上传文档
- 查看截图或图片
- 决定每一页应该放什么内容

而这个项目负责：

- 生成或修订 deck JSON
- 校验结构
- 调用 Node renderer 输出 PPTX

## 它不是什么

它本身不是一个完整的 research agent。

它也不应该被描述成“网页搜索直接生成幻灯片”的简单工具。

如果用于相对严肃的场景，系统应优先依赖：

1. 官方来源
2. 用户上传资料
3. 明确的用户指令
4. 网页搜索仅作为兜底

## 当前能力

- 基于 prompt 的 deck planning
- 基于自然语言指令的 deck revise
- 本地文件与 URL 的可信来源 ingestion
- 图表数据验证，无效图表自动降级为 bullet 布局
- 图表自动修复：无效类型纠正、字符串→数值转换、数据/分类长度自动对齐（降级前先尝试修复）
- 从资料来源中提取数值数据作为图表提示
- 基于 JSON Schema 的结构校验
- 通过 Node renderer 输出 `.pptx`
- 品牌模板引擎：传入 .pptx 模板即可生成品牌匹配的输出（基于 python-pptx）
- 双渲染路径：python-pptx（有模板）或 pptxgenjs（无模板）
- MCP Server，支持 Claude Desktop、Cursor、Windsurf（`create_deck`、`revise_deck`）
- MCP 远程传输：Streamable HTTP 模式，支持托管部署（`--transport streamable-http`）
- 可被 agent 调用的 JSON request/response 流程
- 本地 HTTP skill 接口
- LLM 提供者抽象（OpenAI、OpenRouter、Claude、Gemini、Qwen、DeepSeek、GLM、MiniMax）
- 图片资产管线：本地图片插入、URL 图片、多 Agent 协作占位符协议
- 安全防护：路径穿越防护、SSRF 拦截、文件大小限制、子进程超时、图片扩展名白名单
- 263 条自动化测试（84% 覆盖率：单元测试、MCP 服务测试、MCP 集成测试、模板引擎测试、图片处理测试、跨模块测试）
- API 版本控制（`apiVersion: "1.0"`）包含在所有请求和响应中
- CI 矩阵：Python 3.10/3.11/3.12 上的 pytest + Node.js 18/20/22 烟雾测试
- Docker 打包：Dockerfile + docker-compose.yml，一键容器化部署

## 当前对外入口

推荐使用的主入口：

- `mcp_server.py`（MCP — 推荐用于 Claude Desktop、Cursor、Windsurf）
- `py-generate-from-prompt.py`（CLI）
- `py-revise-deck.py`（CLI）
- `py-agent-skill.py`（JSON skill）
- `py-skill-server.py`（HTTP 服务）

仍然保留的兼容入口：

- `generate-from-prompt.js`
- `revise-deck.js`
- `agent-skill.js`
- `skill-server.js`

这些 Node 入口现在会转发到 Python 智能层，不再是主实现。

## 为什么这样拆分

Python 更适合承接下一阶段能力：

- 更强的文档解析
- model routing 和 orchestration
- retrieval 与来源推理
- OCR 与 multimodal 扩展
- 更高级的 revise 能力

JavaScript 继续保留，是因为现有 PPTX renderer 已经可用，而且应该保持稳定。

## 目前仍存在的产品缺口

- 对表格、电子表格和复杂结构化资料的更强 ingestion 能力
- 图片与截图理解
- 更精细的 provenance tracking
- 更好的版式质量和字体控制
- 面向托管部署的工程化加固

## 建议的开源定位描述

建议 GitHub 简介使用：

> AI-agent-ready PowerPoint backend: plan, revise, and render PPTX decks from natural-language prompts. MCP + CLI + HTTP interfaces.