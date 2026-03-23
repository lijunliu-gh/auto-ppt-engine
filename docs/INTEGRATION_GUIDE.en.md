# Integration Guide

This document is written for integrators.

If you want to connect this project to your own AI agent, workflow engine, script, backend service, or local toolchain, focus on this file.

## The Role Of This Project In An Integration Chain

This project is best used as a:

- Python-first PPT generation backend
- deck planning and rendering engine
- local skill service
- agent-callable PPT workflow

It does not replace a full research agent. Instead, it converts upstream inputs into:

- deck JSON
- `.pptx`

The recommended model is:

1. An upstream agent collects the user request and source material.
2. The upstream agent calls the Python smart layer in this project.
3. This project outputs deck JSON and PPTX.
4. Run a visual QA gate on generated PPTX before delivery.
5. The upstream agent calls the revise flow again when the user requests changes.

## Recommended Visual QA Gate

After each `create` or `revise` run, execute:

```bash
./auto-ppt qa-visual output/py-generated-deck.pptx --strict
```

For revised outputs:

```bash
./auto-ppt qa-visual output/py-revised-deck.pptx --strict
```

Why this matters in integration pipelines:

- catches obvious layout risks before human review
- generates a machine-readable report for CI/automation (`visual-qa-report.json`)
- provides a deterministic non-zero exit in `--strict` mode for quality gating

## Supported Integration Modes

## 1. MCP Integration (Recommended for AI environments)

This is the best option for AI-native workflows. The MCP server exposes `create_deck` and `revise_deck` as native tools, so Claude Desktop, Cursor, Windsurf, and any MCP-compatible client can invoke them directly — no file handling, no HTTP setup.

### Setup

Install dependencies:

```bash
npm install && pip install .
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

### Cursor / Windsurf

Add to `.cursor/mcp.json` or `.windsurf/mcp.json` in your project:

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

### Available MCP tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `create_deck` | `prompt` (required), `sources`, `mock`, `research`, `output_dir` | Create a new deck |
| `revise_deck` | `prompt` (required), `deck_path` (required), `sources`, `mock`, `research`, `output_dir` | Revise an existing deck |

Both tools return a JSON string with: `ok`, `action`, `slideCount`, `deckJsonPath`, `pptxPath`, `assumptions`, `sourcesUsed`.

### Why MCP first

- Zero friction: the AI environment calls the tool directly
- No file management: no request/response JSON files to coordinate
- Revision is natural: the AI can chain `create_deck` → review → `revise_deck`
- Works with mock mode for offline testing

### Remote MCP via Streamable HTTP

For hosted or remote deployments, the MCP server supports streamable HTTP transport:

```bash
python mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8080
```

Then configure your MCP client to connect to `http://<server-host>:8080/mcp`.

This is useful when running the server inside Docker, on a cloud VM, or in any environment where stdio is not available.

## 2. CLI Integration

This is the simplest path. It works well for:

- Claude Code style tools
- local automation scripts
- shell or PowerShell workflows
- CI command execution

### Create

```bash
python py-generate-from-prompt.py --prompt "Create an 8-slide product strategy deck"
```

### Create with sources

```bash
python py-generate-from-prompt.py --mock --prompt "Create an 8-slide product strategy deck" --source examples/inputs/sample-source-brief.md
```

### Revise

```bash
python py-revise-deck.py --deck output/py-generated-deck.json --prompt "Compress this deck to 6 slides"
```

### Agent skill request mode

```bash
python py-agent-skill.py --request examples/inputs/sample-agent-request.json --response output/py-agent-response.json
```

## 3. JSON Skill Integration

This is one of the best current options for agent workflows.

Your agent only needs to:

1. write a request JSON file
2. call `py-agent-skill.py`
3. read the response JSON file

### Create request format

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
      "path": "examples/inputs/sample-source-brief.md",
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

### Revise request format

```json
{
  "action": "revise",
  "apiVersion": "1.0",
  "prompt": "Compress this deck, make it more conclusion-driven, and emphasize the execution plan",
  "mock": true,
  "research": false,
  "engine": "python-smart-layer",
  "deckPath": "output/py-generated-deck.json",
  "contextFiles": [],
  "sources": [
    {
      "path": "examples/inputs/sample-source-brief.md",
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

### Invocation

```bash
python py-agent-skill.py --request examples/inputs/sample-agent-request.json --response output/py-agent-response.json
```

### Response format

```json
{
  "ok": true,
  "apiVersion": "1.0",
  "action": "create",
  "prompt": "string",
  "deckJsonPath": "absolute path",
  "pptxPath": "absolute path",
  "slideCount": 8,
  "assumptions": [],
  "sourcesUsed": []
}
```

## 4. HTTP Integration

If your upstream system prefers API calls, this project also supports a local HTTP service.

### Start the service

```bash
npm run skill:server
```

### Health check

```bash
curl http://localhost:3010/health
```

### Call the skill

```bash
curl -X POST http://localhost:3010/skill -H "Content-Type: application/json" --data @examples/inputs/sample-http-request.json
```

### Example HTTP request body

```json
{
  "action": "create",
  "apiVersion": "1.0",
  "prompt": "Create an 8-slide AI agent product strategy deck for executives in a professional tone",
  "mock": true,
  "research": false,
  "contextFiles": [],
  "sources": [
    {
      "path": "examples/inputs/sample-source-brief.md",
      "type": "text",
      "label": "Sample product brief",
      "trustLevel": "user-provided",
      "priority": "high"
    }
  ]
}
```

### HTTP routes

- `GET /health`
- `POST /skill`

## Input Fields

## 1. `prompt`

Purpose:

- define the presentation goal
- describe the target audience, tone, slide count, and purpose

Recommended prompt style:

- clear objective
- clear audience
- clear tone
- clear slide count

Example:

```text
Create an 8-slide strategy deck for executives. Keep it concise, decision-oriented, and focused on execution priorities.
```

## 2. `contextFiles`

Purpose:

- provide extra context material
- useful for text notes, supplemental requirements, or internal comments

Type:

- array of file paths

## 3. `sources`

Purpose:

- provide trusted source material
- convert sources into context before planning
- preserve slide-level source metadata
- export sources to presenter notes by default

Supported source types:

- text
- json
- html
- pdf
- docx
- image
- url

Suggested source priority:

1. user-uploaded material
2. official product pages
3. official documentation
4. investor materials
5. other external sources

## 4. `mock`

Purpose:

- choose whether to use the local mock planner

Good for:

- offline testing
- local integration work
- quick path validation without calling a model

## 5. `research`

Purpose:

- turn on lightweight research augmentation

Current note:

- this only works when Tavily is configured
- it is useful for demos, but it should not be treated as the final factual authority for rigorous production workflows

## What The Deck Output Contains

Generated deck JSON currently includes:

- `sourceDisplayMode`
- `slides[].sources`
- `slides[].speakerNotes`

### Default behavior

Current default:

- `sourceDisplayMode = notes`

That means:

- sources do not appear in slide body content
- sources do appear in presenter notes
- sources are still preserved in structured metadata

## Recommended Integration Model

If you are integrating this into an AI agent, the most stable path is:

1. the agent collects the user goal
2. the agent collects trusted source material
3. the agent organizes a request JSON
4. it calls `py-agent-skill.py`
5. it reads the response JSON
6. it returns the generated result to the user
7. when needed, it calls revise again

In short, you should treat it as a:

- local skill
- local deck backend
- agent tool

rather than as a fully independent end-user product.

## Recommendations For Different Integrators

## For Claude Code or coding-agent style tools

Best option:

- MCP integration (if MCP-compatible)
- CLI invocation (fallback)
- or JSON request plus `py-agent-skill.py`

Why:

- simple
- local path handling is straightforward
- easy to support multi-round revise flows

## For Claude Desktop, Cursor, or Windsurf

Best option:

- MCP integration

Why:

- native tool invocation — no file or HTTP coordination needed
- supports create + revise loops naturally
- easiest setup of all integration modes

## For service-based systems

Best option:

- HTTP invocation

Why:

- easier to integrate with existing backend systems
- easier to connect to external workflow engines

## For local automation scripts

Best option:

- CLI mode

Why:

- simple debugging
- no extra server lifecycle management

## Current Boundaries And Caveats

## 1. It is not a full research agent

Do not expect it to perform all of the following by itself:

- official-site discovery
- multi-source comparison
- evidence conflict resolution
- multimodal analysis

Those responsibilities belong to the upstream agent.

## 2. Images can be inserted, but no built-in visual understanding

As of v0.5.1, the renderer can insert local images and URL images into slides. However, this repository itself does not perform OCR or image reasoning — those belong to the upstream agent.

## 3. Slide-level sources exist, but attribution is still coarse

The deck output already includes:

- `slides[].sources`

But it does not yet map:

- a specific bullet to a specific source fragment
- a specific chart point to a specific data fragment

## 4. Brand template support (v0.5.0)

As of v0.5.0, you can pass a `.pptx` brand template to produce brand-matched output:

- Add `"template": "path/to/brand.pptx"` to your request
- The system will extract layouts, placeholders, theme colors, and fonts from the template
- Slides are rendered via `python-pptx` using the template's slide layouts
- Without a template, the existing JS renderer (pptxgenjs) is used automatically
- The API response includes a `"renderer"` field (`"python-pptx"` or `"pptxgenjs"`)

## 5. Image and visual support (v0.5.1)

As of v0.5.1, the `visuals` array on each slide accepts three types of items:

**Plain string** (text description):
```json
"visuals": ["Add a market context chart"]
```

**Image object** (local path or URL):
```json
"visuals": [
  {"type": "image", "path": "assets/logo.png", "alt": "Company logo", "position": "right"},
  {"type": "image", "url": "https://example.com/chart.png", "position": "center"}
]
```

**Placeholder object** (for later image generation):
```json
"visuals": [
  {"type": "placeholder", "prompt": "A workflow diagram showing the 4-step process", "position": "right"}
]
```

Supported `position` values: `right` (default), `left`, `center`, `full`.

Security: local paths are constrained to the project directory, URL images reject private networks (SSRF), maximum 10 MB, only common image formats accepted.

## 6. Chart data validation and fallback

As of v0.4.1, the system automatically validates chart slides:

- Charts must have non-empty `categories` and numeric `series` data
- Invalid charts are automatically downgraded to `bullet` layout with the original content preserved
- Source material is scanned for numerical data (percentages, currency, metrics) and injected as chart hints to the LLM
- Fallback decisions are logged in the deck's `assumptions` field

## Key Files

- `mcp_server.py`: MCP server entrypoint (Claude Desktop, Cursor, Windsurf)
- `py-agent-skill.py`: primary JSON skill entrypoint
- `py-skill-server.py`: primary HTTP service entrypoint
- `skill-manifest.json`: skill contract
- `py-generate-from-prompt.py`: primary create CLI
- `py-revise-deck.py`: primary revise CLI
- `python_backend/source_loader.py`: primary source loading layer
- `python_backend/smart_layer.py`: primary planning core
- `python_backend/template_engine.py`: .pptx template parser
- `python_backend/pptx_renderer.py`: python-pptx renderer (brand template mode)
- `python_backend/image_handler.py`: image resolution, validation, and insertion
- `generate-ppt.js`: PPT renderer (no-template mode)
- `deck-schema.json`: deck schema contract\n\n## API Versioning

As of v0.6.0, all API requests and responses include an `apiVersion` field:

- Current API version: `"1.0"`
- Include `"apiVersion": "1.0"` in all request JSON payloads (optional; server defaults to current version)
- All response JSON payloads include `"apiVersion": "1.0"`
- The server always responds with its own API version regardless of the client-provided value

This field enables forward-compatible API evolution without breaking existing integrations.

## 5. Docker Deployment

The project ships with `Dockerfile` and `docker-compose.yml` for containerized deployment.

### Quick Start with Docker Compose

```bash
export OPENAI_API_KEY="sk-..."
docker compose up --build
```

This starts the HTTP skill server on port 5000 (set via `ENV PORT=5000` in the Dockerfile). Outside Docker, the default is port 3010. Both are controlled by the `PORT` environment variable.

### MCP Server in Docker

```bash
# Local stdio MCP
docker run --rm -it -e OPENAI_API_KEY auto-ppt-engine python mcp_server.py

# Remote streamable HTTP MCP
docker run --rm -p 8080:8080 -e OPENAI_API_KEY auto-ppt-engine \
  python mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8080
```

### CLI in Docker

```bash
docker run --rm -e OPENAI_API_KEY -v $(pwd)/output:/app/output auto-ppt-engine \
  python py-generate-from-prompt.py --mock --prompt "Create an 8-slide AI strategy deck"
```

## One-Line Integration Advice

If you want to integrate now, the most stable path is:

**If you use Claude Desktop, Cursor, or Windsurf: start with MCP. Otherwise: start with JSON skill mode, then move to HTTP mode only when you need service-style integration.**