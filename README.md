# Auto PPT Engine

<p align="center">
  <a href="https://github.com/lijunliu-gh/auto-ppt-engine/tags"><img src="https://img.shields.io/github/v/tag/lijunliu-gh/auto-ppt-engine?label=release&sort=semver" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://github.com/lijunliu-gh/auto-ppt-engine/actions/workflows/smoke.yml"><img src="https://img.shields.io/github/actions/workflow/status/lijunliu-gh/auto-ppt-engine/smoke.yml?branch=main&label=CI" alt="CI"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/tests-409%20passed-brightgreen" alt="Tests"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/coverage-84%25-green" alt="Coverage"></a>
  <br>
  <a href="requirements.txt"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python"></a>
  <a href="package.json"><img src="https://img.shields.io/badge/node-18%2B-green" alt="Node"></a>
  <a href="Dockerfile"><img src="https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white" alt="Docker"></a>
  <a href="mcp_server.py"><img src="https://img.shields.io/badge/MCP-compatible-8A2BE2" alt="MCP"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
</p>

Open-source PowerPoint generation engine — built to be called by AI agents.

Give your agent (Claude Desktop, Cursor, Windsurf, or any MCP-compatible host) the ability to create and revise `.pptx` decks from natural language. Also works as a standalone CLI for developers.

### Who is this for?

| You are… | How you use it |
|:---|:---|
| **AI agent builder** | Connect via MCP / HTTP / JSON skill — your agent says "make a deck", this engine does the rest |
| **Developer / power user** | Run `./auto-ppt generate` from the terminal, pipe into your workflow |
| **Enterprise team** | Deploy via Docker behind your VPN, let internal agents call it as a tool |

> **Not a SaaS.** Not a GUI. This is an embeddable engine — the backend behind "make me a PPT".

## Quick Start

```bash
# 1. Install
npm install && pip install .

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

### Example Output

```
$ ./auto-ppt generate --mock --prompt "Q1 AI Strategy Review for Leadership"

Action: create
Deck JSON: output/py-generated-deck.json
PPTX:      output/py-generated-deck.pptx
Renderer:  pptxgenjs
Slides:    8
Sources:   1

  1. [title       ] Q1 AI Strategy Review for Leadership
  2. [agenda      ] Agenda
  3. [bullet      ] Background and goals
  4. [two-column  ] Current state and challenges
  5. [process     ] Python smart layer workflow
  6. [timeline    ] Execution timeline
  7. [chart       ] Adoption metrics
  8. [closing     ] Key recommendations
```

The engine produces a validated deck JSON (schema-checked) and a ready-to-open `.pptx` file.

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
| Built-in themes | 6 themes (business-clean, corporate-blue, dark-executive, warm-modern, minimal, tech); `--theme` flag or API param |
| Multi-language | CJK + Latin universal font stack — any language mixed with English |
| Security | Path traversal protection, SSRF blocking, file size limits, subprocess timeout |

## Entry Points

| Interface | Command | Use Case |
|----------|---------|----------|
| **MCP** | `python mcp_server.py` | Claude Desktop, Cursor, Windsurf — **recommended for agent integration** |
| **CLI** | `./auto-ppt generate` / `revise` | Interactive or scripted usage |
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
python -m pytest tests/ -v   # 400+ tests
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
| [Changelog](CHANGELOG.md) | Version history |
| [Roadmap](ROADMAP.md) | Planned evolution |

Multilingual: all guides available in [English](docs/EXAMPLES.en.md), [中文](docs/EXAMPLES.zh-CN.md), [日本語](docs/EXAMPLES.ja.md).

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
