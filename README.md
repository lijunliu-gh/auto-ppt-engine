# Auto PPT

[![Release](https://img.shields.io/github/v/tag/lijunliu-gh/auto-ppt-engine?label=release&sort=semver)](https://github.com/lijunliu-gh/auto-ppt-engine/tags)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/lijunliu-gh/auto-ppt-engine/smoke.yml?branch=main&label=CI)](https://github.com/lijunliu-gh/auto-ppt-engine/actions/workflows/smoke.yml)

Open-source PowerPoint generation engine for AI agents.
Give it a prompt, optional source files, and an LLM key — get back a validated `.pptx`.

## Quick Start

```bash
# 1. Install
npm install && python -m pip install -r requirements.txt

# 2. Configure (writes .env with your LLM key)
./auto-ppt init

# 3. Generate — mock mode, no LLM key needed
./auto-ppt generate --mock \
  --prompt "Create an 8-slide AI strategy deck for executives" \
  --source examples/inputs/sample-source-brief.md

# 4. Generate — real model, after init
./auto-ppt generate \
  --prompt "Create an 8-slide AI strategy deck for executives" \
  --source examples/inputs/sample-source-brief.md

# 5. Revise
./auto-ppt revise \
  --deck output/py-generated-deck.json \
  --prompt "Compress to 6 slides, make it more conclusion-driven"

# 6. Visual QA (heuristics + optional slide image export)
./auto-ppt qa-visual output/py-generated-deck.pptx --strict
```

Output: `output/py-generated-deck.json` + `.pptx`, `output/py-revised-deck.json` + `.pptx`.

`qa-visual` writes a JSON report (default: alongside PPTX in `<deck-name>-qa/visual-qa-report.json`) and attempts to export slide images when `soffice` and `pdftoppm` are available.

## What It Does

| Capability | Detail |
|-----------|--------|
| Prompt-to-deck planning | Natural-language prompt → structured slide deck |
| Natural-language revision | Iterate on an existing deck with free-text instructions |
| Source ingestion | `.txt` `.md` `.csv` `.json` `.yaml` `.xml` `.html` `.pdf` `.docx`, images, URLs |
| Schema validation | JSON-schema check before every render |
| LLM providers | OpenAI, OpenRouter, Claude, Gemini, Qwen, DeepSeek, GLM, MiniMax, any OpenAI-compatible endpoint |
| PPTX rendering | JS renderer (pptxgenjs) with CJK font support and chart image fallback for Keynote/Google Slides |
| Cross-platform charts | Image-based charts by default; native OOXML via `--native-charts` |
| Multi-language | CJK + Latin universal font stack — any language mixed with English |
| Security | Path traversal protection, SSRF blocking, file size limits, subprocess timeout |

## Entry Points

| Interface | Command | Use Case |
|----------|---------|----------|
| **CLI** | `./auto-ppt generate` / `revise` | Interactive or scripted usage |
| **MCP** | `python mcp_server.py` | Claude Desktop, Cursor, Windsurf |
| **HTTP** | `python py-skill-server.py` | REST integration (`POST /skill`) |
| **JSON skill** | `python py-agent-skill.py --request req.json` | File-based agent orchestration |
| **Docker** | `docker compose up --build` | One-command deploy |

## MCP Configuration

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "auto-ppt": {
      "command": "python",
      "args": ["/absolute/path/to/auto-ppt-engine/mcp_server.py"]
    }
  }
}
```

**Cursor / Windsurf** — add to `.cursor/mcp.json` or `.windsurf/mcp.json`:

```json
{
  "mcpServers": {
    "auto-ppt": {
      "command": "python",
      "args": ["/absolute/path/to/auto-ppt-engine/mcp_server.py"]
    }
  }
}
```

Tools exposed: `create_deck`, `revise_deck`. Both accept `sources`, `mock` mode, and optional `output_dir`.

## Docker

```bash
export OPENAI_API_KEY="sk-..."
docker compose up --build                          # HTTP skill server
docker run --rm -it -e OPENAI_API_KEY auto-ppt-engine python mcp_server.py  # MCP stdio
```

## Testing

```bash
python -m pytest tests/ -v   # 300+ tests
npm run ci:smoke             # JS renderer + end-to-end smoke
```

CI: pytest on Python 3.10 / 3.11 / 3.12, smoke on Node.js 18 / 20 / 22.

## Architecture

```
prompt + sources ➜ Python smart layer ➜ deck JSON ➜ PPTX renderer ➜ .pptx
                        ↑ revise loop ↲
```

- **Python** (`python_backend/`): planning, revision, source loading, LLM calls, schema validation
- **Node** (`generate-ppt.js`): pptxgenjs rendering from validated deck JSON, cross-platform chart images, CJK font stack
- **deck JSON**: the stable contract between both layers

## Documentation

| Doc | Content |
|-----|---------|
| [Examples](docs/EXAMPLES.en.md) | Copy-paste usage flows |
| [User Guide](docs/USER_GUIDE.en.md) | Day-to-day usage |
| [Integration Guide](docs/INTEGRATION_GUIDE.en.md) | HTTP, MCP, JSON skill patterns |
| [Product Overview](docs/PRODUCT.en.md) | Positioning and boundaries |
| [Repository Map](docs/REPOSITORY_MAP.md) | File-by-file structure |
| [Changelog](CHANGELOG.md) | Version history |
| [Roadmap](ROADMAP.md) | Planned evolution |

Multilingual: all guides available in [English](docs/EXAMPLES.en.md), [中文](docs/EXAMPLES.zh-CN.md), [日本語](docs/EXAMPLES.ja.md).

## License

MIT
