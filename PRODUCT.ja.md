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
- deck JSON の validation
- Node renderer による PPTX 出力
- エージェントから呼び出せる JSON request / response フロー
- ローカル HTTP skill エンドポイント

## 現在の公開エントリーポイント

推奨される主要エントリーポイント:

- `py-generate-from-prompt.py`
- `py-revise-deck.py`
- `py-agent-skill.py`
- `py-skill-server.py`

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
- より強いテーマとテンプレート対応
- より良いレイアウト品質とタイポグラフィ制御
- 自動テスト
- ホスティング運用向けのハードニング

## 推奨されるオープンソースの説明

推奨 GitHub description:

> Open-source PowerPoint backend for AI agents using a Python smart layer for planning and a JavaScript renderer for PPTX output.