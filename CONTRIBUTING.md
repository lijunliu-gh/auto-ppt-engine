# Contributing

Thanks for contributing to Auto PPT Engine.

## Before You Start

- Read `README.md` for project scope and usage modes.
- Read `docs/PRODUCT.en.md` for positioning and boundaries.
- Read `docs/INTEGRATION_GUIDE.en.md` if your change affects agent or service integration.

## Development Setup

1. Install Node.js 18 or newer.
2. Install Python 3.10 or newer.
3. Install dependencies:

```bash
npm install && pip install -e ".[test]"
```

4. Copy `.env.example` to `.env` only if you need model-backed runs.

## Local Validation

Run the smoke checks before opening a pull request:

```bash
npm run ci:smoke
```

Run the full test suite:

```bash
python -m pytest tests/ -v
```

The test suite includes:

- `tests/test_smart_layer.py` — unit tests for planning, revision, chart validation, source loading
- `tests/test_mcp_server.py` — MCP server tool tests
- `tests/test_mcp_integration.py` — MCP stdio integration tests
- `tests/test_template_engine.py` — template parsing and PPTX rendering tests
- `tests/test_image_handler.py` — image pipeline and security tests
- `tests/test_coverage_boost.py` — cross-module coverage tests (LLM provider, skill API, smart layer)

Total: 409 tests, 84% line coverage. CI runs pytest across Python 3.10, 3.11, 3.12 and Node.js 18, 20, 22.

## Contribution Scope

Good contribution areas:

- deck planning quality
- revise quality
- source ingestion (see `python_backend/source_loader.py`)
- chart data reliability and validation
- MCP server integration (`mcp_server.py`)
- schema validation
- docs and examples
- integration stability
- CI and test coverage

Please keep changes focused. Avoid mixing unrelated refactors into the same pull request.

## Pull Request Guidelines

- explain what changed and why
- mention affected user flows
- include sample commands used for verification
- update docs when behavior changes
- avoid committing generated files under `output/`

## Design Principles

- prefer trusted and user-provided sources over broad web search
- keep rendered slides visually clean
- preserve provenance in machine-readable form where possible
- treat this repository as an agent backend, not a full research agent

## Reporting Problems

- Use the issue templates when possible.
- For security-sensitive issues, do not open a public issue. Follow `SECURITY.md`.