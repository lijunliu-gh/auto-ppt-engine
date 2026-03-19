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
- deck JSON validation
- PPTX rendering through the Node renderer
- agent-callable JSON request and response flow
- local HTTP skill endpoint

## Public Entry Points

Preferred entry points:

- `py-generate-from-prompt.py`
- `py-revise-deck.py`
- `py-agent-skill.py`
- `py-skill-server.py`

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
- stronger theme and template support
- better layout quality and typography control
- broader automated testing
- hosted deployment hardening

## Recommended Open-Source Framing

Recommended GitHub description:

> Open-source PowerPoint backend for AI agents using a Python smart layer for planning and a JavaScript renderer for PPTX output.
