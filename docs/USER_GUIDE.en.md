# User Guide

This document is written for users rather than developers.

If you want to know what the project can do today and how to operate it, start here.

## What This Is

This is a PowerPoint backend prototype that can be called by an AI agent.

It is best understood as:

- a Python smart layer that plans or revises a deck
- a JavaScript renderer that turns deck JSON into `.pptx`

In short:

`requirements + source material -> Python planning -> deck JSON -> Node rendering -> PPTX`

## Good Use Cases

The current version is a good fit for:

- product strategy presentations
- executive review decks
- sales proposal decks
- project retrospectives
- first-draft training decks
- presentations grounded in official sites, PDFs, DOCX files, or Markdown briefs
- workflows where you generate a first draft and then revise it multiple times

## What To Use By Default

**If you are new to the repository**, use the official CLI first:

```bash
./auto-ppt init
./auto-ppt generate --mock --prompt "Create an 8-slide strategy deck" --source examples/inputs/sample-source-brief.md
```

This is the shortest path to proving the project works end-to-end.

**If you use Claude Desktop, Cursor, or Windsurf**, MCP is the fastest integration path after that. Add the server to your MCP config and ask it to create a deck directly from conversation.

The legacy Python entrypoints still exist, but `auto-ppt` is now the official user-facing CLI.

If you need the older commands directly, you can still use:

```bash
npm run generate:source
npm run skill:create
npm run revise:mock
npm run skill:server
```

These npm commands now use the Python smart layer by default.

If you want the shortest copy-paste onboarding path, read `docs/EXAMPLES.en.md` first.

## What It Can Do Today

### 1. Render PPT from existing JSON

Use this when you already have structured deck data.

```bash
npm run generate
```

### 2. Generate PPT from a natural-language prompt

Use this when you only have a rough request.

```bash
npm run generate:mock
```

If a model is configured, you can also run:

```bash
npm run generate:prompt
```

Direct Python example:

```bash
python py-generate-from-prompt.py --prompt "Create an 8-slide AI product strategy deck for executives in a professional tone"
```

### 3. Generate PPT with source material

This is the recommended path for most real use cases.

```bash
npm run generate:source
```

You can also pass your own sources:

```bash
python py-generate-from-prompt.py --mock --prompt "Create an 8-slide strategy deck" --source your-brief.md --source https://example.com/product
```

### 4. Revise an existing deck

Use this after generating a first draft.

Typical revision requests include:

- reduce the slide count
- make it more conclusion-driven
- emphasize the execution plan
- reorganize the structure
- make it more suitable for executives

```bash
npm run revise:mock
```

### Visual QA for generated PPTX

Use this after generation or revision to catch common visual risks before sharing slides.

```bash
./auto-ppt qa-visual output/py-generated-deck.pptx --strict
```

What this command does:

- runs structural visual heuristics (edge crowding, overlap candidates, empty slides)
- exports slide images when `soffice` and `pdftoppm` are available
- writes `visual-qa-report.json` under `<deck-name>-qa/`

In CI, use `--strict` to fail the step when any issue is detected.

### 5. Use it as a skill from another agent

Use this when another workflow needs a request and response file contract.

```bash
npm run skill:create
npm run skill:revise
```

### 6. Use it as an HTTP service

Use this when your system prefers local API-style integration.

```bash
npm run skill:server
curl http://localhost:3010/health
curl -X POST http://localhost:3010/skill -H "Content-Type: application/json" --data @examples/inputs/sample-http-request.json
```

### 7. Use it via MCP (Claude Desktop, Cursor, Windsurf)

This is the recommended path for AI-native workflows.

Add to your MCP client config:

```json
{
  "mcpServers": {
    "auto-ppt": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/auto-ppt-engine"
    }
  }
}
```

Then ask your AI assistant to create or revise a deck. The MCP server exposes `create_deck` and `revise_deck` tools.

For remote/hosted deployments, the MCP server also supports streamable HTTP transport:

```bash
python mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8080
```

### 8. Docker

```bash
# One-command launch (HTTP skill server)
docker compose up --build

# Or run MCP server with remote transport
docker run --rm -p 8080:8080 -e OPENAI_API_KEY auto-ppt-engine \
  python mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8080
```

## How Source Material Works

Supported source types include:

- local text files: `txt`, `md`, `csv`, `json`, `yaml`, `xml`
- local HTML
- local PDF
- local DOCX
- image file references
- HTTP and HTTPS URLs

Current default source display behavior:

- slide body does not show sources
- presenter notes do show sources
- per-slide source metadata is preserved in the deck JSON

## Recommended Workflow

If you want a more rigorous presentation, do not rely on a prompt alone.

The better workflow is:

1. Define the presentation goal.
2. Provide source material.
3. Generate a first draft.
4. Run 1 to 3 revision rounds.

## Main Files To Know

### User-facing files

- `README.md`
- `docs/EXAMPLES.en.md`
- `examples/inputs/sample-deck-brief.md`
- `examples/inputs/sample-deck-brief.json`
- `examples/inputs/sample-input.json`
- `examples/inputs/sample-source-brief.md`
- `examples/inputs/sample-agent-request.json`
- `examples/inputs/sample-agent-revise-request.json`
- `examples/inputs/sample-http-request.json`

## What A Deck Brief Looks Like

A deck brief is the task definition for the presentation you want the system to produce.

It can be either:

- a natural-language brief document such as `examples/inputs/sample-deck-brief.md`
- a structured JSON brief such as `examples/inputs/sample-deck-brief.json`

Useful brief fields include:

- topic
- goal
- audience
- slide count
- tone
- must-include sections
- constraints
- supporting materials

### Main execution files

- `py-generate-from-prompt.py`
- `py-revise-deck.py`
- `py-agent-skill.py`
- `py-skill-server.py`
- `generate-ppt.js`

## Themes

The engine ships with 6 built-in themes. Use `--theme` to change the look of generated decks.

Available themes: `business-clean`, `corporate-blue`, `dark-executive`, `warm-modern`, `minimal`, `tech`.

### CLI

```bash
./auto-ppt generate --theme dark-executive --prompt "Create an 8-slide strategy deck"
```

### MCP / API

Include `"theme": "corporate-blue"` in your request JSON or MCP tool parameters.

### Custom Themes

Create a JSON file following the schema in `assets/themes/theme-schema.json`:

```json
{
  "name": "my-brand",
  "colors": {
    "primary": "1A365D",
    "secondary": "2B6CB0",
    "accent": "ED8936",
    "background": "F7FAFC",
    "slideBg": "FFFFFF",
    "text": "1A202C",
    "textLight": "F7FAFC",
    "textMuted": "718096",
    "headerBg": "E2E8F0",
    "border": "CBD5E0"
  },
  "fonts": {
    "heading": "Aptos Display, Microsoft YaHei, PingFang SC",
    "body": "Aptos, Microsoft YaHei, PingFang SC"
  },
  "chartColors": ["1A365D", "2B6CB0", "ED8936", "E53E3E"]
}
```

Pass a custom theme file path via `--theme /path/to/my-brand.json`.

## Chart Data Handling

When slides use the `chart` layout, the system validates chart data automatically:

- Charts must have non-empty categories and series with numeric data
- If chart data is invalid, the slide automatically falls back to a bullet layout
- Source material is scanned for numerical data (percentages, currency, metrics) and injected as chart hints to the LLM

## Image and Visual Support

As of v0.5.1, the `visuals` array on each slide supports three types of items:

- **Plain strings**: text descriptions or suggestions (e.g. `"Add a market context chart"`)
- **Image objects**: `{"type": "image", "path": "assets/logo.png"}` or `{"type": "image", "url": "https://..."}` — the renderer inserts the actual image
- **Placeholder objects**: `{"type": "placeholder", "prompt": "A workflow diagram"}` — renders as a labeled box for later image generation

Each visual item supports a `position` field: `right` (default), `left`, `center`, or `full`.

Security controls for images:

- Local paths are validated to stay within the project directory (path traversal prevention)
- URL images are validated to reject private/internal networks (SSRF protection)
- Maximum image size: 10 MB
- Only common image formats accepted: PNG, JPG, GIF, BMP, TIFF, SVG, WebP

## Where It Is Still Weak

The project is still a prototype, not a production-grade product.

Current weak points include:

- it is not a complete research agent
- OCR and multimodal understanding are not fully implemented
- slide-level source binding is still coarse
- quality still depends on the upstream model and agent

## API Versioning

As of v0.6.0, all API requests and responses include an `apiVersion` field set to `"1.0"`. This field ensures compatibility as the API evolves. When making custom integration requests, include `"apiVersion": "1.0"` in your JSON payload.

## One-Line Summary

Today this project can already complete:

- `prompt -> deck -> pptx`
- `prompt + sources -> deck -> pptx`
- `existing deck + revise prompt -> revised deck -> pptx`
- `MCP tool call -> deck + pptx`
- `agent request -> skill response`
- `HTTP request -> generated PPT artifacts`