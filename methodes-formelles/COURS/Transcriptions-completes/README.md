# Cours de méthodes formelles — transcriptions et résumés

Enseignante : Dr MEKAHLIA Fatma Zohra · USTHB · 5e année Software Engineering.

Les quatre supports de cours ont été consultés dans la session Edge autorisée le **3 novembre 2026**, depuis [la classe](https://classroom.google.com/c/ODg4NjEyMTk1OTQx). Le dossier couvre **155 diapositives** et conserve **35 captures de formules, schémas et tableaux**.

| Chapitre | Diapositives | Transcription |
| --- | --- | --- |
| 1 — Introduction aux méthodes formelles | 52 | [Lire](../Chapitre-01/cours.md) |
| 2 — Les principales familles de méthodes formelles | 32 | [Lire](../Chapitre-02/cours.md) |
| 3 — Logique de Hoare | 29 | [Lire](../Chapitre-03/cours.md) |
| 4 — Automates et systèmes de transitions | 42 | [Lire](../Chapitre-04/cours.md) |

- [Transcription réunie des quatre chapitres](transcription.md), avec captures et compléments visuels.
- [Transcription en texte brut](transcription.txt).
- [resumer.pdf — résumé organisé par chapitre](../resumer.pdf).
- [Résumé détaillé, version modifiable](../resumer.md).
- [Fiche de révision](../fiche-revision.md).

## Lecture des transcriptions

Chaque page distingue le **texte du support**, la **transcription complémentaire des éléments visuels** et, si nécessaire, une **note de lecture/correction**. Les captures permettent de vérifier les formules et figures qui n'étaient pas présentes dans la couche texte accessible du lecteur PDF.

La structure et la formulation du texte source sont conservées, y compris ses coquilles. Seules les puces de police ont été normalisées et les notifications de l'interface Drive retirées. Les descriptions de figures explicitent leur contenu ; leur disposition graphique est conservée dans les captures. Les corrections pédagogiques sont annoncées comme telles.

Les références des supports sont dans `sources.json`. Chaque dossier `Chapitre-01` à `Chapitre-04` contient son `cours.md`, son `texte-source.json` et ses figures éventuelles. Les compléments vérifiés visuellement sont dans `complements-visuels.json`.

Pour régénérer le PDF à partir de `../resumer.md`, exécuter `python methodes-formelles/COURS/Transcriptions-completes/generer-resumer.py` depuis la racine du dépôt. ReportLab et les polices DejaVu (ou Arial/Consolas sous Windows) sont nécessaires.
