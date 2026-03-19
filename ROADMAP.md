# Roadmap

Current version: **v0.5.0**

This roadmap reflects the project's current capabilities, known gaps, and planned evolution from experimental prototype to a production-grade AI-agent PowerPoint backend.

---

## Current Baseline (v0.3.1)

| Capability | Status |
|------------|--------|
| Python planning + JS rendering + JSON contract | ✅ Stable |
| 13 slide layouts (title, bullet, timeline, chart, table, etc.) | ✅ |
| Chart / Table schema + rendering | ✅ Schema and renderer exist; LLM planning rarely generates valid chart data |
| Source ingestion (PDF, DOCX, HTML, TXT, JSON, URL) | ✅ |
| Security hardening (path traversal, SSRF, file size, subprocess timeout) | ✅ Added in v0.3.1 |
| Pluggable LLM provider abstraction | ✅ Added in v0.3.1 |
| Structured logging | ✅ Added in v0.3.1 |
| Schema versioning | ✅ Added in v0.3.1 |
| Unit tests (39 pytest cases) | ✅ Added in v0.3.1 |
| CLI / JSON Skill / HTTP Server | ✅ |

---

## Phase 1 — MCP Server + Ecosystem Integration → v0.4.0 ✅

**Status**: Complete — released in v0.4.0

**Goal**: Enable native invocation from Claude Desktop, Cursor, Windsurf, and other MCP-compatible AI environments.

| Task | Description | Complexity |
|------|-------------|------------|
| Implement MCP Server | Expose `create_deck` and `revise_deck` as MCP tools via the `mcp` Python SDK | Medium |
| MCP tool schema | Map existing `skill-manifest.json` actions to MCP tool definitions | Low |
| Security boundary | MCP runs locally but must enforce file access scope (reuse v0.3.1 path traversal protection) | Low (already done) |
| Integration test | End-to-end script: MCP call → deck JSON → PPTX output | Medium |
| Documentation | Add MCP config examples for Claude Desktop and Cursor | Low |

**Why first**: Security prerequisites are met (v0.3.1). Implementation reuses existing HTTP server logic. Highest leverage for user acquisition — one MCP server makes the tool callable from every MCP-compatible environment with zero friction.

**Deliverables**: `mcp_server.py`, Cursor / Claude Desktop config examples, integration tests.

---

## Phase 2 — Chart Data Reliability + Multi-Model Validation → v0.4.1 ✅

**Status**: Complete — released in v0.4.1

**Goal**: Make LLM-generated chart and table data actually usable (not empty placeholders).

| Task | Description | Complexity |
|------|-------------|------------|
| Strengthen chart prompts | Add chart data generation constraints and few-shot examples to system prompt | Low |
| Source → chart mapping | When sources contain numerical data (CSV, JSON, tables), auto-extract and inject into chart context | Medium |
| Multi-model testing | Run planning through Claude, GPT-4.1, Gemini; compare schema pass rate and chart fill rate | Medium |
| Chart fallback | When LLM-generated chart data is invalid, fall back to bullet layout + assumption declaration | Low |

**Why here**: The schema and renderer already support charts — the real bottleneck is LLM planning quality. The v0.3.1 LLM provider abstraction makes multi-model testing straightforward.

---

## Phase 3 — Brand Template Engine → v0.5.0 ✅

**Status**: Complete — released in v0.5.0

**Goal**: Accept a user-provided `.pptx` master template and produce brand-matched output.

| Task | Description | Complexity |
|------|-------------|------------|
| Template parsing | Read `.pptx` slide layouts + placeholders via `python-pptx` | High |
| Layout mapping | Build a config that maps schema layouts → master slide layouts | Medium |
| Dual render path | No template → existing JS renderer; with template → Python `python-pptx` placeholder injection | High |
| Schema extension | Add `template` field to deck JSON (template path + layout mapping overrides) | Low |
| Sample templates | Ship 2–3 ready-to-use brand templates (tech, business, education) | Medium |

**Why here, not earlier**: This is the biggest usability leap, but also the highest implementation cost. It may require introducing `python-pptx` as a second render path alongside `pptxgenjs`. Best tackled after MCP and chart reliability have established a user base.

**Risk**: May require re-evaluating whether to keep the JS render layer or migrate entirely to `python-pptx`.

---

## Phase 4 — Image Asset Pipeline → v0.5.1

**Goal**: Support image insertion and lay the groundwork for multi-agent image collaboration.

| Task | Description | Complexity |
|------|-------------|------------|
| Local image insertion | `visuals` field accepts local file paths / URLs → renderer actually inserts images | Medium |
| Image placeholder protocol | `visuals` supports `{"type": "placeholder", "prompt": "...", "position": "right"}` | Low |
| Two-pass rendering | First pass: render with blank placeholders + annotations → external agent fills images → second pass: final render | Medium |
| Size / position constraints | Renderer auto-calculates image region size to prevent overflow | Medium |

**Why last**: Text content is the core value of any presentation. Image support is important but additive. Start with local image insertion (practical), then add the placeholder protocol (interface for multi-agent ecosystems).

---

## Ongoing (Across All Phases)

| Task | Description |
|------|-------------|
| Remove legacy JS code | ~~After Phase 1, delete `deck-agent-core.js` and `source-loader.js` entirely~~ ✅ Done in v0.4.1 |
| Expand test coverage | Each phase adds integration tests; target 80%+ coverage |
| API versioning | Add `apiVersion` field to requests / responses for backward compatibility during Phase 3 schema changes |
| CI hardening | Add pytest + multi-Node-version matrix to GitHub Actions |
| Documentation sync | Update EN / ZH / JA docs with each release |

---

## Timeline Summary

```text
v0.4.0   MCP Server               ← Highest leverage, do first
v0.4.1   Chart reliability         ← Prove core quality
v0.5.0   Brand template engine     ← Usability breakthrough
v0.5.1   Image pipeline            ← Ecosystem expansion
```

---

## Contributing

If you are interested in contributing to any of these areas, see [CONTRIBUTING.md](CONTRIBUTING.md) and open an issue to discuss your approach before starting work.
