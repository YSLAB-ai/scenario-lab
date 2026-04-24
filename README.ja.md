# Scenario Lab

🌐 Languages: [English](README.md) | [中文](README.zh-CN.md) | [Español](README.es.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

> 実験的プレビュー：Codex または Claude でローカル実行できる、実世界イベント向け Monte Carlo シミュレーションツールです。

Language: 日本語

This translation is provided for convenience. The English README is canonical for product scope, license terms, disclaimers, and release details.

Scenario Lab は、地域紛争、市場ストレス、政治交渉、企業判断などの実世界イベントに使う Monte Carlo simulation engine です。研究用の実験ツールであり、prediction product ではなく、not financial advice です。

Version: `v0.1.0` public preview. Contributors: [CONTRIBUTORS.md](CONTRIBUTORS.md).

![Scenario Lab workflow](docs/assets/scenario-lab-workflow.png)

## 概要

Scenario Lab は、進行中の状況を構造化されたシミュレーション実行に変換します。利用者は actors、current development、承認する evidence を指定します。その後、Monte Carlo tree search で複数の分岐未来を探索し、見つかった branches を順位付けします。

基本的な仕組み：

- domain pack は interstate crisis、market shock、company decision などのイベント種別ごとに actors、phases、action space を定義します。
- 承認済み evidence packet と case framing は、actor behavior profiles と domain-specific fields を含む belief state にコンパイルされます。
- simulation engine はその状態で `mcts` を実行し、actions を提案し、transitions をサンプリングし、branches を採点します。
- reports は検索された branches を読みやすい outcomes、scenario families、calibrated confidence labels に変換します。

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

![Scenario Lab runtime workflow](docs/assets/scenario-lab-runtime-workflow.png)

1. `intake`: 問題を理解し、主要 actors と time horizon を設定します。
2. `evidence`: 重要な第三者、足りない evidence、取り込む sources を確認します。
3. `approval`: search の前に設定、assumptions、evidence を固定します。
4. `simulation`: deterministic Monte Carlo tree search で可能な paths を探索します。
5. `report`: 上位 outcomes と branches の説明を表示し、状況更新を続けられるようにします。

検証済みの `U.S.-Iran` 例は [docs/demo-us-iran.md](docs/demo-us-iran.md) にあります。この実行は `10000` iterations を使い、`133` nodes と `111` transposition hits を生成しました。現在の `interstate-crisis` pack は bounded crisis paths をモデル化し、full-scale war を明示的な terminal outcome としてはモデル化していません。

## 有効性の理由

Scenario Lab は、すべての branch を同じ確からしさとして扱いません。branch search は domain rules、actor behavior profiles、承認済み evidence によって形作られます。

- actions は domain packs によって制約されます。
- evidence は actor profiles と domain fields に影響します。
- downstream の negative consequences は ranking で不利に扱われます。
- evidence と domain knowledge が強いほど、branch differentiation は改善しやすくなります。

AI agent に薄い domain pack を改善させる場合は、[docs/domain-pack-enrichment.md](docs/domain-pack-enrichment.md) を読ませてください。

## 現在の制限

[docs/limitations.md](docs/limitations.md) を参照してください。

- 出力品質は承認済み evidence packet に大きく依存します。
- 出力品質は domain pack の深さと品質に大きく依存します。
- replay coverage、evidence quality、domain knowledge は community contributions によって改善されます。
- OCR-backed PDF ingestion は現在の public preview では意図的に延期されています。

## ライセンスと免責

Scenario Lab は [PolyForm Noncommercial License 1.0.0](LICENSE) で提供されています。公開リポジトリは非商用利用向けであり、商用デプロイや再販売には使えません。

Required Notice: Copyright Heuristic Search Group LLC

このリポジトリは実験、教育、研究目的のものです。prediction product ではなく、将来の出来事を保証せず、専門的判断、投資判断、運用上の意思決定を代替しません。It is not financial advice.

ソフトウェアは `as is` で提供され、保証はありません。法律で許される範囲で、Heuristic Search Group LLC は金融損失、取引損失、運用損失、その他の損害について責任を負いません。[LICENSE](LICENSE)、[NOTICE](NOTICE)、[docs/limitations.md](docs/limitations.md) を確認してください。

## その他のリンク

- English canonical README: [README.md](README.md)
- quickstart: [docs/quickstart.md](docs/quickstart.md)
- workflow: [docs/natural-language-workflow.md](docs/natural-language-workflow.md)
- demo: [docs/demo-us-iran.md](docs/demo-us-iran.md)
- contributors: [CONTRIBUTORS.md](CONTRIBUTORS.md)
- release notes: [docs/release-notes/public-preview.md](docs/release-notes/public-preview.md)
