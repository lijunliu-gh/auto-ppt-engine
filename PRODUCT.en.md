# Product Summary

## Current Product

Auto PPT Prototype is an open-source PowerPoint backend for AI agents.

Its current architecture is deliberate:

- Python smart layer for planning, revision, source handling, and agent orchestration
- JavaScript render layer for final PPTX generation

## What It Is

It is a planning-and-rendering backend.

It is meant to sit behind an upstream agent that can:

- collect requirements
- ask clarifying questions
- retrieve trusted material
- read uploaded documents
- inspect screenshots or images
- decide what content belongs on each slide

The product boundary is clear:

- the upstream agent owns research and workflow control
- this repository owns deck planning, revision, validation, and rendering

## What It Is Not

It is not a complete research agent by itself.

It should not be described as a simple web-search-to-slide generator.

For serious use cases, the system should rely on:

1. official sources
2. user-uploaded source material
3. explicit user instructions
4. web search only as a fallback

## Current Capabilities

- deck planning from prompts
- deck revision from natural-language instructions
- trusted source ingestion from files and URLs
- chart data validation with automatic fallback to bullet layout
- chart auto-repair: invalid type correction, string-to-number coercion, data/category length alignment before fallback
- numerical data extraction from sources for chart hints
- deck JSON validation
- PPTX rendering through the Node renderer
- Brand template engine: pass a .pptx template for brand-matched output via python-pptx
- Dual render path: python-pptx (with template) or pptxgenjs (without template)
- MCP Server for Claude Desktop, Cursor, and Windsurf (`create_deck`, `revise_deck`)
- MCP remote transport: streamable HTTP mode for hosted deployments (`--transport streamable-http`)
- agent-callable JSON request and response flow
- local HTTP skill endpoint
- LLM provider abstraction (OpenAI, OpenRouter, Claude, Gemini, Qwen, DeepSeek, GLM, MiniMax)
- image asset pipeline: local image insertion, URL images, placeholder protocol for multi-agent collaboration
- security: path traversal prevention, SSRF blocking, file size limits, subprocess timeout, image extension whitelist
- 263 automated tests (84% coverage: unit, MCP server, MCP integration, template engine, image handler, cross-module)
- API versioning (`apiVersion: "1.0"`) in all requests and responses
- CI matrix: pytest on Python 3.10/3.11/3.12 + Node.js 18/20/22 smoke tests
- Docker packaging: Dockerfile + docker-compose.yml for one-command containerized deployment

## Public Entry Points

Preferred entry points:

- `mcp_server.py` (MCP — recommended for Claude Desktop, Cursor, Windsurf)
- `py-generate-from-prompt.py` (CLI)
- `py-revise-deck.py` (CLI)
- `py-agent-skill.py` (JSON skill)
- `py-skill-server.py` (HTTP service)

Compatibility entry points retained for older integrations:

- `generate-from-prompt.js`
- `revise-deck.js`
- `agent-skill.js`
- `skill-server.js`

These Node entrypoints now forward to the Python smart layer.

## Why This Direction Makes Sense

Python is the right home for the next phase of the product:

- stronger document parsing
- model routing and orchestration
- retrieval and source reasoning
- OCR and multimodal expansion
- more advanced revision quality

JavaScript remains in the project because the renderer already works and should stay stable.

## Production Gaps

- richer spreadsheet and tabular source handling
- true image and screenshot understanding
- finer-grained provenance tracking
- better layout quality and typography control
- hosted deployment hardening

## Recommended Open-Source Framing

Recommended GitHub description:

> AI-agent-ready PowerPoint backend: plan, revise, and render PPTX decks from natural-language prompts. MCP + CLI + HTTP interfaces.
