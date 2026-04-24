# Scenario Lab

🌐 Languages: [English](README.md) | [中文](README.zh-CN.md) | [Español](README.es.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

> 실험적 프리뷰: Codex 또는 Claude로 로컬에서 실행할 수 있는 실제 사건 Monte Carlo 시뮬레이션 도구입니다.

Language: 한국어

This translation is provided for convenience. The English README is canonical for product scope, license terms, disclaimers, and release details.

Scenario Lab은 지역 분쟁, 시장 스트레스, 정치적 협상, 기업 의사결정 같은 실제 사건을 위한 Monte Carlo simulation engine입니다. 연구용 실험 도구이며 prediction product가 아니고 not financial advice입니다.

Version: `v0.1.0` public preview. Contributors: [CONTRIBUTORS.md](CONTRIBUTORS.md).

![Scenario Lab workflow](docs/assets/scenario-lab-workflow.png)

## 무엇인가

Scenario Lab은 전개 중인 상황을 구조화된 시뮬레이션 실행으로 바꿉니다. 사용자는 주요 행위자, 현재 전개, 승인할 증거를 제공합니다. 엔진은 Monte Carlo tree search로 여러 갈래의 미래를 탐색하고 찾은 분기를 순위화합니다.

작동 방식:

- domain pack은 interstate crisis, market shock, company decision 같은 사건 유형의 actors, phases, action space를 정의합니다.
- 승인된 evidence packet과 case framing은 actor behavior profiles 및 domain-specific fields가 포함된 belief state로 컴파일됩니다.
- simulation engine은 해당 상태에서 `mcts`를 실행하고 actions, transitions, branch scores를 계산합니다.
- reports는 검색된 branches를 읽기 쉬운 outcomes, scenario families, calibrated confidence labels로 변환합니다.

## 빠른 시작

전체 첫 사용 흐름은 [docs/quickstart.md](docs/quickstart.md)에 있습니다. 최소 로컬 설치:

```bash
git clone git@github.com:YSLAB-ai/scenario-lab.git
cd scenario-lab
PYTHON=/path/to/python3.12
"$PYTHON" -m venv packages/core/.venv
source packages/core/.venv/bin/activate
pip install -e 'packages/core[dev]'
scenario-lab demo-run --root .forecast
```

`demo-run complete`가 표시되고 `.forecast/runs/demo-run` 아래에 결과물이 생성됩니다.

자연어 시작 예시:

```bash
scenario-lab scenario --root .forecast "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days"
```

Scenario Lab은 다음 환경에서 사용할 수 있습니다.

- `Codex`: [docs/install-codex.md](docs/install-codex.md)
- `Claude Code`: [docs/install-claude-code.md](docs/install-claude-code.md)

Claude Code 프로젝트 명령:

```text
/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days
```

## 워크플로와 데모

일반적인 실행은 다음 단계를 거칩니다.

![Scenario Lab runtime workflow](docs/assets/scenario-lab-runtime-workflow.png)

1. `intake`: 문제를 이해하고 주요 행위자와 시간 범위를 정합니다.
2. `evidence`: 관련 제3자, 부족한 증거, 가져올 수 있는 자료를 검토합니다.
3. `approval`: 검색 전에 설정, assumptions, evidence를 고정합니다.
4. `simulation`: deterministic Monte Carlo tree search로 가능한 경로를 탐색합니다.
5. `report`: 주요 outcomes와 branch 설명을 보여주고 상황 업데이트를 이어갈 수 있게 합니다.

검증된 `U.S.-Iran` 예시는 [docs/demo-us-iran.md](docs/demo-us-iran.md)에 있습니다. 이 실행은 `10000` iterations를 사용했고 `133` nodes와 `111` transposition hits를 생성했습니다. 현재 `interstate-crisis` pack은 bounded crisis paths를 모델링하며 full-scale war를 명시적 terminal outcome으로 모델링하지 않습니다.

## 효과적인 이유

Scenario Lab은 모든 branch를 동일하게 그럴듯하다고 보지 않습니다. branch search는 domain rules, actor behavior profiles, 승인된 evidence에 의해 형성됩니다.

- 행동은 domain packs로 제한됩니다.
- evidence는 actor profiles와 domain fields에 영향을 줍니다.
- 부정적 downstream consequences는 ranking에서 불리하게 작용합니다.
- 더 강한 evidence와 domain knowledge는 보통 branch differentiation을 개선합니다.

AI agent가 얇은 domain pack을 개선하게 하려면 [docs/domain-pack-enrichment.md](docs/domain-pack-enrichment.md)를 따르게 하세요.

## 현재 한계

[docs/limitations.md](docs/limitations.md)를 확인하세요.

- 출력 품질은 승인된 evidence packet에 크게 의존합니다.
- 출력 품질은 domain pack의 깊이와 품질에 크게 의존합니다.
- replay coverage, evidence quality, domain knowledge는 커뮤니티 기여로 개선됩니다.
- OCR-backed PDF ingestion은 현재 public preview에서 의도적으로 연기되어 있습니다.

## 라이선스와 면책

Scenario Lab은 [PolyForm Noncommercial License 1.0.0](LICENSE)로 제공됩니다. 공개 저장소는 비상업적 사용을 위한 것이며 상업적 배포나 재판매에는 사용할 수 없습니다.

Required Notice: Copyright Heuristic Search Group LLC

이 저장소는 실험, 교육, 연구 용도입니다. prediction product가 아니며 미래 사건을 보장하지 않고 전문적 판단, 투자 판단, 운영 의사결정을 대체하지 않습니다. It is not financial advice.

소프트웨어는 `as is`로 제공되며 보증이 없습니다. 법이 허용하는 범위에서 Heuristic Search Group LLC는 금융 손실, 거래 손실, 운영 손실 또는 기타 손해에 대해 책임지지 않습니다. [LICENSE](LICENSE), [NOTICE](NOTICE), [docs/limitations.md](docs/limitations.md)를 확인하세요.

## 기타 링크

- English canonical README: [README.md](README.md)
- quickstart: [docs/quickstart.md](docs/quickstart.md)
- workflow: [docs/natural-language-workflow.md](docs/natural-language-workflow.md)
- demo: [docs/demo-us-iran.md](docs/demo-us-iran.md)
- contributors: [CONTRIBUTORS.md](CONTRIBUTORS.md)
- release notes: [docs/release-notes/public-preview.md](docs/release-notes/public-preview.md)
