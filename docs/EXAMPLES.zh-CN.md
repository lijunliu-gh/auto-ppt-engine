# 示例

这份文档给第一次接触这个仓库的人使用。

如果你不想先读完整文档，而是想先跑通一遍，可以从这里开始。

## 最快跑通一次

先安装依赖：

```bash
npm install
python -m pip install -r requirements.txt
```

使用内置 source brief 生成一版 deck：

```bash
python py-generate-from-prompt.py --mock --prompt "Create an 8-slide AI workspace strategy deck for executives" --source examples/inputs/sample-source-brief.md
```

预期输出：

- `output/py-generated-deck.json`
- `output/py-generated-deck.pptx`

对外分享前建议再跑一次可视化质检：

```bash
./auto-ppt qa-visual output/py-generated-deck.pptx --strict
```

预期质检产物：

- `output/py-generated-deck-qa/visual-qa-report.json`

## 使用 Deck Brief 文件

自然语言 brief 示例：

- `examples/inputs/sample-deck-brief.md`

结构化 brief 示例：

- `examples/inputs/sample-deck-brief.json`

把 brief 当作 source 输入的命令示例：

```bash
python py-generate-from-prompt.py --mock --prompt "Turn this brief into an 8-slide product deck" --source examples/inputs/sample-deck-brief.md
```

## 修订已生成的 Deck

第一版生成完成后，可以继续修订：

```bash
python py-revise-deck.py --mock --deck output/py-generated-deck.json --prompt "Compress this deck to 6 slides and make it more conclusion-driven"
```

预期输出：

- `output/py-revised-deck.json`
- `output/py-revised-deck.pptx`

修订后同样建议执行：

```bash
./auto-ppt qa-visual output/py-revised-deck.pptx --strict
```

## JSON Skill 示例

如果你要把它接进别的 agent 或脚本流程，可以直接用 JSON 请求文件：

```bash
python py-agent-skill.py --request examples/inputs/sample-agent-request.json --response output/py-agent-response.json
```

相关文件：

- `examples/inputs/sample-agent-request.json`
- `output/py-agent-response.json`

## HTTP 示例

启动本地服务：

```bash
python py-skill-server.py
```

调用接口：

```bash
curl -X POST http://localhost:3010/skill -H "Content-Type: application/json" --data @examples/inputs/sample-http-request.json
```

## 应该先看哪个示例

- 如果你使用 Claude Desktop、Cursor 或 Windsurf，先用 MCP 接入 —— 这是最简单的方式
- 如果你只是想最快看到成功结果，先看 `examples/inputs/sample-source-brief.md`
- 如果你想理解什么是 deck brief，先看 `examples/inputs/sample-deck-brief.md`
- 如果你要集成进别的 agent 流程，先看 `examples/inputs/sample-agent-request.json`
- 如果你更偏向本地服务调用，先看 `examples/inputs/sample-http-request.json`

## MCP 示例（Claude Desktop / Cursor / Windsurf）

配置好 MCP 之后（参见 [接入说明](INTEGRATION_GUIDE.zh-CN.md)），直接对 AI 助手说：

> 帮我做一个 8 页的 AI 工作空间策略报告，面向管理层，用 examples/inputs/sample-source-brief.md 作为素材

助手会自动调用 `create_deck`。修订时说：

> 压缩到 5 页，结论导向

助手会自动用之前生成的 deck 调用 `revise_deck`。

用 MCP 开发检查器测试：

```bash
mcp dev mcp_server.py
```

### 远程 MCP（Streamable HTTP）

```bash
python mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8080
```

MCP 客户端连接 `http://<server-host>:8080/mcp` 即可。

## Docker 示例

通过 Docker Compose 构建并启动：

```bash
export OPENAI_API_KEY="sk-..."
docker compose up --build
curl http://localhost:5000/health
```

或者执行一次性生成：

```bash
docker run --rm -e OPENAI_API_KEY -v $(pwd)/output:/app/output auto-ppt-engine \
  python py-generate-from-prompt.py --mock --prompt "做一个8页的AI策略汇报"
```
