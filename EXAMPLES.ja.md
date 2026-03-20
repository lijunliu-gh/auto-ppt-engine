# 例

このドキュメントは、このリポジトリを初めて触る人向けです。

最初にすべての文書を読むのではなく、まず一度動かしたい場合はここから始めてください。

## 最短で成功する実行例

依存関係をインストールします。

```bash
npm install
python -m pip install -r requirements.txt
```

内蔵の source brief から deck を生成します。

```bash
python py-generate-from-prompt.py --mock --prompt "Create an 8-slide AI workspace strategy deck for executives" --source sample-source-brief.md
```

想定される出力:

- `output/py-generated-deck.json`
- `output/py-generated-deck.pptx`

## Deck Brief ファイルを使う

自然言語 brief の例:

- `sample-deck-brief.md`

構造化 brief の例:

- `sample-deck-brief.json`

brief を source として渡す例:

```bash
python py-generate-from-prompt.py --mock --prompt "Turn this brief into an 8-slide product deck" --source sample-deck-brief.md
```

## 生成済み Deck を改訂する

最初の deck を作成した後で改訂できます。

```bash
python py-revise-deck.py --mock --deck output/py-generated-deck.json --prompt "Compress this deck to 6 slides and make it more conclusion-driven"
```

想定される出力:

- `output/py-revised-deck.json`
- `output/py-revised-deck.pptx`

## JSON Skill の例

別のエージェントやスクリプトからファイルベースで統合したい場合:

```bash
python py-agent-skill.py --request sample-agent-request.json --response output/py-agent-response.json
```

確認するファイル:

- `sample-agent-request.json`
- `output/py-agent-response.json`

## HTTP の例

ローカルサービスを起動します。

```bash
python py-skill-server.py
```

リクエスト例:

```bash
curl -X POST http://localhost:3010/skill -H "Content-Type: application/json" --data @sample-http-request.json
```

## どの例から始めるべきか

- Claude Desktop、Cursor、または Windsurf を使用している場合は MCP から —— 最も簡単です
- 最短で成功させたいなら `sample-source-brief.md`
- deck brief の形を理解したいなら `sample-deck-brief.md`
- 他の agent ワークフローに組み込みたいなら `sample-agent-request.json`
- ローカルサービス呼び出しを使いたいなら `sample-http-request.json`

## MCP の例（Claude Desktop / Cursor / Windsurf）

MCP を設定した後（[統合ガイド](INTEGRATION_GUIDE.ja.md)を参照）、AI アシスタントに直接聞いてください：

> 幹部向けの AI ワークスペース戦略デッキを 8 スライドで作成してください。sample-source-brief.md をソースとして使ってください

アシスタントは自動的に `create_deck` を呼び出します。改訂時は：

> 5 スライドに圧縮して、結論重視にしてください

アシスタントは前に生成したデッキで `revise_deck` を呼び出します。

MCP 開発インスペクターでテスト：

```bash
mcp dev mcp_server.py
```

### リモート MCP（Streamable HTTP）

```bash
python mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8080
```

MCP クライアントから `http://<server-host>:8080/mcp` に接続してください。

## Docker の例

Docker Compose でビルド・起動：

```bash
export OPENAI_API_KEY="sk-..."
docker compose up --build
curl http://localhost:5000/health
```

またはワンショット生成：

```bash
docker run --rm -e OPENAI_API_KEY -v $(pwd)/output:/app/output auto-ppt-prototype \
  python py-generate-from-prompt.py --mock --prompt "8スライドのAI戦略デッキを作成"
```
