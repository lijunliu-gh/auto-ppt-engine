# ユーザーガイド

このドキュメントは、開発者ではなく利用者向けです。

このプロジェクトが今どう使えるか、どの入口を優先すべきか、どんな用途に向いているかを知りたい場合は、まずここを読んでください。

## これは何か

これは、AI エージェントから呼び出せる PowerPoint バックエンドのプロトタイプです。

現在は次の二層として理解するのが最も適切です。

- Python スマートレイヤー: planning、revise、source ingestion、agent orchestration
- JavaScript レンダラーレイヤー: deck JSON を `.pptx` に変換

つまり:

`requirements + source material -> Python planning -> deck JSON -> Node rendering -> PPTX`

## 向いている場面

現時点では次のような用途に向いています。

- 製品戦略プレゼン
- 経営層向けレビュー資料
- 営業提案 deck
- プロジェクト振り返り deck
- 研修資料の初稿
- 公式サイト、PDF、DOCX、Markdown brief に基づくプレゼン生成
- 初稿を作ってから複数回改訂するワークフロー

## まず何を使うべきか

既定では Python エントリーポイントを使ってください。

最もよく使うコマンド:

```bash
npm run generate:source
npm run skill:create
npm run revise:mock
npm run skill:server
```

これらの npm スクリプトは現在 Python スマートレイヤーを使います。

## 今できること

### 1. 既存 JSON から直接 PPT を生成

```bash
npm run generate
```

### 2. 自然言語プロンプトから PPT を生成

```bash
npm run generate:mock
```

モデル設定がある場合は次も使えます。

```bash
npm run generate:prompt
```

Python を直接使う例:

```bash
python py-generate-from-prompt.py --prompt "Create an 8-slide AI product strategy deck for executives in a professional tone"
```

### 3. ソース資料付きで PPT を生成

```bash
npm run generate:source
```

独自資料を渡す例:

```bash
python py-generate-from-prompt.py --mock --prompt "Create an 8-slide strategy deck" --source your-brief.md --source https://example.com/product
```

### 4. 既存 deck を改訂

```bash
npm run revise:mock
```

### 5. 別のエージェントから skill として使う

```bash
npm run skill:create
npm run skill:revise
```

### 6. HTTP サービスとして使う

```bash
npm run skill:server
curl http://localhost:3010/health
curl -X POST http://localhost:3010/skill -H "Content-Type: application/json" --data @sample-http-request.json
```

## ソース資料の扱い

対応しているソース種別:

- ローカルテキストファイル: `txt`、`md`、`csv`、`json`、`yaml`、`xml`
- ローカル HTML
- ローカル PDF
- ローカル DOCX
- 画像ファイル参照
- HTTP / HTTPS URL

既定では:

- スライド本文にはソースを表示しない
- presenter notes にはソースを表示する
- スライドごとのソースは構造化メタデータにも保持する

## 推奨ワークフロー

比較的厳密なプレゼンを作るなら、プロンプトだけに頼らないでください。

より良い流れは次のとおりです。

1. プレゼンの目的を明確にする
2. ソース資料を渡す
3. 初稿を生成する
4. 1 回から 3 回ほど改訂する

## 最初に試す 3 つのコマンド

```bash
npm run generate:source
npm run skill:create
npm run revise:mock
```

## 主なファイルの役割

### 利用者にとって重要なファイル

- `README.md`
- `PRODUCT.en.md`
- `sample-input.json`
- `sample-source-brief.md`
- `sample-agent-request.json`
- `sample-agent-revise-request.json`
- `sample-http-request.json`

### 主要実行ファイル

- `py-generate-from-prompt.py`
- `py-revise-deck.py`
- `py-agent-skill.py`
- `py-skill-server.py`
- `generate-ppt.js`

### 互換ラッパー

- `generate-from-prompt.js`
- `revise-deck.js`
- `agent-skill.js`
- `skill-server.js`

## まだ弱い部分

このプロジェクトは完全なプロトタイプの流れを通せますが、まだ本番品質の製品ではありません。

現在の弱点は次のとおりです。

- 完全な research agent ではない
- OCR とマルチモーダル理解は未完成
- スライド単位のソース結び付けはまだ粗い
- ブランドテンプレートと見た目の制御はまだ基本的
- 複雑なケースでは上流モデルとエージェント品質への依存が大きい

## 一行まとめ

現時点でこのプロジェクトは次の流れを実行できます。

- `prompt -> deck -> pptx`
- `prompt + sources -> deck -> pptx`
- `existing deck + revise prompt -> revised deck -> pptx`
- `agent request -> skill response`
- `HTTP request -> generated PPT artifacts`