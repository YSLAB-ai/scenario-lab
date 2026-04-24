# Scenario Lab

🌐 Languages: [English](README.md) | [中文](README.zh-CN.md) | [Español](README.es.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

> Aperçu expérimental : simulation Monte Carlo d'événements réels, exécutable localement avec Codex ou Claude.

Langue : Français

Cette traduction est fournie pour faciliter la lecture. English README is canonical ; la version anglaise fait autorité pour le périmètre du produit, la licence, les avertissements et les détails de publication.

Scenario Lab est un moteur de simulation Monte Carlo pour des événements réels, comme les conflits régionaux, les marchés, la politique et les décisions d'entreprise. C'est un outil expérimental de recherche, pas un produit prédictif et ne constitue pas un conseil financier.

Version : `v0.1.0` aperçu public. Contributeurs : [CONTRIBUTORS.md](CONTRIBUTORS.md).

![Flux de travail de Scenario Lab](docs/assets/scenario-lab-workflow.png)

## Qu'est-ce que c'est

Scenario Lab transforme une situation en cours en simulation structurée. Vous indiquez les acteurs, l'évolution actuelle et les preuves à approuver. Le moteur explore ensuite plusieurs futurs ramifiés avec une recherche arborescente Monte Carlo et classe les branches trouvées.

Fonctionnement général :

- Un paquet de domaine définit les acteurs, les phases et l'espace d'action pour un type d'événement, par exemple crise interétatique, choc de marché ou décision d'entreprise.
- Le paquet de preuves approuvé et le cadrage du cas sont compilés en état de croyance avec des profils de comportement des acteurs et des champs propres au domaine.
- Le moteur de simulation exécute `mcts`, propose des actions, échantillonne des transitions d'état et note les branches.
- Les rapports transforment les branches explorées en résultats, familles de scénarios et étiquettes de confiance calibrée.

Le même environnement peut servir aux conflits régionaux, tensions de marché, négociations politiques et réponses d'entreprise, car chaque paquet de domaine porte ses propres règles et champs d'état.

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

- `Codex` : [docs/install-codex.md](docs/install-codex.md)
- `Claude Code` : [docs/install-claude-code.md](docs/install-claude-code.md)

Commande de projet dans Claude Code :

```text
/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days
```

## Corpus de preuves

Les brouillons de preuves utilisent par défaut la base SQLite locale `.forecast/corpus.db`. Si elle n'existe pas encore, enregistrez les fichiers de preuves pertinents dans `.forecast/evidence-candidates/`, puis exécutez :

```bash
scenario-lab ingest-directory --root .forecast --path .forecast/evidence-candidates --tag domain=interstate-crisis
scenario-lab draft-evidence-packet --root .forecast --run-id <run-id> --revision-id r1
```

Vous pouvez aussi utiliser l'exécution d'adaptateur pour importer les fichiers recommandés :

```bash
scenario-lab run-adapter-action --root .forecast --candidate-path .forecast/evidence-candidates --run-id <run-id> --revision-id r1 --action batch-ingest-recommended
scenario-lab run-adapter-action --root .forecast --run-id <run-id> --revision-id r1 --action draft-evidence-packet
```

Utilisez `--corpus-db <path>` uniquement si vous voulez une base de preuves séparée.

## Flux de travail et démonstration

Une exécution normale suit ces phases :

![Flux d'exécution de Scenario Lab](docs/assets/scenario-lab-runtime-workflow.png)

1. `intake` : comprendre le problème, identifier les acteurs principaux et fixer l'horizon.
2. `evidence` : examiner les tiers importants, les preuves manquantes et les sources à importer.
3. `approval` : verrouiller le cadrage, les hypothèses et les preuves avant la recherche.
4. `simulation` : explorer les chemins possibles avec une recherche arborescente Monte Carlo déterministe.
5. `report` : afficher les résultats principaux, expliquer les branches et permettre une mise à jour.

L'exemple vérifié `U.S.-Iran` est dans [docs/demo-us-iran.md](docs/demo-us-iran.md). Cette exécution a utilisé `10000` itérations et généré `133` nœuds et `111` correspondances de transposition. Le paquet de domaine de crise interétatique actuel modélise des trajectoires de crise bornée et ne modélise pas la guerre totale comme résultat final explicite.

## Ce qui le rend utile

Scenario Lab ne considère pas toutes les branches comme également plausibles. La recherche de branches est guidée par les règles de domaine, les profils de comportement des acteurs et les preuves approuvées.

- Les actions sont contraintes par les paquets de domaine.
- Les preuves modifient les profils d'acteurs et les champs du domaine.
- Les conséquences négatives ultérieures pénalisent le classement.
- De meilleures preuves et une meilleure connaissance de domaine produisent généralement une différenciation plus nette des branches.

Pour demander à un agent d'IA d'améliorer un paquet de domaine trop mince, donnez-lui [docs/domain-pack-enrichment.md](docs/domain-pack-enrichment.md).

## Limites actuelles

Voir [docs/limitations.md](docs/limitations.md).

- La qualité dépend fortement du paquet de preuves approuvé.
- La qualité dépend fortement de la profondeur du paquet de domaine.
- La couverture de rejeu historique, la qualité des preuves et la connaissance de domaine s'améliorent par contributions de la communauté.
- L'ingestion de PDF avec OCR est différée dans cet aperçu public.

## Licence et avertissement

Scenario Lab est publié sous [PolyForm Noncommercial License 1.0.0](LICENSE). Le dépôt public est réservé aux usages non commerciaux, sans déploiement commercial ni revente.

Required Notice: Copyright Heuristic Search Group LLC

Ce dépôt est destiné à l'expérimentation, à l'éducation et à la recherche. Ce n'est pas un produit prédictif, il ne garantit aucun événement futur et ne remplace pas le jugement professionnel, les décisions d'investissement ou les décisions opérationnelles. Il ne constitue pas un conseil financier.

Le logiciel est fourni `as is`, sans garantie. Dans la mesure permise par la loi, Heuristic Search Group LLC n'est pas responsable des pertes financières, pertes de trading, pertes opérationnelles ou autres dommages. Consultez [LICENSE](LICENSE), [NOTICE](NOTICE) et [docs/limitations.md](docs/limitations.md).

## Autres liens

- README canonique en anglais : [README.md](README.md)
- démarrage rapide : [docs/quickstart.md](docs/quickstart.md)
- flux de travail : [docs/natural-language-workflow.md](docs/natural-language-workflow.md)
- démo : [docs/demo-us-iran.md](docs/demo-us-iran.md)
- contributeurs : [CONTRIBUTORS.md](CONTRIBUTORS.md)
- notes de version : [docs/release-notes/public-preview.md](docs/release-notes/public-preview.md)
