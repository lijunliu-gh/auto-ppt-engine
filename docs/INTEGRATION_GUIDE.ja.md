# 統合ガイド

このドキュメントは、統合担当者向けです。

このプロジェクトを自分の AI エージェント、ワークフローエンジン、スクリプト、バックエンドサービス、またはローカルツールチェーンに組み込みたい場合は、このファイルを重点的に読んでください。

## 統合チェーンにおけるこのプロジェクトの役割

このプロジェクトは現在、次のような役割に最も適しています。

- Python-first の PPT generation backend
- deck planning and rendering engine
- local skill service
- agent-callable PPT workflow

完全な research agent を置き換えるものではありません。代わりに、上流から渡された入力を次の成果物に変換します。

- deck JSON
- `.pptx`

推奨される利用モデルは次のとおりです。

1. 上流エージェントがユーザー要求と資料を収集する
2. 上流エージェントが Python スマートレイヤーを呼び出す
3. このプロジェクトが deck JSON と PPTX を返す
4. 納品前に生成 PPTX へ可視 QA ゲートを実行する
5. ユーザーが修正を求めたら、上流エージェントが revise フローを再度呼ぶ

## 推奨: 可視 QA ゲート

各 `create` / `revise` 実行後に次を実行します。

```bash
./auto-ppt qa-visual output/py-generated-deck.pptx --strict
```

改訂後の成果物に対しては:

```bash
./auto-ppt qa-visual output/py-revised-deck.pptx --strict
```

統合パイプラインでの効果:

- 人手レビュー前に明確なレイアウトリスクを検出
- CI/自動化向けの構造化レポートを出力（`visual-qa-report.json`）
- `--strict` で問題検出時に非 0 終了し、品質ゲートとして利用可能

## 現在サポートされている統合方式

## 1. MCP 統合（AI 環境向け推奨）

Claude Desktop、Cursor、Windsurf、またはその他の MCP 互換クライアントを使用している場合、MCP が最も簡単な統合方法です。MCP サーバーは `create_deck` と `revise_deck` をネイティブ MCP ツールとして公開し、AI アシスタントが直接呼び出せます。ファイル管理や HTTP サーバーのセットアップは不要です。

### Claude Desktop 設定

`~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）または `%APPDATA%\Claude\claude_desktop_config.json`（Windows）に追加：

```json
{
  "mcpServers": {
    "auto-ppt": {
      "command": "python",
      "args": ["/absolute/path/to/auto-ppt-engine/mcp_server.py"]
    }
  }
}
```

### Cursor / Windsurf 設定

プロジェクトルートに `.cursor/mcp.json` または `.windsurf/mcp.json` を作成：

```json
{
  "mcpServers": {
    "auto-ppt": {
      "command": "python",
      "args": ["/absolute/path/to/auto-ppt-engine/mcp_server.py"]
    }
  }
}
```

### 利用可能な MCP ツール

| ツール | パラメータ | 説明 |
|--------|-----------|------|
| `create_deck` | `prompt`（必須）、`sources`、`mock`、`research`、`output_dir` | 新しいデッキを作成 |
| `revise_deck` | `prompt`（必須）、`deck_path`（必須）、`sources`、`mock`、`research`、`output_dir` | 既存デッキを改訂 |

### Streamable HTTP トランスポート（リモートデプロイ向け）

ホスト環境やリモートデプロイでは、Streamable HTTP トランスポートが利用可能です：

```bash
python mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8080
```

MCP クライアントから `http://<server-host>:8080/mcp` に接続してください。

## 2. CLI 統合

最も簡単な方法です。次のようなケースに向いています。

- Claude Code 系ツール
- ローカル自動化スクリプト
- shell / PowerShell ワークフロー
- CI でのコマンド実行

### Create

```bash
python py-generate-from-prompt.py --prompt "Create an 8-slide product strategy deck"
```

### Create with sources

```bash
python py-generate-from-prompt.py --mock --prompt "Create an 8-slide product strategy deck" --source examples/inputs/sample-source-brief.md
```

### Revise

```bash
python py-revise-deck.py --deck output/py-generated-deck.json --prompt "Compress this deck to 6 slides"
```

### Agent skill request mode

```bash
python py-agent-skill.py --request examples/inputs/sample-agent-request.json --response output/py-agent-response.json
```

## 3. JSON Skill 統合

これは現在、エージェントワークフローに最も適した方法の一つです。

必要なのは次の 3 ステップだけです。

1. request JSON を書く
2. `py-agent-skill.py` を呼ぶ
3. response JSON を読む

### Create request 形式

```json
{
  "action": "create",
  "apiVersion": "1.0",
  "prompt": "Create an 8-slide AI agent product strategy deck for executives in a professional tone",
  "mock": true,
  "research": false,
  "engine": "python-smart-layer",
  "contextFiles": [],
  "sources": [
    {
      "path": "examples/inputs/sample-source-brief.md",
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

### Revise request 形式

```json
{
  "action": "revise",
  "apiVersion": "1.0",
  "prompt": "Compress this deck, make it more conclusion-driven, and emphasize the execution plan",
  "mock": true,
  "research": false,
  "engine": "python-smart-layer",
  "deckPath": "output/py-generated-deck.json",
  "contextFiles": [],
  "sources": [
    {
      "path": "examples/inputs/sample-source-brief.md",
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

### 呼び出し例

```bash
python py-agent-skill.py --request examples/inputs/sample-agent-request.json --response output/py-agent-response.json
```

### Response 形式

```json
{
  "ok": true,
  "apiVersion": "1.0",
  "engine": "python-smart-layer",
  "action": "create",
  "prompt": "string",
  "deckJsonPath": "absolute path",
  "pptxPath": "absolute path",
  "slideCount": 8,
  "assumptions": [],
  "sourcesUsed": []
}
```

## 4. HTTP 統合

上流システムが API 呼び出しを好む場合、このプロジェクトはローカル HTTP サービスとしても使えます。

### サービス起動

```bash
npm run skill:server
```

### ヘルスチェック

```bash
curl http://localhost:3010/health
```

### skill 呼び出し

```bash
curl -X POST http://localhost:3010/skill -H "Content-Type: application/json" --data @examples/inputs/sample-http-request.json
```

### HTTP ルート

- `GET /health`
- `POST /skill`

## 入力項目の説明

## 1. `prompt`

役割:

- プレゼンの目的を定義する
- 対象読者、トーン、枚数、用途を説明する

## 2. `contextFiles`

役割:

- 追加のコンテキスト資料を渡す

## 3. `sources`

役割:

- 信頼できる資料を渡す
- planning 前にコンテキストへ変換する
- スライド単位のソースメタデータを保持する
- 既定で presenter notes にソースを書き出す

対応ソース種別:

- text
- json
- html
- pdf
- docx
- image
- url

## 4. `mock`

役割:

- ローカル mock planner を使うかどうかを決める

## 5. `research`

役割:

- 軽量な research 補助を有効にする

現在の注意点:

- Tavily が設定されている場合のみ動作する
- 厳密な本番ワークフローでの最終的な事実根拠にはすべきではない

## deck 出力に含まれるもの

生成された deck JSON には現在次が含まれます。

- `sourceDisplayMode`
- `slides[].sources`
- `slides[].speakerNotes`

既定では:

- `sourceDisplayMode = notes`
- ソースはスライド本文には表示されない
- ソースは presenter notes に表示される
- ソースは構造化メタデータにも保持される

## 推奨される統合モデル

AI エージェントに統合するなら、最も安定した流れは次のとおりです。

1. エージェントがユーザー目標を収集する
2. エージェントが信頼できる資料を集める
3. エージェントが request JSON を組み立てる
4. `py-agent-skill.py` を呼ぶ
5. response JSON を読む
6. 生成結果をユーザーに返す
7. 必要に応じて revise を再度呼ぶ

## 統合先ごとの推奨

## Claude Code や coding-agent 系ツール向け

最適な方法:

- CLI 呼び出し
- または JSON request と `py-agent-skill.py`

## サービス型システム向け

最適な方法:

- HTTP 呼び出し

## ローカル自動化スクリプト向け

最適な方法:

- CLI モード

## 現在の境界と注意点

## 1. 完全な research agent ではない

公式サイトの発見、複数ソース比較、証拠の矛盾解消、マルチモーダル解析は上流エージェントの責務です。

## 2. 画像の挿入は可能だが、組み込みの視覚理解はない

v0.5.1 以降、レンダラーはローカル画像や URL 画像をスライドに挿入できます。ただし、このリポジトリ自体が完全な OCR や画像推論を行うわけではありません — それらは上流エージェントの責務です。

## 3. スライド単位ソースはあるが、attribution はまだ粗い

deck 出力にはすでに次が含まれます。

- `slides[].sources`

ただし、まだ次までは対応していません。

- 特定の bullet がどの source fragment に対応するか
- 特定の chart 点がどのデータ断片に対応するか

## 4. ブランドテンプレート対応 (v0.5.0)

v0.5.0 以降、`.pptx` ブランドテンプレートを渡してブランドに合った出力を生成できます：

- リクエストに `"template": "path/to/brand.pptx"` を追加
- システムはテンプレートからレイアウト、プレースホルダー、テーマカラー、フォントを抽出
- `python-pptx` を使用してテンプレートのスライドレイアウトでレンダリング
- テンプレートなしの場合は既存の JS レンダラー (pptxgenjs) を自動使用
- API レスポンスに `"renderer"` フィールド（`"python-pptx"` または `"pptxgenjs"`）を含む

## 5. 画像とビジュアルサポート (v0.5.1)

v0.5.1 以降、各スライドの `visuals` 配列は 3 種類のアイテムを受け付けます:

**プレーン文字列**（テキスト説明）:
```json
"visuals": ["市場コンテキスト図を追加"]
```

**画像オブジェクト**（ローカルパスまたは URL）:
```json
"visuals": [
  {"type": "image", "path": "assets/logo.png", "alt": "会社ロゴ", "position": "right"},
  {"type": "image", "url": "https://example.com/chart.png", "position": "center"}
]
```

**プレースホルダーオブジェクト**（後から画像生成用）:
```json
"visuals": [
  {"type": "placeholder", "prompt": "4ステッププロセスのワークフロー図", "position": "right"}
]
```

`position` 値: `right`（デフォルト）、`left`、`center`、`full`。

セキュリティ: ローカルパスはプロジェクトディレクトリ内に制限、URL 画像はプライベートネットワークを拒否（SSRF）、最大 10 MB、一般的な画像フォーマットのみ。

## 6. チャートデータの検証とフォールバック

v0.4.1 以降、システムはチャートスライドを自動検証します:

- チャートには空でない `categories` と数値 `series` データが必要
- 無効なチャートは自動的に `bullet` レイアウトにダウングレードされ、元のコンテンツは保持
- ソース資料から数値データ（パーセンテージ、通貨、指標）をスキャンし、LLM にチャートヒントとして注入
- フォールバック決定は deck の `assumptions` フィールドに記録

## 重要ファイル

- `mcp_server.py`: MCP サーバーエントリーポイント（Claude Desktop、Cursor、Windsurf）
- `py-agent-skill.py`: JSON skill エントリーポイント
- `py-skill-server.py`: HTTP サービスエントリーポイント
- `skill-manifest.json`: skill 契約
- `py-generate-from-prompt.py`: create CLI
- `py-revise-deck.py`: revise CLI
- `python_backend/source_loader.py`: ソースローディングレイヤー
- `python_backend/smart_layer.py`: コアプランニングエンジン
- `python_backend/template_engine.py`: .pptx テンプレートパーサー
- `python_backend/pptx_renderer.py`: python-pptx レンダラー（ブランドテンプレートモード）
- `python_backend/image_handler.py`: 画像解決、検証、挿入
- `generate-ppt.js`: PPT レンダラー（テンプレートなしモード）
- `deck-schema.json`: deck schema 契約

## 一行アドバイス

今すぐ統合するなら、最も安定した道は次です。

**Claude Desktop、Cursor、Windsurf を使っているなら MCP から始めてください。それ以外はまず JSON skill モードで接続し、サービス型統合が必要になった時点で HTTP モードに上げてください。**

## 5. Docker デプロイ

コンテナ化デプロイ用の `Dockerfile` と `docker-compose.yml` が含まれています。

### Docker Compose で起動

```bash
export OPENAI_API_KEY="sk-..."
docker compose up --build
```

HTTP skill サーバーがポート 5000 で起動します（Dockerfile 内の `ENV PORT=5000` で設定）。ローカル開発時のデフォルトはポート 3010 です。いずれも `PORT` 環境変数で変更できます。

### Docker で MCP サーバー

```bash
# ローカル stdio MCP
docker run --rm -it -e OPENAI_API_KEY auto-ppt-engine python mcp_server.py

# リモート Streamable HTTP MCP
docker run --rm -p 8080:8080 -e OPENAI_API_KEY auto-ppt-engine \
  python mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8080
```

**Claude Desktop、Cursor、Windsurf を使っているなら MCP から始めてください。それ以外はまず JSON skill モードで接続し、サービス型統合が必要になった時点で HTTP モードに上げてください。**

## API バージョニング

v0.6.0 以降、すべての API リクエストとレスポンスに `apiVersion` フィールドが含まれます：

- 現在の API バージョン: `"1.0"`
- リクエスト JSON に `"apiVersion": "1.0"` を含めてください（任意; サーバーは現在のバージョンをデフォルトで使用）
- すべてのレスポンス JSON に `"apiVersion": "1.0"` が含まれます

このフィールドにより、既存の統合を壊すことなく API を進化させることができます。