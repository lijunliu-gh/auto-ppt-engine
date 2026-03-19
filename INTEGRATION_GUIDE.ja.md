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
4. ユーザーが修正を求めたら、上流エージェントが revise フローを再度呼ぶ

## 現在サポートされている統合方式

## 1. CLI 統合

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
python py-generate-from-prompt.py --mock --prompt "Create an 8-slide product strategy deck" --source sample-source-brief.md
```

### Revise

```bash
python py-revise-deck.py --deck output/generated-deck.json --prompt "Compress this deck to 6 slides"
```

### Agent skill request mode

```bash
python py-agent-skill.py --request sample-agent-request.json --response output/py-agent-response.json
```

## 2. JSON Skill 統合

これは現在、エージェントワークフローに最も適した方法の一つです。

必要なのは次の 3 ステップだけです。

1. request JSON を書く
2. `py-agent-skill.py` を呼ぶ
3. response JSON を読む

### Create request 形式

```json
{
  "action": "create",
  "prompt": "Create an 8-slide AI agent product strategy deck for executives in a professional tone",
  "mock": true,
  "research": false,
  "engine": "python-smart-layer",
  "contextFiles": [],
  "sources": [
    {
      "path": "sample-source-brief.md",
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
  "prompt": "Compress this deck, make it more conclusion-driven, and emphasize the execution plan",
  "mock": true,
  "research": false,
  "engine": "python-smart-layer",
  "deckPath": "output/generated-deck.json",
  "contextFiles": [],
  "sources": [
    {
      "path": "sample-source-brief.md",
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
python py-agent-skill.py --request sample-agent-request.json --response output/py-agent-response.json
```

### Response 形式

```json
{
  "ok": true,
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

## 3. HTTP 統合

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
curl -X POST http://localhost:3010/skill -H "Content-Type: application/json" --data @sample-http-request.json
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

## 互換性メモ

`generate-from-prompt.js`、`revise-deck.js`、`agent-skill.js`、`skill-server.js` は後方互換のために残っていますが、現在は Python スマートレイヤーへ転送します。新しい統合では Python を主エントリーポイントとして扱ってください。

## 2. 画像は現在「参照」であり、真の視覚理解ではない

画像はソースパイプラインには入れられますが、このリポジトリ自身が完全な OCR や画像推論を行うわけではありません。

## 3. スライド単位ソースはあるが、attribution はまだ粗い

deck 出力にはすでに次が含まれます。

- `slides[].sources`

ただし、まだ次までは対応していません。

- 特定の bullet がどの source fragment に対応するか
- 特定の chart 点がどのデータ断片に対応するか

## 4. レイアウトとブランド制御はまだプロトタイプ段階

企業向けの高度なテンプレート制御が必要なら、まだ追加実装が必要です。

## 重要ファイル

- `agent-skill.js`: JSON skill エントリーポイント
- `skill-server.js`: HTTP サービスエントリーポイント
- `skill-manifest.json`: skill 契約
- `generate-from-prompt.js`: create CLI
- `revise-deck.js`: revise CLI
- `source-loader.js`: ソース読み込み層
- `deck-agent-core.js`: planning 中核
- `generate-ppt.js`: PPT レンダラー
- `deck-schema.json`: deck schema 契約

## 一行アドバイス

今すぐ統合するなら、最も安定した道は次です。

**まず JSON skill モードで接続し、サービス型統合が必要になった時点で HTTP モードに上げることです。**