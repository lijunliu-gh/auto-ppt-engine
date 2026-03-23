# Documentation Index

This directory holds the user-facing and integration documentation for Auto PPT Engine.

## Start Here

- [EXAMPLES.en.md](EXAMPLES.en.md): shortest copy-paste examples for first-time users
- [USER_GUIDE.en.md](USER_GUIDE.en.md): what the project does and how to use it day to day
- [INTEGRATION_GUIDE.en.md](INTEGRATION_GUIDE.en.md): file, HTTP, and MCP integration patterns

## Multilingual Documents

### Examples

- [EXAMPLES.en.md](EXAMPLES.en.md)
- [EXAMPLES.zh-CN.md](EXAMPLES.zh-CN.md)
- [EXAMPLES.ja.md](EXAMPLES.ja.md)

### User Guides

- [USER_GUIDE.en.md](USER_GUIDE.en.md)
- [USER_GUIDE.zh-CN.md](USER_GUIDE.zh-CN.md)
- [USER_GUIDE.ja.md](USER_GUIDE.ja.md)

### Integration Guides

- [INTEGRATION_GUIDE.en.md](INTEGRATION_GUIDE.en.md)
- [INTEGRATION_GUIDE.zh-CN.md](INTEGRATION_GUIDE.zh-CN.md)
- [INTEGRATION_GUIDE.ja.md](INTEGRATION_GUIDE.ja.md)

## Suggested Reading Order

1. First-time evaluation: `EXAMPLES.en.md` → `USER_GUIDE.en.md`
2. Agent or service integration: `INTEGRATION_GUIDE.en.md`

## Visual QA Note

The CLI now includes a visual quality check command:

```bash
./auto-ppt qa-visual output/py-generated-deck.pptx --strict
```

This command is documented in all three User Guides and should be used after generation/revision before sharing decks externally.
