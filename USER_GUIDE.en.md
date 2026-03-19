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

Use the Python entrypoints first.

Primary commands:

```bash
npm run generate:source
npm run skill:create
npm run revise:mock
npm run skill:server
```

These npm commands now use the Python smart layer by default.

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
curl -X POST http://localhost:3010/skill -H "Content-Type: application/json" --data @sample-http-request.json
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
- `PRODUCT.en.md`
- `sample-input.json`
- `sample-source-brief.md`
- `sample-agent-request.json`
- `sample-agent-revise-request.json`
- `sample-http-request.json`

### Main execution files

- `py-generate-from-prompt.py`
- `py-revise-deck.py`
- `py-agent-skill.py`
- `py-skill-server.py`
- `generate-ppt.js`

### Compatibility wrappers

- `generate-from-prompt.js`
- `revise-deck.js`
- `agent-skill.js`
- `skill-server.js`

## Where It Is Still Weak

The project is still a prototype, not a production-grade product.

Current weak points include:

- it is not a complete research agent
- OCR and multimodal understanding are not fully implemented
- slide-level source binding is still coarse
- brand templates and visual control are still basic
- quality still depends on the upstream model and agent

## One-Line Summary

Today this project can already complete:

- `prompt -> deck -> pptx`
- `prompt + sources -> deck -> pptx`
- `existing deck + revise prompt -> revised deck -> pptx`
- `agent request -> skill response`
- `HTTP request -> generated PPT artifacts`