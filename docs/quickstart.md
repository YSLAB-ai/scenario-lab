# Scenario Lab Quickstart

## 1. Create the local environment

```bash
PYTHON=/path/to/python3.12
"$PYTHON" -m venv packages/core/.venv
source packages/core/.venv/bin/activate
pip install -e 'packages/core[dev]'
```

## 2. Run the built-in demo

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli demo-run --root .forecast
```

## 3. Inspect the generated artifacts

```bash
ls .forecast/runs/demo-run
cat .forecast/runs/demo-run/report.md
cat .forecast/runs/demo-run/workbench.md
```
