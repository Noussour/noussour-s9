# TP1 — Chiffrements classiques

**Walid BECHAR — 222231326620**

[Rapport PDF](output/pdf/TP1_Walid_BECHAR_Report.pdf)

Exercices de chiffrement et de déchiffrement avec César, Playfair et Vigenère, calculs manuels et captures de JCrypTool. JCrypTool a été utilisé sur macOS.

## Fichiers

- `inputs/` : les six textes saisis.
- `output/results/` : les sorties produites par JCrypTool.
- `screenshots/` : captures des entrées, paramètres et résultats.
- `build_report.py` : génération du rapport et vérification des résultats.

Le déchiffrement Vigenère de `BR EYRLCAY CF UUAUYYDYQ` avec `SUN` donne `JX RGXYKGL KL HCGHGEQGW`. Le rapport signale cette incohérence dans l’énoncé.

## Régénérer le rapport

Python 3.12 ou supérieur :

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python build_report.py
```

Le PDF est écrit dans `output/pdf/`. Le script crée aussi une archive des captures et fichiers de calcul dans `output/`.
