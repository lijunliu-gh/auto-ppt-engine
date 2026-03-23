# Roadmap

Current version: **v0.7.4**

Product positioning: **to-B PPT generation engine** — embeddable into enterprise AI workflows with private deployment, API-driven generation (MCP / CLI / HTTP), and multi-language support (CJK + English). Core differentiators are data security (no data leaves the enterprise), content intelligence (AI-driven layout and visualization selection), and cross-platform output (PowerPoint, Keynote, Google Slides).

---

## Current Capabilities (v0.7.4)

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
| **Quality** | Visual QA heuristics, quality scorer, 409 tests (84% coverage) |
| **Security** | Path traversal protection, SSRF blocking, file size limits, subprocess timeout, image extension whitelist |
| **LLM Providers** | OpenAI, OpenRouter, Claude, Gemini, Qwen, DeepSeek, GLM, MiniMax, any OpenAI-compatible endpoint |
| **Deployment** | Docker + docker-compose one-command deploy; CI matrix: Python 3.10–3.12 + Node.js 18/20/22 |
| **API** | Versioned (`apiVersion: "1.0"`), stable JSON contract between Python smart layer and JS renderer |

---

## What's Next

### Packaging and Distribution

**Goal**: Reduce installation friction so users can run the tool without understanding the Python + Node implementation split.

- Publish a clean install path (`pipx`, `uvx`, or similar)
- Bootstrap assets: `.env.example`, provider presets, install-time validation
- Docker as the zero-dependency fallback
- Improved default output location, naming, and success messages

### Minimal End-User UI → v1.0.0

**Goal**: Expose the generate/revise loop to non-command-line users through a minimal interface.

- Prompt input, source upload, optional audience/page controls, PPTX download
- Job status feedback with progress and artifact locations
- Template and source upload flows
- Reuse the same CLI core interfaces — no forked product logic

---

## Version History

| Version | Milestone |
|---------|-----------|
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

If you are interested in contributing to any of these areas, see [CONTRIBUTING.md](CONTRIBUTING.md) and open an issue to discuss your approach before starting work.
