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
- 基于 JSON Schema 的结构校验
- 通过 Node renderer 输出 `.pptx`
- 可被 agent 调用的 JSON request/response 流程
- 本地 HTTP skill 接口

## 当前对外入口

推荐使用的主入口：

- `py-generate-from-prompt.py`
- `py-revise-deck.py`
- `py-agent-skill.py`
- `py-skill-server.py`

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
- 更强的主题和模板支持
- 更好的版式质量和字体控制
- 自动化测试
- 面向托管部署的工程化加固

## 建议的开源定位描述

建议 GitHub 简介使用：

> Open-source PowerPoint backend for AI agents using a Python smart layer for planning and a JavaScript renderer for PPTX output.