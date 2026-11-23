#import "petri.typ": net, legend, reach-graph

#let res = json("resultats.json")
#let r(k) = res.at(k)
// Compiler avec `--input real=1` une fois les captures PIPE dans captures/.
#let real = sys.inputs.at("real", default: "0") == "1"

#set document(title: "Réseaux de Petri : inhibiteurs, concurrence, annulation", author: "Bechar Walid")
#set text(lang: "fr", size: 10.5pt, font: "New Computer Modern")
#set page(paper: "a4", margin: (x: 2cm, y: 2cm), numbering: "1")
#set par(justify: true)
#set heading(numbering: "1.")
#show raw: set text(font: "DejaVu Sans Mono", size: 0.88em)
#show figure.caption: set text(size: 9pt)
#set table(stroke: 0.5pt + luma(170), inset: 5pt)
#show table.cell.where(y: 0): set text(weight: "bold")

// Capture d'une etape : vraie capture PIPE si disponible, sinon dessin.
#let cap(file, kind, m, fired: none, title, body) = block(breakable: false, {
  grid(columns: (55%, 1fr), column-gutter: 12pt, align: (center + horizon, left + horizon),
    figure(
      if real { image("captures/" + file + ".png", width: 100%) }
      else { net(kind, m, fired: fired, length: if kind == "r3" or kind == "r3bad" { 0.4cm } else { 0.43cm }, size: 6pt) },
      caption: title, supplement: [Capture]),
    text(size: 9.5pt, body))
  v(0.4em)
})

#align(center)[
  #text(size: 17pt, weight: "bold")[Arcs inhibiteurs, concurrence et annulation \ dans les réseaux de Petri]
  #v(0.2em)
  Bechar Walid, Groupe 2 #h(2em) Enseignant : M. Mekahlia #h(2em) Novembre 2026
]
#v(0.6em)

*Hypothèses.* Deux utilisateurs `U1`, `U2` et une seule place (1 jeton dans `Libres`). Chaque utilisateur passe par `Idle` (rien demandé), `Attente` (demande soumise), `Confirmee` (place obtenue). Les réseaux sont simulés dans PIPE 5.0.2 (fichiers `.pnml` joints). Le nombre d'états est calculé par le script `analyse.py`.

#if not real { align(center, legend) }

= Partie 1

== Réseau 1 : avec arc inhibiteur

- `demander_U1` : `Idle_U1` vers `Attente_U1`, avec un *arc inhibiteur* depuis `Attente_U2` (bloqué si `U2` attend). Symétrique pour `U2`.
- `attribuer_Ui` : consomme `Attente_Ui` *et* un jeton de `Libres`, produit `Confirmee_Ui`. Sans jeton dans `Libres`, pas d'attribution.

#cap("r1_0", "r1", (Idle_U1: 1, Idle_U2: 1, Libres: 1), [R1, état initial.])[
  Les deux demandes sont possibles, aucune place `Attente` n'est marquée.]
#cap("r1_1", "r1", (Idle_U2: 1, Attente_U1: 1, Libres: 1), fired: "demander_U1", [R1, après `demander_U1`.])[
  `U1` attend. L'inhibiteur depuis `Attente_U1` *bloque `demander_U2`* : `U2` ne peut pas entrer tant que `U1` attend.]
#cap("r1_2", "r1", (Idle_U2: 1, Confirmee_U1: 1), fired: "attribuer_U1", [R1, après `attribuer_U1`.])[
  La place va à `U1` (`Libres` = 0). `Attente_U1` est vide, donc `demander_U2` redevient possible.]
#cap("r1_3", "r1", (Attente_U2: 1, Confirmee_U1: 1), fired: "demander_U2", [R1, après `demander_U2`.])[
  `attribuer_U2` est bloquée car `Libres` = 0. Plus aucune transition possible : *blocage*, `U2` attend pour toujours.]

== Réseau 2 : demandes concurrentes

Même réseau sans les arcs inhibiteurs : `demander_Ui` ne dépend que de `Idle_Ui`. L'exclusion repose sur le seul jeton de `Libres`.

#cap("r2_1", "r2", (Idle_U2: 1, Attente_U1: 1, Libres: 1), fired: "demander_U1", [R2, après `demander_U1`.])[
  Contrairement au réseau 1, `demander_U2` reste possible pendant que `U1` attend.]
#cap("r2_2", "r2", (Attente_U1: 1, Attente_U2: 1, Libres: 1), fired: "demander_U2", [R2, après `demander_U2`.])[
  Les deux attendent. `attribuer_U1` et `attribuer_U2` sont *en conflit* : elles veulent le même jeton de `Libres`.]
#cap("r2_3", "r2", (Attente_U1: 1, Confirmee_U2: 1), fired: "attribuer_U2", [R2, après `attribuer_U2`.])[
  `U2` gagne. Le jeton est consommé, `attribuer_U1` est désactivée : la place n'est pas attribuée deux fois. `U1` reste bloqué.]

== Comparaison

#table(columns: (auto, 1fr, 1fr),
  [], [Réseau 1 (inhibiteur)], [Réseau 2 (concurrent)],
  [Traitement des demandes], [une seule demande en attente à la fois], [toutes les demandes acceptées en attente],
  [Acceptation], [`Attente_Ui` et `Libres` $>= 1$], [idem],
  [Rôle de l'inhibiteur], [contrôle l'entrée, évite le conflit], [aucun inhibiteur],
  [Blocage], [l'utilisateur en attente bloque aussi l'entrée des suivants], [les non servis attendent, mais l'entrée reste ouverte],
  [Transitions / états / arcs], [#r("R1_2u_1p").transitions / #r("R1_2u_1p").states / #r("R1_2u_1p").edges], [#r("R2_2u_1p").transitions / #r("R2_2u_1p").states / #r("R2_2u_1p").edges],
  [Avantages], [pas de conflit, moins d'états], [réaliste, sûr sans inhibiteur],
  [Inconvénients], [restrictif, blocage général], [conflit non déterministe, pas d'équité],
)

Le réseau 2 a un état de plus : celui où les deux utilisateurs attendent, que l'inhibiteur interdit dans le réseau 1. Dans les deux cas, l'invariant `Libres + Confirmee_U1 + Confirmee_U2 = 1` est vérifié : jamais de double attribution.

*Choix : réseau 2.* La sûreté vient du jeton de `Libres`, pas de l'inhibiteur. L'inhibiteur ne fait que limiter l'entrée, ce qui transforme un manque de place en blocage de tout le système. Le conflit du réseau 2 représente la vraie concurrence sur la dernière place, et il est bien résolu (un seul gagnant).

#pagebreak()
= Partie 2 : annulation (réseau 3)

On ajoute au réseau 2 `annuler_Ui` : consomme `Confirmee_Ui`, produit `Annulee_Ui` *et rend un jeton à `Libres`*.

#cap("r3_2", "r3", (Idle_U2: 1, Confirmee_U1: 1), fired: "attribuer_U1", [R3, après `demander_U1` et `attribuer_U1`.])[
  `U1` a la place, `Libres` = 0. `annuler_U1` devient possible.]
#cap("r3_3", "r3", (Attente_U2: 1, Confirmee_U1: 1), fired: "demander_U2", [R3, après `demander_U2`.])[
  `U2` attend, mais `attribuer_U2` est bloquée (`Libres` = 0).]
#cap("r3_4", "r3", (Attente_U2: 1, Libres: 1, Annulee_U1: 1), fired: "annuler_U1", [R3, après `annuler_U1`.])[
  Le jeton revient dans `Libres`. `attribuer_U2` devient franchissable, mais ne part pas toute seule.]
#cap("r3_5", "r3", (Annulee_U1: 1, Confirmee_U2: 1), fired: "attribuer_U2", [R3, après `attribuer_U2`.])[
  `U2` obtient la place libérée.]

- *La place redevient-elle disponible ?* Oui, grâce à l'arc `annuler_U1` vers `Libres`.
- *`U2` est-il accepté automatiquement ?* Non. `attribuer_U2` devient possible, mais un réseau de Petri n'oblige jamais à franchir une transition : il faut la déclencher.
- *Conditions de confirmation de `U2` :* `Attente_U2` = 1 et `Libres` = 1. Avec plusieurs demandeurs, `U2` doit aussi gagner le conflit, sans priorité.
- *Blocage ou perte ?* Aucune perte : l'invariant reste vrai (#r("R3_2u_1p").states états, le seul état mort est la fin normale où les deux ont annulé). Mais `U2` attend indéfiniment si `U1` n'annule jamais. Sans l'arc de retour vers `Libres`, la place serait perdue et `U2` bloqué, comme le montre la variante ci-dessous.

#cap("r3_perte", "r3bad", (Attente_U2: 1, Annulee_U1: 1), fired: "annuler_U1", [Variante sans arc de retour, après `annuler_U1`.])[
  `U1` a annulé mais `Libres` reste à 0 : place perdue, `U2` bloqué.]

= Conclusion

#table(columns: (auto, 1fr, 1fr, 1fr),
  [], [Réseau 1], [Réseau 2], [Réseau 3],
  [Admission], [une demande à la fois], [libre], [libre],
  [Conflit sur la place], [non], [oui], [oui],
  [États (2 u., 1 place)], [#r("R1_2u_1p").states], [#r("R2_2u_1p").states], [#r("R3_2u_1p").states],
  [Double attribution], [impossible], [impossible], [impossible],
  [Blocage avec attente], [oui], [oui], [non],
)

Dans toutes les simulations, la place n'a été attribuée qu'avec un jeton dans `Libres`, sans double attribution. Le réseau 1 sérialise les demandes mais bloque tout dès qu'une place manque. Le réseau 2 laisse les demandes entrer et gère le conflit, mais un perdant n'a pas d'issue. Le réseau 3 ajoute l'annulation : la place circule et il n'y a plus de blocage.

*Solution retenue : le réseau 3.* Il garde la sûreté du réseau 2 sans inhibiteur et ne laisse jamais une place inutilisée. Il resterait à ajouter un refus ou un abandon pour limiter l'attente, et une priorité pour l'équité.
