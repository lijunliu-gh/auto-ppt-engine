# 製品概要

## 現在の製品ポジション

Auto PPT Prototype は、AI エージェント向けのオープンソース PowerPoint バックエンドです。

現在は明確な二層構成になっています。

- Python スマートレイヤー: planning、revise、source handling、model orchestration、agent 統合
- JavaScript レンダラーレイヤー: deck JSON を `.pptx` に変換

## これは何か

本質的には、agent 向けの planning-and-rendering backend です。

想定している構成は次のとおりです。

- 上流の AI エージェントが要件収集、追加質問、資料収集、判断を行う
- このプロジェクトが deck JSON を計画または改訂し、最終的な PPTX を出力する

つまり責務分担は次のとおりです。

- 上流エージェントが research と workflow 制御を担当する
- このリポジトリが planning、revision、validation、rendering を担当する

## これは何ではないか

これ自体は完全な research agent ではありません。

また、単純な「Web 検索からスライドを作るツール」として説明すべきでもありません。

厳密な用途では、システムは次を優先すべきです。

1. 公式ソース
2. ユーザーがアップロードした資料
3. 明示的なユーザー指示
4. Web 検索は最後の補助手段

## 現在の機能

- プロンプトからの deck planning
- 自然言語指示による deck revise
- ローカルファイルと URL からの trusted source ingestion
- チャートデータ検証、無効なチャートは自動的に bullet レイアウトにフォールバック
- チャート自動修復: 無効なタイプ補正、文字列→数値変換、データ/カテゴリ長の自動調整（フォールバック前に実行）
- ソース資料から数値データを抽出しチャートヒントとして注入
- deck JSON の validation
- Node renderer による PPTX 出力
- ブランドテンプレートエンジン: .pptx テンプレートを渡してブランドに合った出力を生成（python-pptx ベース）
- デュアルレンダーパス: python-pptx（テンプレートあり）または pptxgenjs（テンプレートなし）
- MCP Server（Claude Desktop、Cursor、Windsurf 対応、`create_deck`・`revise_deck`）
- MCP リモートトランスポート: ホスト型デプロイ向けの Streamable HTTP モード（`--transport streamable-http`）
- エージェントから呼び出せる JSON request / response フロー
- ローカル HTTP skill エンドポイント
- LLM プロバイダー抽象（OpenAI、OpenRouter、Claude、Gemini、Qwen、DeepSeek、GLM、MiniMax）
- 画像アセットパイプライン: ローカル画像挿入、URL 画像、マルチエージェント連携用プレースホルダープロトコル
- セキュリティ: パストラバーサル防止、SSRF ブロック、ファイルサイズ制限、サブプロセスタイムアウト、画像拡張子ホワイトリスト
- 282 件の自動テスト（85% カバレッジ: ユニット、MCP サーバー、MCP 統合、テンプレートエンジン、画像ハンドラー、クロスモジュール）
- API バージョニング（`apiVersion: "1.0"`）をすべてのリクエストとレスポンスに含む
- CI マトリックス: Python 3.10/3.11/3.12 での pytest + Node.js 18/20/22 スモークテスト
- Docker パッケージング: Dockerfile + docker-compose.yml によるワンコマンドコンテナデプロイ

## 現在の公開エントリーポイント

推奨される主要エントリーポイント:

- `mcp_server.py`（MCP — Claude Desktop、Cursor、Windsurf に推奨）
- `py-generate-from-prompt.py`（CLI）
- `py-revise-deck.py`（CLI）
- `py-agent-skill.py`（JSON skill）
- `py-skill-server.py`（HTTP サービス）

後方互換のために残しているエントリーポイント:

- `generate-from-prompt.js`
- `revise-deck.js`
- `agent-skill.js`
- `skill-server.js`

これらの Node エントリーポイントは現在 Python スマートレイヤーへ転送します。

## なぜこの方向なのか

次のフェーズの能力は Python に置く方が自然だからです。

- より強い文書解析
- model routing と orchestration
- retrieval と source reasoning
- OCR と multimodal 拡張
- より高度な revise 品質

一方で JavaScript は既存 renderer がすでに機能しているため、安定した出力層として残しています。

## 現在のプロダクトギャップ

- 表計算や複雑な構造化資料へのより強い ingestion
- 画像とスクリーンショットの理解
- より細かな provenance tracking
- より良いレイアウト品質とタイポグラフィ制御
- ホスティング運用向けのハードニング

## 推奨されるオープンソースの説明

推奨 GitHub description:

> AI-agent-ready PowerPoint backend: plan, revise, and render PPTX decks from natural-language prompts. MCP + CLI + HTTP interfaces.