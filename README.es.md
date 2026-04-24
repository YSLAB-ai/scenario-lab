# Scenario Lab

🌐 Languages: [English](README.md) | [中文](README.zh-CN.md) | [Español](README.es.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

> Vista previa experimental: simulación Monte Carlo de eventos reales que puedes ejecutar localmente con Codex o Claude.

Idioma: Español

Esta traducción se ofrece para facilitar la lectura. English README is canonical; la versión inglesa rige el alcance del producto, la licencia, los avisos legales y los detalles de publicación.

Scenario Lab es un motor de simulación Monte Carlo para eventos reales, como conflictos regionales, mercados, política y decisiones empresariales. Es una herramienta experimental de investigación, no un producto predictivo y no es asesoramiento financiero.

Versión: `v0.1.0` vista previa pública. Contribuidores: [CONTRIBUTORS.md](CONTRIBUTORS.md).

![Flujo de trabajo de Scenario Lab](docs/assets/scenario-lab-workflow.png)

## Qué es

Scenario Lab convierte una situación en desarrollo en una simulación estructurada. Tú defines los actores, el desarrollo actual y la evidencia que quieres aprobar. Después explora futuros ramificados con búsqueda de árbol Monte Carlo y clasifica las ramas encontradas.

Cómo funciona:

- Un paquete de dominio define actores, fases y acciones para un tipo de evento, como crisis interestatal, choque de mercado o decisión empresarial.
- El paquete de evidencia aprobado y el encuadre del caso se compilan en un estado de creencias con perfiles de comportamiento de actores y campos específicos del dominio.
- El motor de simulación ejecuta `mcts`, propone acciones, muestrea transiciones de estado y puntúa ramas.
- Los informes convierten las ramas exploradas en resultados, familias de escenarios y etiquetas de confianza calibrada.

El mismo entorno puede usarse para conflicto regional, tensión de mercado, negociación política y respuesta empresarial porque cada paquete de dominio contiene reglas y campos de estado distintos.

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

![Flujo de ejecución de Scenario Lab](docs/assets/scenario-lab-runtime-workflow.png)

1. `intake`: entender el problema, identificar actores principales y fijar el horizonte temporal.
2. `evidence`: revisar terceros relevantes, evidencia faltante y fuentes que podrían incorporarse.
3. `approval`: bloquear configuración, supuestos y evidencia antes de la búsqueda.
4. `simulation`: explorar rutas posibles con búsqueda de árbol Monte Carlo determinista.
5. `report`: mostrar los resultados principales, explicar las ramas y permitir actualizaciones.

El ejemplo verificado `U.S.-Iran` está en [docs/demo-us-iran.md](docs/demo-us-iran.md). Esa ejecución usó `10000` iteraciones y generó `133` nodos y `111` aciertos de transposición. El paquete de dominio de crisis interestatal actual modela rutas de crisis acotada y no incluye guerra total como resultado final explícito.

## Qué lo hace útil

Scenario Lab no trata todas las ramas como igualmente plausibles. La búsqueda de ramas se guía por reglas de dominio, perfiles de comportamiento de actores y evidencia aprobada.

- Las acciones están restringidas por paquetes de dominio.
- La evidencia cambia los perfiles de actores y los campos del dominio.
- Las consecuencias negativas posteriores penalizan la clasificación.
- Mejor evidencia y mejor conocimiento de dominio suelen producir ramas más diferenciadas.

Para que un agente de IA mejore un paquete de dominio débil, indícale [docs/domain-pack-enrichment.md](docs/domain-pack-enrichment.md).

## Límites actuales

Consulta [docs/limitations.md](docs/limitations.md).

- La calidad depende mucho del paquete de evidencia aprobado.
- La calidad depende mucho de la profundidad del paquete de dominio.
- La cobertura de repetición histórica, la calidad de evidencia y el conocimiento de dominio mejoran mediante contribuciones de la comunidad.
- La incorporación de PDF mediante OCR está diferida en esta vista previa pública.

## Licencia y descargo

Scenario Lab usa [PolyForm Noncommercial License 1.0.0](LICENSE). El repositorio público es para uso no comercial, no para despliegue comercial o reventa.

Required Notice: Copyright Heuristic Search Group LLC

Este repositorio es para uso experimental, educativo y de investigación. No es un producto predictivo, no garantiza eventos futuros y no sustituye juicio profesional, decisiones de inversión ni decisiones operativas. No es asesoramiento financiero.

El software se proporciona `as is`, sin garantía. En la medida permitida por la ley, Heuristic Search Group LLC no responde por pérdidas financieras, pérdidas de trading, pérdidas operativas u otros daños. Revisa [LICENSE](LICENSE), [NOTICE](NOTICE) y [docs/limitations.md](docs/limitations.md).

## Otros enlaces

- README canónico en inglés: [README.md](README.md)
- inicio rápido: [docs/quickstart.md](docs/quickstart.md)
- flujo de trabajo: [docs/natural-language-workflow.md](docs/natural-language-workflow.md)
- demo: [docs/demo-us-iran.md](docs/demo-us-iran.md)
- contribuidores: [CONTRIBUTORS.md](CONTRIBUTORS.md)
- notas de versión: [docs/release-notes/public-preview.md](docs/release-notes/public-preview.md)
