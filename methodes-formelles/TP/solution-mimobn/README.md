# solution tdtp — Méthodes formelles

Le corrigé répond aux douze points du sujet `../../TD-TP-MFGL.pdf`.

- [Document PDF](../solution-mimobn.pdf)
- [Version Markdown complète](../solution-mimobn.md)
- `java/` : implémentation Java 17, tests, course incorrecte, explorateur Petri et calcul probabiliste.
- `modeles/` : automate PlantUML, PNML et XML PIPE, modèles NuSMV, DTMC et propriétés PRISM.
- `figures/` : automate, conflit Petri et courbe de probabilité.
- `resultats/` : sorties réelles des outils et récapitulatif avec empreintes SHA-256.

Les identifiants étudiant sont laissés à compléter dans le document.

## Reproduire les vérifications Java

Installer un **JDK 17 ou supérieur**, puis ouvrir un terminal dans ce dossier :

```bat
verifier-java.cmd
```

Sous un autre système, les commandes équivalentes sont :

```sh
mkdir -p out
javac --release 17 -encoding UTF-8 -d out java/*.java
java -cp out ReservationTests
java -cp out PetriExplorer modeles/reservation.pnml
java -cp out PetriExplorer modeles/reservation-pipe.xml
java -cp out PetriExplorer modeles/reservation-incorrecte.pnml --expect-unsafe
java -cp out ProbabilityAnalysis
```

Résultats attendus : 830 vérifications réussies, dont 200 essais concurrents ;
12 marquages pour les deux fichiers Petri corrects ; 19 marquages pour le réseau
incorrect avec une violation attendue. Le cas incorrect ne fait pas échouer le
script : il vérifie que le défaut volontaire est effectivement détecté.

## Reproduire les modèles formels

Versions réellement utilisées : Java 17, NuSMV 2.7.1, PRISM 4.11.
Après installation et ajout des exécutables au PATH :

```text
NuSMV modeles/reservation-correcte.smv
NuSMV modeles/reservation-incorrecte.smv
NuSMV modeles/reservation-sans-equite.smv
prism modeles/reservation-probabiliste.pm modeles/reservation-probabiliste.pctl -explicit -const D=5
prism modeles/reservation-probabiliste.pm modeles/reservation-probabiliste.pctl -explicit -const D=0:10 -prop 1
java -jar plantuml.jar -tpng modeles/reservation.puml -o ../figures
```

Sous Windows, adapter `prism` au lanceur de votre installation. Certains lanceurs
PRISM utilisent des chemins relatifs et exigent d'être exécutés depuis leur dossier
`bin` ; donner alors des chemins absolus vers les modèles et propriétés.

Les modèles NuSMV incorrect et sans équité doivent produire des propriétés
**false**, avec contre-exemples : c'est un résultat pédagogique attendu.
Les sept propriétés du modèle corrigé sont **true**. Pour D=5, PRISM donne
0,932421875 pour la confirmation avant l'échéance incluse.

Ouvrir `modeles/reservation-pipe.xml` dans PIPE pour l'animation graphique.
L'importation graphique PIPE n'a pas été exécutée : les fichiers Petri livrés ont
été explorés exhaustivement par l'explorateur Java fourni. L'automate a été généré
avec PlantUML et ses transitions exercées par les tests Java.

Les paramètres probabilistes sont pédagogiques. Les vérifications NuSMV et Petri
portent sur deux demandes et une place ; le Java accepte une capacité générale.
Le rapport détaille les hypothèses et les garanties de chaque abstraction.

## Régénérer le document

```text
python -m pip install reportlab pillow
python generer-document.py
```

Le générateur lit `rapport-source.md`, inclut les sources Java et les modèles,
puis écrit `../solution-mimobn.md` et `../solution-mimobn.pdf`. Il utilise les polices
DejaVu (installées sur le système ou fournies avec matplotlib), ou Arial/Consolas
sous Windows. Les journaux de vérification ne sont pas réécrits par ce script.
