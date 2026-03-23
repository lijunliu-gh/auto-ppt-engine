# Project Status

Current version: **v0.7.7**

Product positioning: **to-B PPT generation engine** — embeddable into enterprise AI workflows with private deployment, API-driven generation (MCP / CLI / HTTP), and multi-language support (CJK + English). Core differentiators are data security (no data leaves the enterprise), content intelligence (AI-driven layout and visualization selection), and cross-platform output (PowerPoint, Keynote, Google Slides).

Current release posture: **published in its current scope**. This repository is being released as a personal open-source project in maintenance mode. No additional roadmap items are currently committed.

---

## Current Capabilities (v0.7.7)

| Area | What's Included |
|------|----------------|
| **Interfaces** | MCP Server (stdio + streamable HTTP), CLI (`auto-ppt generate` / `revise` / `qa-visual`), HTTP skill endpoint, JSON agent workflow |
| **Planning & Revision** | Prompt-to-deck, natural-language revision, source-grounded planning |
| **Source Ingestion** | 12+ formats: PDF, DOCX, HTML, TXT, MD, CSV, JSON, YAML, XML, images, URLs |
| **Rendering** | Dual path: pptxgenjs (JS) or python-pptx (brand template); CJK font stack; image-based charts for cross-platform compatibility |
| **Layouts** | 18+ types including KPI, SWOT, funnel, image-text, process-circular, timeline-vertical |
| **Theming** | 6 built-in themes + custom theme JSON; `--theme` CLI flag; LLM-suggested theme selection |
| **Brand Templates** | Upload `.pptx` → auto-parse → themed output via python-pptx |
| **Image Pipeline** | Local images, URL images, placeholder protocol for multi-agent collaboration |
| **Chart Handling** | Auto-repair, type correction, string-to-number coercion, graceful fallback to bullet layout |
| **Quality** | Visual QA heuristics, quality scorer, 408 tests (84% coverage) |
| **Security** | Path traversal protection, SSRF blocking, file size limits, subprocess timeout, image extension whitelist |
| **LLM Providers** | OpenAI, OpenRouter, Claude, Gemini, Qwen, DeepSeek, GLM, MiniMax, any OpenAI-compatible endpoint |
| **Deployment** | Docker + docker-compose one-command deploy; CI matrix: Python 3.10–3.12 + Node.js 18/20/22 |
| **API** | Versioned (`apiVersion: "1.0"`), stable JSON contract between Python smart layer and JS renderer |

---

## Maintenance Status

This repository is published as a stable personal-project snapshot.

- No additional feature roadmap is currently committed
- Future updates, if any, are expected to be limited to bug fixes, small documentation corrections, or metadata cleanup
- The recommended way to evaluate the project is to use the current CLI, MCP, HTTP, and JSON skill entrypoints as documented

---

## Version History

| Version | Milestone |
|---------|-----------|
| v0.7.7 | Current-scope release alignment; roadmap converted to project status / maintenance posture |
| v0.7.6 | Release metadata audit cleanup and public baseline verification |
| v0.7.5 | README positioning update for personal-project release |
| v0.7.4 | Switch to Apache 2.0 license |
| v0.7.3 | 409 tests, 84% coverage, documentation alignment |
| v0.7.2 | Theme system, 6 built-in themes, new layouts (KPI, SWOT, funnel), brand template adaptation |
| v0.7.1 | Cross-platform rendering: text auto-fit, CJK font stack, chart image mode |
| v0.7.0 | Docker packaging, chart auto-repair, remote MCP (streamable HTTP) |
| v0.6.0 | API versioning, CI matrix, expanded test coverage |
| v0.5.1 | Image asset pipeline, placeholder protocol |
| v0.5.0 | Brand template engine (python-pptx dual render path) |
| v0.4.1 | Chart data reliability, multi-model validation, legacy JS removal |
| v0.4.0 | MCP Server for Claude Desktop, Cursor, Windsurf |
| v0.3.1 | Security hardening, LLM provider abstraction, structured logging |

---

## Contributing

If you are interested in contributing fixes or documentation improvements, see [CONTRIBUTING.md](CONTRIBUTING.md) and open an issue to discuss your approach before starting work.
