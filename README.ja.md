# Scenario Lab

🌐 Languages: [English](README.md) | [中文](README.zh-CN.md) | [Español](README.es.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

> 実験的プレビュー：Codex または Claude でローカル実行できる、実世界イベント向けモンテカルロ・シミュレーションツールです。

言語：日本語

この翻訳は読みやすさのために提供されています。English README is canonical であり、製品範囲、ライセンス条件、免責事項、リリース詳細は英語 README が基準です。

Scenario Lab は、地域紛争、市場ストレス、政治交渉、企業判断などの実世界イベントに使うモンテカルロ・シミュレーションエンジンです。研究用の実験ツールであり、予測製品ではなく、金融助言ではありません。

バージョン：`v0.1.0` 公開プレビュー。貢献者：[CONTRIBUTORS.md](CONTRIBUTORS.md)。

![Scenario Lab ワークフロー](docs/assets/scenario-lab-workflow.png)

## 概要

Scenario Lab は、進行中の状況を構造化されたシミュレーション実行に変換します。利用者は主要な行為者、現在の展開、承認する証拠を指定します。その後、モンテカルロ木探索で複数の分岐未来を探索し、見つかった分岐を順位付けします。

基本的な仕組み：

- ドメインパックは国家間危機、市場ショック、企業判断などのイベント種別ごとに、行為者、段階、行動空間を定義します。
- 承認済みの証拠パケットとケースの枠組みは、行為者の行動プロファイルとドメイン固有フィールドを含む信念状態にコンパイルされます。
- シミュレーションエンジンはその状態で `mcts` を実行し、行動を提案し、状態遷移をサンプリングし、分岐を採点します。
- レポートは探索された分岐を、読みやすい結果、シナリオ群、校正済み信頼度ラベルに変換します。

同じ実行環境は地域紛争、市場ストレス、政治交渉、企業対応に使えます。各ドメインパックが異なるルールと状態フィールドを持つためです。

## クイックスタート

初回利用の完全な流れは [docs/quickstart.md](docs/quickstart.md) にあります。最短のローカルセットアップ：

```bash
git clone git@github.com:YSLAB-ai/scenario-lab.git
cd scenario-lab
PYTHON=/path/to/python3.12
"$PYTHON" -m venv packages/core/.venv
source packages/core/.venv/bin/activate
pip install -e 'packages/core[dev]'
scenario-lab demo-run --root .forecast
```

`demo-run complete` が表示され、`.forecast/runs/demo-run` に成果物が作成されます。

自然言語での開始例：

```bash
scenario-lab scenario --root .forecast "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days"
```

Scenario Lab は次の環境で利用できます。

- `Codex`: [docs/install-codex.md](docs/install-codex.md)
- `Claude Code`: [docs/install-claude-code.md](docs/install-claude-code.md)

Claude Code のプロジェクトコマンド：

```text
/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days
```

## ワークフローとデモ

通常の実行は次の段階を通ります。

![Scenario Lab 実行ワークフロー](docs/assets/scenario-lab-runtime-workflow.png)

1. `intake`: 問題を理解し、主要な行為者と時間範囲を設定します。
2. `evidence`: 重要な第三者、足りない証拠、取り込む資料を確認します。
3. `approval`: 探索の前に設定、仮定、証拠を固定します。
4. `simulation`: 決定的なモンテカルロ木探索で可能な経路を探索します。
5. `report`: 上位結果と分岐の説明を表示し、状況更新を続けられるようにします。

検証済みの `U.S.-Iran` 例は [docs/demo-us-iran.md](docs/demo-us-iran.md) にあります。この実行は `10000` 回の反復を使い、`133` 個のノードと `111` 回の転置ヒットを生成しました。現在の国家間危機ドメインパックは限定的な危機経路をモデル化し、全面戦争を明示的な最終結果としてはモデル化していません。

## 有効性の理由

Scenario Lab は、すべての分岐を同じ確からしさとして扱いません。分岐探索はドメインルール、行為者の行動プロファイル、承認済み証拠によって形作られます。

- 行動はドメインパックによって制約されます。
- 証拠は行為者プロファイルとドメインフィールドに影響します。
- 下流の負の結果は順位付けで不利に扱われます。
- 証拠とドメイン知識が強いほど、分岐の区別は改善しやすくなります。

AI エージェントに薄いドメインパックを改善させる場合は、[docs/domain-pack-enrichment.md](docs/domain-pack-enrichment.md) を読ませてください。

## 現在の制限

[docs/limitations.md](docs/limitations.md) を参照してください。

- 出力品質は承認済み証拠パケットに大きく依存します。
- 出力品質はドメインパックの深さと品質に大きく依存します。
- 履歴再実行の範囲、証拠品質、ドメイン知識はコミュニティの貢献によって改善されます。
- OCR ベースの PDF 取り込みは現在の公開プレビューでは意図的に延期されています。

## ライセンスと免責

Scenario Lab は [PolyForm Noncommercial License 1.0.0](LICENSE) で提供されています。公開リポジトリは非商用利用向けであり、商用デプロイや再販売には使えません。

Required Notice: Copyright Heuristic Search Group LLC

このリポジトリは実験、教育、研究目的のものです。予測製品ではなく、将来の出来事を保証せず、専門的判断、投資判断、運用上の意思決定を代替しません。金融助言ではありません。

ソフトウェアは `as is` で提供され、保証はありません。法律で許される範囲で、Heuristic Search Group LLC は金融損失、取引損失、運用損失、その他の損害について責任を負いません。[LICENSE](LICENSE)、[NOTICE](NOTICE)、[docs/limitations.md](docs/limitations.md) を確認してください。

## その他のリンク

- 英語の基準 README: [README.md](README.md)
- クイックスタート: [docs/quickstart.md](docs/quickstart.md)
- ワークフロー: [docs/natural-language-workflow.md](docs/natural-language-workflow.md)
- デモ: [docs/demo-us-iran.md](docs/demo-us-iran.md)
- 貢献者: [CONTRIBUTORS.md](CONTRIBUTORS.md)
- リリースノート: [docs/release-notes/public-preview.md](docs/release-notes/public-preview.md)
