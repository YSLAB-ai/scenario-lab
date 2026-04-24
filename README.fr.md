# Scenario Lab

🌐 Languages: [English](README.md) | [中文](README.zh-CN.md) | [Español](README.es.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

> Aperçu expérimental : simulation Monte Carlo d'événements réels, exécutable localement avec Codex ou Claude.

Language: Français

This translation is provided for convenience. The English README is canonical for product scope, license terms, disclaimers, and release details.

Scenario Lab est un Monte Carlo simulation engine pour des événements réels, comme les conflits régionaux, les marchés, la politique et les décisions d'entreprise. C'est un outil expérimental de recherche, pas un produit de prédiction et not financial advice.

Version: `v0.1.0` public preview. Contributors: [CONTRIBUTORS.md](CONTRIBUTORS.md).

![Scenario Lab workflow](docs/assets/scenario-lab-workflow.png)

## Qu'est-ce que c'est

Scenario Lab transforme une situation en cours en simulation structurée. Vous indiquez les acteurs, le développement actuel et les preuves à approuver. Le moteur explore ensuite plusieurs futurs ramifiés avec Monte Carlo tree search et classe les branches trouvées.

Fonctionnement général :

- Un domain pack définit les acteurs, les phases et l'espace d'action pour un type d'événement, par exemple interstate crisis, market shock ou company decision.
- Le evidence packet approuvé et le cadrage du cas sont compilés en belief state avec actor behavior profiles et champs propres au domaine.
- Le simulation engine exécute `mcts`, propose des actions, échantillonne des transitions et note les branches.
- Les rapports transforment les branches en outcomes, scenario families et calibrated confidence labels lisibles.

## Démarrage rapide

Le guide complet se trouve dans [docs/quickstart.md](docs/quickstart.md). Installation locale minimale :

```bash
git clone git@github.com:YSLAB-ai/scenario-lab.git
cd scenario-lab
PYTHON=/path/to/python3.12
"$PYTHON" -m venv packages/core/.venv
source packages/core/.venv/bin/activate
pip install -e 'packages/core[dev]'
scenario-lab demo-run --root .forecast
```

Vous devriez voir `demo-run complete`, puis des artefacts dans `.forecast/runs/demo-run`.

Exemple en langage naturel :

```bash
scenario-lab scenario --root .forecast "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days"
```

Scenario Lab est prévu pour :

- `Codex`: [docs/install-codex.md](docs/install-codex.md)
- `Claude Code`: [docs/install-claude-code.md](docs/install-claude-code.md)

Commande de projet dans Claude Code :

```text
/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days
```

## Workflow et démonstration

Une exécution normale suit ces phases :

![Scenario Lab runtime workflow](docs/assets/scenario-lab-runtime-workflow.png)

1. `intake`: comprendre le problème, identifier les acteurs principaux et fixer l'horizon.
2. `evidence`: examiner les tiers importants, les preuves manquantes et les sources à importer.
3. `approval`: verrouiller le cadrage, les hypothèses et les preuves avant la recherche.
4. `simulation`: explorer les chemins avec deterministic Monte Carlo tree search.
5. `report`: afficher les outcomes principaux, expliquer les branches et permettre une mise à jour.

L'exemple vérifié `U.S.-Iran` est dans [docs/demo-us-iran.md](docs/demo-us-iran.md). Cette exécution a utilisé `10000` iterations et généré `133` nodes et `111` transposition hits. Le `interstate-crisis` pack actuel modélise des bounded crisis paths et ne modélise pas full-scale war comme terminal outcome explicite.

## Ce qui le rend utile

Scenario Lab ne considère pas toutes les branches comme également plausibles. La recherche est guidée par les domain rules, les actor behavior profiles et les preuves approuvées.

- Les actions sont contraintes par les domain packs.
- Les preuves modifient les actor profiles et les champs du domaine.
- Les conséquences négatives en aval pénalisent le classement.
- Une meilleure evidence et un meilleur domain knowledge produisent généralement une meilleure différenciation des branches.

Pour demander à un AI agent d'améliorer un domain pack trop mince, donnez-lui [docs/domain-pack-enrichment.md](docs/domain-pack-enrichment.md).

## Limites actuelles

Voir [docs/limitations.md](docs/limitations.md).

- La qualité dépend fortement du evidence packet approuvé.
- La qualité dépend fortement de la profondeur du domain pack.
- Replay coverage, evidence quality et domain knowledge s'améliorent par contributions de la communauté.
- OCR-backed PDF ingestion est différé dans cette public preview.

## Licence et avertissement

Scenario Lab est publié sous [PolyForm Noncommercial License 1.0.0](LICENSE). Le dépôt public est réservé aux usages non commerciaux, sans déploiement commercial ni revente.

Required Notice: Copyright Heuristic Search Group LLC

Ce dépôt est destiné à l'expérimentation, à l'éducation et à la recherche. Ce n'est pas un prediction product, il ne garantit aucun événement futur et ne remplace pas le jugement professionnel, les décisions d'investissement ou les décisions opérationnelles. It is not financial advice.

Le logiciel est fourni `as is`, sans garantie. Dans la mesure permise par la loi, Heuristic Search Group LLC n'est pas responsable des pertes financières, pertes de trading, pertes opérationnelles ou autres dommages. Consultez [LICENSE](LICENSE), [NOTICE](NOTICE) et [docs/limitations.md](docs/limitations.md).

## Autres liens

- English canonical README: [README.md](README.md)
- quickstart: [docs/quickstart.md](docs/quickstart.md)
- workflow: [docs/natural-language-workflow.md](docs/natural-language-workflow.md)
- demo: [docs/demo-us-iran.md](docs/demo-us-iran.md)
- contributors: [CONTRIBUTORS.md](CONTRIBUTORS.md)
- release notes: [docs/release-notes/public-preview.md](docs/release-notes/public-preview.md)
