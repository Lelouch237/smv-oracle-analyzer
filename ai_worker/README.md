# AI WORKER v1

Agent de recherche et d'exécution de micro-tâches pour marketplaces qui accueillent explicitement les agents IA.

## Mode actuel
DRY_RUN=true et ENABLE_AUTONOMY=false par défaut.

Le worker:
- scanne les tâches;
- score budget/concurrence/compatibilité/délai;
- sélectionne les meilleures opportunités;
- prépare des propositions;
- génère un brouillon de livrable;
- peut ensuite être connecté à une API de marketplace.

Le worker ne contourne pas les CAPTCHA, MFA, paywalls ou protections anti-bot, n'usurpe pas d'identité et ne travaille pas sur une plateforme qui interdit explicitement les agents.

## Marketplace initiale
market.near.ai. NEAR AI présente son Agent Market comme un marché où les agents peuvent proposer, exécuter et recevoir des paiements pour des tâches. Le cycle courant est open -> bid -> accepted -> in_progress -> submitted -> accepted/paid.

## Installation
```bash
python -m venv .venv
pip install -r ai_worker/requirements.txt
python -m ai_worker.worker.main --sample
```

## Live
Après tests et validation des conditions de la marketplace:
```text
ENABLE_AUTONOMY=true
DRY_RUN=false
MARKET_API_KEY=...
```

La clé ne doit jamais être commitée dans Git. Utiliser les Secrets du fournisseur d'exécution.

## Important
Cette v1 n'effectue pas de retrait financier et ne clique pas sur des sites arbitraires. Les tâches web pourront être ajoutées via des connecteurs/API explicitement autorisés.
