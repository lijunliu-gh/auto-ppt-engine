# Examples

This file is for people who want to run the project quickly without reading the full documentation first.

## Fastest Successful Run

Install dependencies:

```bash
npm install
python -m pip install -r requirements.txt
```

Generate a deck from the built-in source brief:

```bash
python py-generate-from-prompt.py --mock --prompt "Create an 8-slide AI workspace strategy deck for executives" --source examples/inputs/sample-source-brief.md
```

Expected outputs:

- `output/py-generated-deck.json`
- `output/py-generated-deck.pptx`

Optional visual QA before sharing:

```bash
./auto-ppt qa-visual output/py-generated-deck.pptx --strict
```

Expected QA artifact:

- `output/py-generated-deck-qa/visual-qa-report.json`

## Use A Deck Brief File

Natural-language brief example:

- `examples/inputs/sample-deck-brief.md`

Structured brief example:

- `examples/inputs/sample-deck-brief.json`

Example prompt using the deck brief as source material:

```bash
python py-generate-from-prompt.py --mock --prompt "Turn this brief into an 8-slide product deck" --source examples/inputs/sample-deck-brief.md
```

## Revise The Generated Deck

After the first deck is created:

```bash
python py-revise-deck.py --mock --deck output/py-generated-deck.json --prompt "Compress this deck to 6 slides and make it more conclusion-driven"
```

Expected outputs:

- `output/py-revised-deck.json`
- `output/py-revised-deck.pptx`

Optional visual QA for revised deck:

```bash
./auto-ppt qa-visual output/py-revised-deck.pptx --strict
```

## JSON Skill Example

Use the JSON skill request contract when another agent or script wants file-based integration:

```bash
python py-agent-skill.py --request examples/inputs/sample-agent-request.json --response output/py-agent-response.json
```

Files to inspect:

- `examples/inputs/sample-agent-request.json`
- `output/py-agent-response.json`

## HTTP Example

Start the local service:

```bash
python py-skill-server.py
```

Call the skill:

```bash
curl -X POST http://localhost:3010/skill -H "Content-Type: application/json" --data @examples/inputs/sample-http-request.json
```

## Which Example To Start With

- Start with MCP if you use Claude Desktop, Cursor, or Windsurf — it's the simplest integration.
- Start with `examples/inputs/sample-source-brief.md` if you want the shortest successful CLI demo.
- Start with `examples/inputs/sample-deck-brief.md` if you want to understand what a deck brief looks like.
- Start with `examples/inputs/sample-agent-request.json` if you are integrating this project into another workflow.
- Start with `examples/inputs/sample-http-request.json` if your system prefers local service calls.

## MCP Example (Claude Desktop / Cursor / Windsurf)

After configuring MCP (see [Integration Guide](INTEGRATION_GUIDE.en.md)), just ask your AI assistant:

> Create an 8-slide AI workspace strategy deck for executives, using examples/inputs/sample-source-brief.md as source material

The assistant will call `create_deck` automatically. To revise:

> Compress that deck to 5 slides and make it more conclusion-driven

The assistant will call `revise_deck` with the previously generated deck path.

To test MCP directly without a client:

```bash
mcp dev mcp_server.py
```

### Remote MCP (Streamable HTTP)

```bash
python mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8080
```

Then point your MCP client to `http://<server-host>:8080/mcp`.

## Docker Example

Build and run with Docker Compose:

```bash
export OPENAI_API_KEY="sk-..."
docker compose up --build
curl http://localhost:5000/health
```

Or run a one-off generation:

```bash
docker run --rm -e OPENAI_API_KEY -v $(pwd)/output:/app/output auto-ppt-engine \
  python py-generate-from-prompt.py --mock --prompt "Create an 8-slide AI strategy deck"
```
