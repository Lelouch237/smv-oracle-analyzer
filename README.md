# SMV ORACLE Analyzer

Scanner de marché en lecture seule basé sur les règles SMV fournies dans la conversation.

## Règles actuellement codées
- Haussier : HH = sommet de plus en plus haut, HL = creux de plus en plus haut.
- Baissier : LL = creux de plus en plus bas, LH = sommet de plus en plus bas.
- Swing majeur = long mouvement en HTF.
- Swing interne = mouvement en LTF.
- Début/fin du swing : impulsions et corrections via HH/HL/LL/LH.

Les règles détaillées ORaCLE pour Liquidité, Zones d'intervention, Order Blocks, Breaker Blocks, Raffinage, Swing, Intraday et Entrée précise sont laissées en attente tant qu'elles ne sont pas définies précisément.

## Sécurité
Ce projet ne contient aucun module de placement d'ordres.
Aucune clé de trading n'est nécessaire pour la version actuelle.

## Démarrage
```bash
pip install -r requirements.txt
python bot.py
```
