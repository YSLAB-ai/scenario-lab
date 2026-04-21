## Domain Depth Pass

Date: 2026-04-21

### Verified Scope

- Expanded evidence-conditioned modeling in:
  - `market-shock`
  - `regulatory-enforcement`
  - `supply-chain-disruption`
- Expanded replay coverage to cover:
  - `company-action`
  - `market-shock`
  - `regulatory-enforcement`

### Verified Commands

- `packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `193 passed`
- Realistic smoke campaign rerun after the deeper state-model changes

### Verified New Inferred Fields

- `market-shock`
  - `contagion_risk`
  - `policy_optionality`
- `regulatory-enforcement`
  - `remedy_severity`
  - `litigation_readiness`
- `supply-chain-disruption`
  - `supplier_concentration`
  - `customer_penalty_pressure`

### Verified Smoke Outcomes

- `Market rate shock` -> `Emergency liquidity`
- `Regulator ad-tech` -> `Internal remediation`
- `Supply rare-earth` -> `Expedite alternatives`
- `Supplier flooding` -> `Expedite alternatives`

### Remaining Gap

- The deeper field models improve causal differentiation and replay coverage, but they still rely on heuristic scoring rather than calibrated outcome probabilities or a large historical replay library.
