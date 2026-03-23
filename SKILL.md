---
name: auto-ppt-engine
description: Plan, revise, validate, and render PowerPoint decks from user requirements and trusted source material.
user-invocable: true
---

# Auto PPT Engine Skill

## Purpose

Use this skill when the user wants to create or revise a PowerPoint presentation from requirements, reference material, uploaded assets, or trusted external sources.

This file is intentionally narrow. It defines agent behavior, not repository marketing or end-user documentation.

## When To Use This Skill

Use this skill when the user asks for any of the following:

- create a PowerPoint presentation
- create an executive deck
- generate a sales deck
- generate a strategy deck
- revise an existing presentation
- compress a deck into fewer slides
- make slides more conclusion-driven
- turn notes or documents into a presentation

## Agent Rules

The agent using this skill should:

1. understand the presentation objective
2. identify missing requirements
3. prefer trusted sources over generic search
4. produce a coherent structured deck
5. validate before rendering
6. preserve useful content during revision

## Source Priority

When planning deck content, use sources in this order of trust whenever possible:

1. User-uploaded documents and assets
2. Official product websites
3. Official documentation
4. Official financial or investor materials
5. User-provided notes and context
6. Reputable third-party sources
7. Generic web search results only as a fallback

## Visual Rules

The `visuals` array on each slide supports three kinds of items:

1. Plain strings — text descriptions or visual suggestions
2. Image objects — `{"type": "image", "path": "..."}` or `{"type": "image", "url": "..."}` for actual images to insert
3. Placeholder objects — `{"type": "placeholder", "prompt": "..."}` for images to be generated later

Supported position values: `right` (default), `left`, `center`, `full`.

When source materials reference specific images or diagrams, emit image objects with the file path. When no actual image is available but a visual would help, use a placeholder with a descriptive prompt. Otherwise, use plain string descriptions.

Do not rely on generic web search when the user has already provided source files or official links.

## Required Inputs

Try to collect or infer the following:

- presentation objective
- target audience
- desired tone or style
- slide count or expected length
- trusted source material
- constraints such as timeline, brand, or structure

If key inputs are missing, ask concise clarification questions.

## Workflow

### Create Flow

1. Read the user request
2. Ask for clarification if the audience, objective, or source base is unclear
3. Prefer user files and official sources over broad search
4. Build a deck plan with a clear narrative arc
5. Return structured deck JSON that matches the schema
6. Render the final PowerPoint

### Revise Flow

1. Read the existing deck JSON
2. Interpret the revision request precisely
3. Preserve the deck objective unless the user changes it
4. Update only what is necessary
5. Keep the revised deck internally consistent
6. Render the revised PowerPoint

## Content Standards

The generated deck should:

- be clear and audience-aware
- avoid unsupported claims
- avoid vague filler content
- present evidence-based points when source material exists
- be concise at executive level unless the user asks for detail
- keep titles action-oriented when appropriate
- maintain narrative continuity across slides

## Layout Rules

Choose layouts intentionally:

- `title`: opening slide
- `agenda`: outline slide
- `section`: major transition
- `bullet`: concise talking points
- `two-column`: compare two categories or separate summary from detail
- `comparison`: option evaluation
- `timeline`: milestones and roadmap
- `process`: workflow, operating model, or phased plan
- `table`: structured factual comparison
- `chart`: quantitative story
- `quote`: highlight a key statement
- `summary`: synthesis slide
- `closing`: final takeaway or next step

Do not use charts or tables unless the content justifies them.

### Chart Data Requirements

When using chart layout, always populate concrete data:

- `chart.type`: one of `bar`, `line`, `pie`, `area`
- `chart.title`: clear descriptive title
- `chart.categories`: array of label strings (e.g. quarters, product names)
- `chart.series`: array of `{name, data}` objects where data lengths match categories
- If source material contains numbers, extract and use real data
- If no real data is available, use realistic placeholders and note it in assumptions
- Never leave categories or series as empty arrays

The system automatically validates chart data after generation. If a chart slide has invalid data (empty categories, missing series, or non-numeric values), it falls back to a bullet layout and records the fallback in assumptions.

## Narrative Guidance

Prefer a narrative structure such as:

1. Title / context
2. Problem or opportunity
3. Current state or market context
4. Key insights
5. Strategy or recommendation
6. Execution plan
7. Risks or dependencies
8. Conclusion / next steps

Adapt this structure to the user's use case.

## Output Contract

Produce deck JSON that follows the repository schema.

At minimum, ensure:

- `title` is present
- `theme` is present
- `slideCount` matches the number of slides
- each slide has a supported `layout`
- each slide has a clear `title`
- slide content is internally consistent

## Revision Rules

When revising a deck:

- preserve useful existing content where possible
- remove repetition
- compress when the user asks for fewer slides
- sharpen conclusions when the user asks for a more executive tone
- strengthen execution details when asked for an action plan
- change layout only when it improves communication

## Non-Goals

This skill does not guarantee factual correctness by itself. Correctness depends on the quality of the inputs, source retrieval, and model reasoning upstream.

If the task requires high rigor, the agent using this skill should:

- retrieve trusted documents
- preserve source provenance
- avoid unsupported extrapolation
- route ambiguous claims back to the user for confirmation

## References

For repository usage and integration details, see:

- `README.md`
- `docs/USER_GUIDE.en.md`
- `docs/INTEGRATION_GUIDE.en.md`
