# Scenario Lab

🌐 Languages: [English](README.md) | [中文](README.zh-CN.md) | [Español](README.es.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

> Vista previa experimental: simulación Monte Carlo de eventos reales que puedes ejecutar localmente con Codex o Claude.

Language: Español

This translation is provided for convenience. The English README is canonical for product scope, license terms, disclaimers, and release details.

Scenario Lab es un Monte Carlo simulation engine para eventos reales, como conflictos regionales, mercados, política y decisiones empresariales. Es una herramienta experimental de investigación, no un producto de predicción y not financial advice.

Version: `v0.1.0` public preview. Contributors: [CONTRIBUTORS.md](CONTRIBUTORS.md).

![Scenario Lab workflow](docs/assets/scenario-lab-workflow.png)

## Qué es

Scenario Lab convierte una situación en desarrollo en una simulación estructurada. Tú defines los actores, el desarrollo actual y la evidencia que quieres aprobar. Después explora futuros ramificados con Monte Carlo tree search y clasifica las ramas encontradas.

Cómo funciona:

- Un domain pack define actores, fases y acciones para un tipo de evento, como interstate crisis, market shock o company decision.
- El evidence packet aprobado y el encuadre del caso se compilan en un belief state con actor behavior profiles y campos específicos del dominio.
- El simulation engine ejecuta `mcts`, propone acciones, muestrea transiciones y puntúa ramas.
- Los reportes convierten las ramas en outcomes, scenario families y calibrated confidence labels legibles.

## Inicio rápido

La guía completa está en [docs/quickstart.md](docs/quickstart.md). Instalación local mínima:

```bash
git clone git@github.com:YSLAB-ai/scenario-lab.git
cd scenario-lab
PYTHON=/path/to/python3.12
"$PYTHON" -m venv packages/core/.venv
source packages/core/.venv/bin/activate
pip install -e 'packages/core[dev]'
scenario-lab demo-run --root .forecast
```

Deberías ver `demo-run complete` y artefactos en `.forecast/runs/demo-run`.

Ejemplo con lenguaje natural:

```bash
scenario-lab scenario --root .forecast "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days"
```

Scenario Lab está preparado para:

- `Codex`: [docs/install-codex.md](docs/install-codex.md)
- `Claude Code`: [docs/install-claude-code.md](docs/install-claude-code.md)

Comando de proyecto en Claude Code:

```text
/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days
```

## Flujo de trabajo y demo

Una ejecución normal pasa por estas fases:

![Scenario Lab runtime workflow](docs/assets/scenario-lab-runtime-workflow.png)

1. `intake`: entender el problema, identificar actores principales y fijar el horizonte temporal.
2. `evidence`: revisar terceros relevantes, evidencia faltante y fuentes posibles.
3. `approval`: bloquear configuración, supuestos y evidencia antes de la búsqueda.
4. `simulation`: explorar rutas con deterministic Monte Carlo tree search.
5. `report`: mostrar outcomes principales, explicar ramas y permitir actualizaciones.

El ejemplo verificado `U.S.-Iran` está en [docs/demo-us-iran.md](docs/demo-us-iran.md). Esa ejecución usó `10000` iterations y generó `133` nodes y `111` transposition hits. El `interstate-crisis` pack actual modela bounded crisis paths y no incluye full-scale war como terminal outcome explícito.

## Qué lo hace útil

Scenario Lab no trata todas las ramas como igualmente plausibles. La búsqueda se guía por domain rules, actor behavior profiles y la evidencia aprobada.

- Las acciones están restringidas por domain packs.
- La evidencia cambia actor profiles y campos del dominio.
- Las consecuencias negativas aguas abajo penalizan la clasificación.
- Mejor evidencia y mejor domain knowledge suelen producir ramas más diferenciadas.

Para que un AI agent mejore un domain pack débil, indícale [docs/domain-pack-enrichment.md](docs/domain-pack-enrichment.md).

## Límites actuales

Consulta [docs/limitations.md](docs/limitations.md).

- La calidad depende mucho del evidence packet aprobado.
- La calidad depende mucho de la profundidad del domain pack.
- Replay coverage, evidence quality y domain knowledge mejoran mediante contribuciones de la comunidad.
- OCR-backed PDF ingestion está diferido en esta public preview.

## Licencia y descargo

Scenario Lab usa [PolyForm Noncommercial License 1.0.0](LICENSE). El repositorio público es para uso no comercial, no para despliegue comercial o reventa.

Required Notice: Copyright Heuristic Search Group LLC

Este repositorio es para uso experimental, educativo y de investigación. No es un prediction product, no garantiza eventos futuros y no sustituye juicio profesional, decisiones de inversión ni decisiones operativas. It is not financial advice.

El software se proporciona `as is`, sin garantía. En la medida permitida por la ley, Heuristic Search Group LLC no responde por pérdidas financieras, pérdidas de trading, pérdidas operativas u otros daños. Revisa [LICENSE](LICENSE), [NOTICE](NOTICE) y [docs/limitations.md](docs/limitations.md).

## Otros enlaces

- English canonical README: [README.md](README.md)
- quickstart: [docs/quickstart.md](docs/quickstart.md)
- workflow: [docs/natural-language-workflow.md](docs/natural-language-workflow.md)
- demo: [docs/demo-us-iran.md](docs/demo-us-iran.md)
- contributors: [CONTRIBUTORS.md](CONTRIBUTORS.md)
- release notes: [docs/release-notes/public-preview.md](docs/release-notes/public-preview.md)
