# Repository Map

## Top-Level Layout

```text
auto-ppt-engine/
|-- python_backend/
|   |-- __init__.py            # package init + version metadata
|   |-- smart_layer.py         # planning, revision, validation
|   |-- source_loader.py       # trusted material ingestion
|   |-- skill_api.py           # skill request orchestration + dual render dispatch
|   |-- js_renderer.py         # bridge into the Node PPTX renderer
|   |-- pptx_renderer.py       # python-pptx renderer (brand template mode)
|   |-- template_engine.py     # .pptx template parser (layouts, placeholders, theme)
|   |-- image_handler.py       # image asset pipeline (classify, resolve, security)
|   `-- llm_provider.py        # LLM provider abstraction (OpenAI/OpenRouter/Claude/Gemini)
|-- mcp_server.py              # MCP server (Claude Desktop, Cursor, Windsurf)
|-- py-generate-from-prompt.py
|-- py-revise-deck.py
|-- py-agent-skill.py
|-- py-skill-server.py
|-- generate-ppt.js            # stable PPTX renderer (no-template path)
|-- compat/
|   |-- generate-from-prompt.js # compatibility wrapper
|   |-- revise-deck.js          # compatibility wrapper
|   |-- agent-skill.js          # compatibility wrapper
|   `-- skill-server.js         # compatibility wrapper
|-- assets/
|   `-- social-preview.png
|-- docs/
|   |-- EXAMPLES.en.md
|   |-- EXAMPLES.zh-CN.md
|   |-- EXAMPLES.ja.md
|   |-- PRODUCT.en.md
|   |-- USER_GUIDE.en.md
|   |-- INTEGRATION_GUIDE.en.md
|   `-- REPOSITORY_MAP.md
|-- examples/
|   `-- inputs/
|       |-- sample-source-brief.md
|       |-- sample-deck-brief.md
|       |-- sample-deck-brief.json
|       |-- sample-agent-request.json
|       |-- sample-agent-revise-request.json
|       |-- sample-http-request.json
|       `-- sample-input.json
|-- quality_samples/
|   |-- manifest.json
|   |-- cases/
|   `-- sources/
|-- tests/
|-- output/
|-- scripts/
|-- README.md
|-- CHANGELOG.md
|-- ROADMAP.md
`-- package.json
```

## Practical Split

- `python_backend/` owns planning, revision, source understanding, and agent-facing orchestration.
- `generate-ppt.js` is the stable PPTX renderer when no template is provided.
- `mcp_server.py` is the MCP entrypoint for Claude Desktop, Cursor, and Windsurf.
- root-level `py-*.py` files are the direct Python entrypoints.
- `docs/` holds multilingual usage, product, and integration documentation.
- `examples/inputs/` holds demo requests and source inputs for onboarding and smoke checks.
- `quality_samples/` holds the fixed Phase 7 regression corpus for quality work.
- `tests/` contains pytest coverage for the Python backend and integration flows.
- `output/` holds generated deck JSON and PPTX artifacts.
