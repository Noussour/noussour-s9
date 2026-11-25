# Modèles PIPE 5 (tous ouvrent dans PIPE : Fichier > Ouvrir)

## 1/ — implémentations existantes
`reservation.pnml`, `reservation-incorrecte.pnml` (TP réservation) ; `r1`, `r2`, `r3`, `r3_perte` (arcs inhibiteurs).

## 2/ — nouvelles implémentations (générées par `python generer-modeles.py --png`)
Format et mise en page identiques au modèle de Walid (`solution-bechar-walid/3-petri/reservation.pnml`) :
même grille, arcs orthogonaux avec points de passage, identifiants « source TO cible ». Un aperçu `.png`
accompagne chaque fichier.

- `2/walid/` : refus garde par un **arc inhibiteur** depuis `Libres` (`reserver_`, `refuser_`, `reessayer_`...).
- `2/mimobn/` : refus garde par un **arc de lecture** sur `Occupees` (réseau P/T pur, `Confirmer_`, `Refuser_`...).

Les deux interprétations sont équivalentes (`Libres + Occupees = 1`).
- `reservation-retour-2-utilisateurs.pnml` : 2 utilisateurs, une place. Après un refus ou une annulation, retour
  possible en attente. 14 marquages, sans blocage, réversible.
- `reservation-priorite-3-utilisateurs.pnml` : 3 utilisateurs (avec retour). Au départ U1 est confirmé, U2 est en
  attente, U3 vient réserver. Priorité U1 > U2 > U3 par arcs inhibiteurs (rouges) depuis `Attente_*` vers la
  réservation. 53 marquages, sans blocage, réversible. Limite : famine possible pour un utilisateur de faible priorité.
- `reservation-priorite-3-utilisateurs-U3-confirme.pnml` : même réseau, mais U3 est confirmé au départ, U1 et U2
  attendent, et U1 attend après U2. Priorité **U2 > U1 > U3** : nouvel arc inhibiteur `Attente_U2 → reserver_U1`
  (couloir du bas), les deux arcs de priorité vers `reserver_U3` sont conservés. 53 marquages, sans blocage,
  réversible, aucune violation de priorité.
- `reservation-priorite-3-utilisateurs-demande.pnml` : correction du précédent. Un utilisateur qui revient (après
  refus, abandon ou annulation) passe par `Demande_*` puis `rejoindre_*`, bloquée tant qu'un utilisateur qu'il
  dépasserait attend déjà : il ne regagne plus sa priorité. 111 marquages, sans blocage, réversible.

Historique complet des versions et des problèmes corrigés : [HISTORIQUE.md](HISTORIQUE.md).
Analyse : `python analyse.py <fichier>.pnml` ; rejeu du scénario : `python analyse.py --scenario <fichier>.pnml`.
