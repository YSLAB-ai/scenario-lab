# Scenario Lab

🌐 Languages: [English](README.md) | [中文](README.zh-CN.md) | [Español](README.es.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

> 实验性预览版：可在本地用 Codex 或 Claude 运行的真实事件蒙特卡洛模拟工具。

语言：中文

本译文仅为方便阅读而提供。English README is canonical，其内容以英文版为准，包括产品范围、许可证条款、免责声明和发布细节。

Scenario Lab 是一个用于真实事件的蒙特卡洛模拟引擎，适用于地区冲突、市场压力、政治博弈和公司决策等场景。它是实验性研究工具，不是预测产品，也不是金融建议。

版本：`v0.1.0` 公开预览版。贡献者：[CONTRIBUTORS.md](CONTRIBUTORS.md)。

![Scenario Lab 工作流](docs/assets/scenario-lab-workflow.png)

## 它是什么

Scenario Lab 会把一个正在发展的情况转成结构化模拟。你提供主要参与者、当前进展和要批准的证据。系统随后用蒙特卡洛树搜索探索多个可能分支，并对找到的分支进行排序。

核心机制：

- 领域包定义某类事件的参与者、阶段和行动空间，例如国家间危机、市场冲击或公司决策。
- 已批准的证据包和场景描述会被编译成信念状态，其中包含参与者行为画像和领域专属字段。
- 模拟引擎在该状态上运行 `mcts`，提出行动、采样状态转移、并为分支评分。
- 报告会把搜索到的分支转成可读的结果、情景族和校准后的置信度标签。

同一套运行时可以用于地区冲突、市场压力、政治谈判和公司应对场景，因为不同领域包携带不同规则和状态字段。

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

你应该看到 `demo-run complete`，并在 `.forecast/runs/demo-run` 下看到生成文件。

自然语言启动示例：

```bash
scenario-lab scenario --root .forecast "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days"
```

Scenario Lab 支持：

- `Codex`：[docs/install-codex.md](docs/install-codex.md)
- `Claude Code`：[docs/install-claude-code.md](docs/install-claude-code.md)

Claude Code 项目命令：

```text
/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days
```

## 证据语料库

证据草稿默认使用本地 SQLite 数据库 `.forecast/corpus.db`。如果还没有语料库，请把相关证据文件保存到 `.forecast/evidence-candidates/`，然后运行：

```bash
scenario-lab ingest-directory --root .forecast --path .forecast/evidence-candidates --tag domain=interstate-crisis
scenario-lab draft-evidence-packet --root .forecast --run-id <run-id> --revision-id r1
```

也可以让适配器运行时批量导入推荐文件：

```bash
scenario-lab run-adapter-action --root .forecast --candidate-path .forecast/evidence-candidates --run-id <run-id> --revision-id r1 --action batch-ingest-recommended
scenario-lab run-adapter-action --root .forecast --run-id <run-id> --revision-id r1 --action draft-evidence-packet
```

只有在需要单独的证据数据库时才传入 `--corpus-db <path>`。

## 工作流和演示

一次正常运行会经过这些阶段：

![Scenario Lab 运行工作流](docs/assets/scenario-lab-runtime-workflow.png)

1. `intake`：理解问题、确定主要参与者、设定时间范围。
2. `evidence`：审查重要第三方、缺失证据和可导入资料。
3. `approval`：在搜索前锁定设定、假设和证据。
4. `simulation`：用确定性的蒙特卡洛树搜索探索可能路径。
5. `report`：展示主要结果、解释分支，并允许在局势变化后继续更新。

已验证的 `U.S.-Iran` 示例见 [docs/demo-us-iran.md](docs/demo-us-iran.md)。该运行使用 `10000` 次迭代，生成 `133` 个节点和 `111` 次转置命中。当前国家间危机领域包只建模受控危机路径，不把全面战争作为显式终局结果。

## 为什么有效

Scenario Lab 不把所有分支视为同等可能。分支搜索受领域规则、参与者行为画像和已批准证据共同约束。

- 行动由领域包约束。
- 证据会影响参与者画像和领域字段。
- 下游负面后果会在评分中受到惩罚。
- 领域知识和证据越强，分支区分度通常越好。

如果你希望 AI 代理改进薄弱的领域包，请让它阅读 [docs/domain-pack-enrichment.md](docs/domain-pack-enrichment.md)。

## 当前限制

详见 [docs/limitations.md](docs/limitations.md)。

- 输出质量高度依赖已批准证据包。
- 输出质量高度依赖领域包的深度和质量。
- 回放覆盖、证据质量和领域知识都需要社区贡献持续改进。
- 基于 OCR 的 PDF 导入功能在当前公开预览版中有意延后。

## 许可证和免责声明

Scenario Lab 使用 [PolyForm Noncommercial License 1.0.0](LICENSE)。公开仓库仅限非商业使用，不允许商业部署或转售。

Required Notice: Copyright Heuristic Search Group LLC

本仓库仅用于实验、教育和研究。它不是预测产品，不保证未来事件，不替代专业判断、投资判断或运营决策。它不是金融建议。

软件按 `as is` 提供，不含担保。在法律允许范围内，Heuristic Search Group LLC 不对金融损失、交易损失、运营损失或其他损害承担责任。请阅读 [LICENSE](LICENSE)、[NOTICE](NOTICE) 和 [docs/limitations.md](docs/limitations.md)。

## 其他入口

- 英文权威 README：[README.md](README.md)
- 快速开始：[docs/quickstart.md](docs/quickstart.md)
- 工作流：[docs/natural-language-workflow.md](docs/natural-language-workflow.md)
- 演示：[docs/demo-us-iran.md](docs/demo-us-iran.md)
- 贡献者：[CONTRIBUTORS.md](CONTRIBUTORS.md)
- 发布说明：[docs/release-notes/public-preview.md](docs/release-notes/public-preview.md)
