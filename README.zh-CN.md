# Scenario Lab

🌐 Languages: [English](README.md) | [中文](README.zh-CN.md) | [Español](README.es.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

> 实验性预览版：可在本地用 Codex 或 Claude 运行的真实事件 Monte Carlo 模拟工具。

Language: 中文

This translation is provided for convenience. The English README is canonical for product scope, license terms, disclaimers, and release details.

Scenario Lab 是一个用于真实事件的 Monte Carlo simulation engine，适用于地区冲突、市场压力、政治博弈和公司决策等场景。它是实验性研究工具，不是预测产品，也不是 financial advice。

Version: `v0.1.0` public preview. Contributors: [CONTRIBUTORS.md](CONTRIBUTORS.md).

![Scenario Lab workflow](docs/assets/scenario-lab-workflow.png)

## 它是什么

Scenario Lab 把一个正在发展的情况转成结构化模拟。你提供主要参与者、当前进展和要批准的证据。系统会用 Monte Carlo tree search 探索多个可能分支，并对分支进行排序。

核心机制：

- domain pack 定义某类事件的参与者、阶段和行动空间，例如 interstate crisis、market shock 或 company decision。
- 已批准的 evidence packet 和场景描述会被编译成 belief state，其中包含 actor behavior profiles 和领域字段。
- simulation engine 在该状态上运行 `mcts`，提出行动、采样转移、评分分支。
- report 把搜索结果转成可读的 outcomes、scenario families 和 calibrated confidence labels。

## 快速开始

完整流程见 [docs/quickstart.md](docs/quickstart.md)。最短本地安装流程：

```bash
git clone git@github.com:YSLAB-ai/scenario-lab.git
cd scenario-lab
PYTHON=/path/to/python3.12
"$PYTHON" -m venv packages/core/.venv
source packages/core/.venv/bin/activate
pip install -e 'packages/core[dev]'
scenario-lab demo-run --root .forecast
```

你应该看到 `demo-run complete`，并在 `.forecast/runs/demo-run` 下看到生成的文件。

自然语言启动示例：

```bash
scenario-lab scenario --root .forecast "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days"
```

Scenario Lab 支持：

- `Codex`: [docs/install-codex.md](docs/install-codex.md)
- `Claude Code`: [docs/install-claude-code.md](docs/install-claude-code.md)

Claude Code 项目命令：

```text
/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days
```

## 工作流和演示

一次正常运行会经过这些阶段：

![Scenario Lab runtime workflow](docs/assets/scenario-lab-runtime-workflow.png)

1. `intake`: 理解问题、确定主要参与者、设定时间范围。
2. `evidence`: 审查第三方参与者、缺失证据和可导入资料。
3. `approval`: 锁定设定、假设和证据。
4. `simulation`: 使用 deterministic Monte Carlo tree search 探索路径。
5. `report`: 展示主要 outcomes、分支解释和后续更新入口。

已验证的 `U.S.-Iran` 示例见 [docs/demo-us-iran.md](docs/demo-us-iran.md)。该运行使用 `10000` iterations，生成 `133` nodes 和 `111` transposition hits。当前 `interstate-crisis` pack 只建模 bounded crisis paths，不把 full-scale war 作为显式 terminal outcome。

## 为什么有效

Scenario Lab 不把所有分支视为同等可能。branch search 受 domain rules、actor behavior profiles 和已批准证据共同约束。

- 行动由 domain pack 约束。
- 证据会影响 actor profiles 和领域字段。
- 下游负面后果会在评分中受到惩罚。
- 领域知识和证据越强，分支区分度通常越好。

如果你希望 AI agent 改进薄弱的 domain pack，请让它阅读 [docs/domain-pack-enrichment.md](docs/domain-pack-enrichment.md)。

## 当前限制

详见 [docs/limitations.md](docs/limitations.md)。

- 输出质量高度依赖已批准证据包。
- 输出质量高度依赖 domain pack 的深度和质量。
- replay coverage、evidence quality 和 domain knowledge 都需要社区贡献持续改进。
- OCR-backed PDF ingestion 当前 public preview 中有意延后。

## 许可证和免责声明

Scenario Lab 使用 [PolyForm Noncommercial License 1.0.0](LICENSE)。公开仓库仅限非商业使用，不允许商业部署或转售。

Required Notice: Copyright Heuristic Search Group LLC

本仓库仅用于实验、教育和研究。它不是 prediction product，不保证未来事件，不替代专业判断、投资判断或运营决策。It is not financial advice.

软件按 `as is` 提供，不含担保。在法律允许范围内，Heuristic Search Group LLC 不对金融损失、交易损失、运营损失或其他损害承担责任。请阅读 [LICENSE](LICENSE)、[NOTICE](NOTICE) 和 [docs/limitations.md](docs/limitations.md)。

## 其他入口

- English canonical README: [README.md](README.md)
- quickstart: [docs/quickstart.md](docs/quickstart.md)
- workflow: [docs/natural-language-workflow.md](docs/natural-language-workflow.md)
- demo: [docs/demo-us-iran.md](docs/demo-us-iran.md)
- contributors: [CONTRIBUTORS.md](CONTRIBUTORS.md)
- release notes: [docs/release-notes/public-preview.md](docs/release-notes/public-preview.md)
