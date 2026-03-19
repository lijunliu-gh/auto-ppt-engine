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
4. The upstream agent calls the revise flow again when the user requests changes.

## Supported Integration Modes

## 1. CLI Integration

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
python py-generate-from-prompt.py --mock --prompt "Create an 8-slide product strategy deck" --source sample-source-brief.md
```

### Revise

```bash
python py-revise-deck.py --deck output/generated-deck.json --prompt "Compress this deck to 6 slides"
```

### Agent skill request mode

```bash
python py-agent-skill.py --request sample-agent-request.json --response output/py-agent-response.json
```

## 2. JSON Skill Integration

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
      "path": "sample-source-brief.md",
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
  "prompt": "Compress this deck, make it more conclusion-driven, and emphasize the execution plan",
  "mock": true,
  "research": false,
  "engine": "python-smart-layer",
  "deckPath": "output/generated-deck.json",
  "contextFiles": [],
  "sources": [
    {
      "path": "sample-source-brief.md",
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
python py-agent-skill.py --request sample-agent-request.json --response output/py-agent-response.json
```

### Response format

```json
{
  "ok": true,
  "action": "create",
  "prompt": "string",
  "deckJsonPath": "absolute path",
  "pptxPath": "absolute path",
  "slideCount": 8,
  "assumptions": [],
  "sourcesUsed": []
}
```

## 3. HTTP Integration

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
curl -X POST http://localhost:3010/skill -H "Content-Type: application/json" --data @sample-http-request.json
```

### Example HTTP request body

```json
{
  "action": "create",
  "prompt": "Create an 8-slide AI agent product strategy deck for executives in a professional tone",
  "mock": true,
  "research": false,
  "contextFiles": [],
  "sources": [
    {
      "path": "sample-source-brief.md",
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
4. it calls `agent-skill.js`
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

- CLI invocation
- or JSON request plus `py-agent-skill.py`

Why:

- simple
- local path handling is straightforward
- easy to support multi-round revise flows

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

## 2. Images are currently references, not true visual understanding

Images can enter the source pipeline, but this repository itself does not perform full OCR or image reasoning.

## 3. Slide-level sources exist, but attribution is still coarse

The deck output already includes:

- `slides[].sources`

But it does not yet map:

- a specific bullet to a specific source fragment
- a specific chart point to a specific data fragment

## 4. Layout and brand control are still prototype-level

If you need enterprise-grade template control, more work is still required.

## Key Files

- `py-agent-skill.py`: primary JSON skill entrypoint
- `py-skill-server.py`: primary HTTP service entrypoint
- `skill-manifest.json`: skill contract
- `py-generate-from-prompt.py`: primary create CLI
- `py-revise-deck.py`: primary revise CLI
- `python_backend/source_loader.py`: primary source loading layer
- `python_backend/smart_layer.py`: primary planning core
- `generate-ppt.js`: PPT renderer
- `deck-schema.json`: deck schema contract

## Compatibility Note

The JavaScript entrypoints still exist for older integrations, but they now forward to the Python smart layer. New integrations should treat Python as the primary entrypoint surface.

## One-Line Integration Advice

If you want to integrate now, the most stable path is:

**start with JSON skill mode, then move to HTTP mode only when you need service-style integration.**