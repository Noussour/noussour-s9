"""Construit le rapport « Évolution du réseau de Petri » : modèles, analyses, figures, rapport.md et rapport.pdf.

Usage : python construire.py
Tous les chiffres du rapport sont calculés ici à partir des fichiers PIPE (aucune valeur saisie à la main).
"""
import json
import sys
from pathlib import Path

import markdown
import networkx as nx
import sympy as sp

from figures import AJOUT, PROBLEME, graphe, reseau
from modeles import construire as construire_modeles
from proprietes import conflits, famine, incidence, proprietes, violations_priorite

ICI = Path(__file__).resolve().parent
FIG = ICI / "figures"
U2, U3 = ("U1", "U2"), ("U1", "U2", "U3")


def depassements(r, u):
    """Nombre maximal de réservations faites par d'autres pendant que u reste en attente (None si illimité)."""
    S = {k for k, m in r["etats"].items() if m["Attente_" + u]}
    G = nx.DiGraph()
    for k in S:
        G.add_node(k)
        for t, d in r["succ"][k]:
            if d in S:
                w = 1 if t.startswith("reserver_") else 0
                G.add_edge(k, d, w=max(w, G[k][d]["w"] if G.has_edge(k, d) else 0))
    for a, b, w in G.edges(data="w"):
        if w and nx.has_path(G, b, a):
            return None
    C = nx.condensation(G)
    best = {}
    for c in reversed(list(nx.topological_sort(C))):
        best[c] = max([best[d] + max(G[a][b]["w"] for a in C.nodes[c]["members"] for b in C.nodes[d]["members"]
                                     if G.has_edge(a, b)) for d in C.successors(c)] or [0])
    return max(best.values()) if best else 0


def dim_invariants(n):
    C = incidence(n)
    M = sp.Matrix([[C[p][t] for t in n.trans] for p in n.m0])
    return len(M.T.nullspace())


def rejouer(n, sequence):
    m, lignes = n.m0, [("M0", "—", n.m0)]
    for i, t in enumerate(sequence, 1):
        m = n.tirer(m, t)
        lignes.append(("M%d" % i, t, m))
    return lignes, [t for t in n.actives(m) if t.startswith("reserver_")]


def etat_u(m, u):
    noms = {"Attente": "attente", "Confirmee": "**confirmé**", "Refusee": "refusé", "Annulee": "annulé",
            "Demande": "demande"}
    return ", ".join(noms[p.split("_")[0]] for p, v in m.items() if v and p.endswith("_" + u)
                     and p.split("_")[0] in noms) or "—"


def table_scenario(lignes, users):
    t = ["| Marquage | Transition franchie | " + " | ".join(users) + " | Libres |",
         "|---|---|" + "---|" * len(users) + "---|"]
    for nom, tr, m in lignes:
        t.append("| %s | `%s` | %s | %d |" % (nom, tr, " | ".join(etat_u(m, u) for u in users), m["Libres"]))
    return "\n".join(t)


def oui(b):
    return "oui" if b else "**non**"


def main():
    FIG.mkdir(exist_ok=True)
    ch = construire_modeles()
    users = {"E0": U2, "E1": U2, "E2": U2, "E2b": U3, "E3": U3, "E4": U3, "E5": U3}
    R = {k: proprietes(c, users[k]) for k, c in ch.items()}
    for k in ("E2b", "E3", "E4", "E5"):
        R[k]["famine"] = {u: famine(R[k], u) for u in U3}
        R[k]["depasse"] = {u: depassements(R[k], u) for u in U3}
    R["E3"]["viol"] = violations_priorite(R["E3"], ("U1", "U2", "U3"))
    R["E4"]["viol"] = violations_priorite(R["E4"], ("U2", "U1", "U3"))
    R["E5"]["viol"] = violations_priorite(R["E5"], ("U2", "U1", "U3"))
    for k in R:
        R[k]["dim_inv"] = dim_invariants(R[k]["n"])

    # --- figures des réseaux, modifications surlignées
    reseau(ch["E0"], FIG / "E0.png", {"Libres": PROBLEME},
           {("reserver_U1", "Libres"): PROBLEME, ("reserver_U2", "Libres"): PROBLEME})
    reseau(ch["E1"], FIG / "E1.png", {p: PROBLEME for p in ("Refusee_U1", "Refusee_U2", "Annulee_U1", "Annulee_U2")})
    nouv = {t + u: AJOUT for t in ("retour_refus_", "reessayer_") for u in U2}
    reseau(ch["E2"], FIG / "E2.png", nouv, {(s, d): AJOUT for t in nouv for (s, d) in
                                             [(a, b) for a in [t] for b in ("Attente_" + t[-2:],)] +
                                             [(("Refusee_" if "refus" in t else "Annulee_") + t[-2:], t)]})
    prio3 = [("Attente_U1", "reserver_U2"), ("Attente_U1", "reserver_U3"), ("Attente_U2", "reserver_U3")]
    reseau(ch["E3"], FIG / "E3.png", {"Attente_U1": AJOUT, "Attente_U2": AJOUT}, {a: AJOUT for a in prio3})
    reseau(ch["E4"], FIG / "E4.png", {"Confirmee_U3": AJOUT}, {("Attente_U2", "reserver_U1"): AJOUT})
    dem = {p + u: AJOUT for p in ("Demande_", "rejoindre_") for u in U3}
    garde = [("Attente_U1", "rejoindre_U2"), ("Attente_U3", "rejoindre_U2"), ("Attente_U3", "rejoindre_U1")]
    arcs5 = {a: AJOUT for a in garde}
    for u in U3:
        arcs5.update({("retour_refus_" + u, "Demande_" + u): AJOUT, ("reessayer_" + u, "Demande_" + u): AJOUT,
                      ("Demande_" + u, "rejoindre_" + u): AJOUT, ("rejoindre_" + u, "Attente_" + u): AJOUT})
    reseau(ch["E5"], FIG / "E5.png", dem, arcs5)
    graphe(R["E0"], FIG / "graphe-E0.png")
    graphe(R["E1"], FIG / "graphe-E1.png")
    graphe(R["E2"], FIG / "graphe-E2.png")

    # --- scénarios
    sc0, act0 = rejouer(R["E0"]["n"], ["reserver_U1", "reserver_U2"])
    sc2b, act2b = rejouer(R["E2b"]["n"], ["annuler_U1"])
    seq = ["abandonner_U2", "reessayer_U2", "annuler_U3"]
    sc4, act4 = rejouer(R["E4"]["n"], seq)
    sc5, act5 = rejouer(R["E5"]["n"], seq)

    md = rapport(R, sc0, sc2b, act2b, sc4, act4, sc5, act5)
    (ICI / "rapport.md").write_text(md, encoding="utf-8")
    (ICI / "resultats.json").write_text(json.dumps({k: {x: v for x, v in r.items() if x not in
                                                        ("n", "etats", "succ", "ordre", "morts")} | {"morts": len(r["morts"])}
                                                    for k, r in R.items()}, indent=2, ensure_ascii=False),
                                        encoding="utf-8")
    pdf(md)
    print("rapport.md, rapport.pdf, resultats.json")


def ligne_synthese(nom, r, prob):
    return "| %s | %d | %d | %s | %d | %s | %s | %s | %s | %s |" % (
        nom, r["marquages"], r["borne"], oui(r["sauf"]), len(r["morts"]), oui(r["quasi"]), oui(r["vivant"]),
        oui(r["reversible"]), oui(r["exclusion"]), prob)


def rapport(R, sc0, sc2b, act2b, sc4, act4, sc5, act5):
    E0, E1, E2, E2b, E3, E4, E5 = (R[k] for k in ("E0", "E1", "E2", "E2b", "E3", "E4", "E5"))
    conf1 = [c for c in conflits(E1["n"]) if c[2] == ["Libres"]]
    dep = lambda r, u: "illimité" if r["depasse"][u] is None else str(r["depasse"][u])
    return f"""# Évolution d'un réseau de Petri : de la première modélisation à la version actuelle

<p class="subtitle">Réservation de la dernière place — chaque modification et le problème qui l'a rendue nécessaire</p>

<p class="meta"><b>Étudiant :</b> Mohamed BENALIA &nbsp;·&nbsp; <b>Réseau de départ :</b> Walid BECHAR &nbsp;·&nbsp; <b>Module :</b> Méthodes formelles &nbsp;·&nbsp; <b>Enseignant :</b> M. Mekahlia &nbsp;·&nbsp; Novembre 2026</p>

## 1. Objet du rapport

Le système étudié est la réservation de **la dernière place disponible** : plusieurs utilisateurs la demandent,
un seul doit l'obtenir, les autres sont refusés, et une réservation confirmée peut être annulée. Nous l'avons
modélisé par un réseau de Petri sous **PIPE 5**, puis nous avons modifié ce réseau à plusieurs reprises.
Chaque version a été écrite pour corriger un défaut que l'analyse de la version précédente avait révélé.

Le rapport suit cette évolution dans l'ordre. Pour chaque étape, il présente le réseau, ses propriétés, puis
**le problème qui a imposé l'étape suivante**. Le point de départ est le réseau de Walid BECHAR
(`solution-bechar-walid/3-petri/reservation.pnml`). Toutes les versions suivantes reprennent sa mise en page et
ses noms. Elles sont précédées d'un modèle naïf (étape 0) qui justifie sa construction.

**Méthode.** Chaque version est un fichier PIPE (`modeles/*.pnml`). Le programme `construire.py` lit ces fichiers,
construit le **graphe des marquages accessibles** avec la règle de franchissement de PIPE, puis calcule toutes les
propriétés et tous les chiffres du rapport. Les figures reprennent les positions enregistrées dans les fichiers.

<p class="legend"><b>Lecture des figures de réseaux :</b> cercle = place (● = jeton) ; rectangle noir = transition ;
flèche = arc ordinaire ; <span style="color:#c0392b"><b>trait rouge terminé par un petit cercle</b></span> = arc
inhibiteur. <span style="color:#059669"><b>En vert épais</b></span> : éléments ajoutés à l'étape ;
<span style="color:#dc2626"><b>en rouge épais</b></span> : éléments responsables du problème décrit.</p>

## 2. Notions utilisées

| Notion | Définition retenue | Comment elle est vérifiée |
|---|---|---|
| Marquage, franchissement | État du réseau = nombre de jetons par place. Une transition est **franchissable** si chaque place d'entrée contient assez de jetons et si chaque place reliée par un **arc inhibiteur** est vide. | Règle de PIPE |
| Arc inhibiteur | Test à zéro : `p ⊸ t` autorise `t` seulement si `p` est vide. Il ne consomme aucun jeton. | — |
| Graphe des marquages | Ensemble des marquages accessibles depuis M0, reliés par les franchissements. | Exploration en largeur |
| Réseau **borné**, **sauf** | Borné : le nombre de jetons de chaque place reste fini (k-borné : au plus k jetons). Sauf : 1-borné. | Maximum sur le graphe |
| **Blocage** (marquage mort) | Marquage où aucune transition n'est franchissable. | Nœud sans successeur |
| **Quasi-vivacité** | Chaque transition peut être franchie au moins une fois depuis M0. | Transitions présentes sur le graphe |
| **Vivacité** | Depuis **tout** marquage accessible, chaque transition peut encore être franchie plus tard. Plus forte que l'absence de blocage. | Pour chaque marquage, transitions atteignables |
| **Réversibilité** | M0 est accessible depuis tout marquage accessible : M0 est un **état d'accueil**. | Accessibilité inverse |
| **P-invariant** | Vecteur `y` tel que `y · C = 0`, avec `C = Post − Pre` la matrice d'incidence. La somme pondérée `y · M` reste constante. | Calcul symbolique sur `C` |
| **Conflit** | Deux transitions franchissables qui partagent une place d'entrée : en franchir une peut désactiver l'autre. | Places d'entrée communes |
| **Exclusion mutuelle** | Jamais deux utilisateurs confirmés en même temps. | Sur chaque marquage |
| **Équité**, **famine** | Famine : un utilisateur en attente peut être dépassé indéfiniment, car il existe un cycle où il reste en attente pendant que d'autres réservent. Attente **bornée** : il est dépassé au plus *k* fois. | Cycles et plus longs chemins dans le graphe |

## 3. Vue d'ensemble de l'évolution

| Étape | Marquages | Borne | Sauf | Blocages | Quasi-vivant | Vivant | Réversible | Exclusion | Problème qui mène à l'étape suivante |
|---|---|---|---|---|---|---|---|---|---|
{ligne_synthese("E0 modèle naïf", E0, "deux utilisateurs confirmés à la fois")}
{ligne_synthese("E1 réseau de Walid", E1, "états puits : refus et annulation définitifs")}
{ligne_synthese("E2 retour", E2, "à 3 utilisateurs, conflit non arbitré, famine")}
{ligne_synthese("E3 priorité U1>U2>U3", E3, "nouveau scénario : U3 confirmé, U2 avant U1")}
{ligne_synthese("E4 U3 confirmé, U2>U1>U3", E4, "l'utilisateur qui revient regagne sa priorité")}
{ligne_synthese("E5 état Demande", E5, "— (version actuelle)")}

Taille des réseaux : E0 et E1 ont {E1["places"]} places et {E1["transitions"]} transitions, E2 en a {E2["places"]} et
{E2["transitions"]}, E3 et E4 en ont {E3["places"]} et {E3["transitions"]}, et E5 en a {E5["places"]} et
{E5["transitions"]}.

## 4. Étape 0 — Modèle naïf : tester la place sans la prendre

**Modélisation.** Une première idée consiste à vérifier qu'une place est libre, puis à confirmer. Dans le réseau,
`reserver_Ui` lit le jeton de `Libres` et **le remet aussitôt** (arc retour, en rouge). La vérification et la prise
de la place ne sont donc pas atomiques.

<figure><img src="figures/E0.png"><figcaption>Figure 1 — E0 : réseau de Walid dont la réservation rend le jeton à
Libres (arcs rouges). Le test de disponibilité ne réserve rien.</figcaption></figure>

**Analyse.** Le graphe compte {E0["marquages"]} marquages. Le réseau **n'est pas sauf** : `Libres` monte jusqu'à
{E0["borne"]} jetons. Il est seulement {E0["borne"]}-borné. La somme `Libres + Occupees` n'est plus un invariant,
et l'**exclusion mutuelle est violée**. La séquence la plus courte qui la viole a deux franchissements :

{table_scenario(sc0, U2)}

<figure><img src="figures/graphe-E0.png" style="width:88%"><figcaption>Figure 2 — Graphe des marquages de E0. Un état
s'écrit « U1 U2 / jetons de Libres et Occupees », avec A = attente, C = confirmé, R = refusé, X = annulé. Le
marquage « C C » sur fond rouge viole l'exclusion mutuelle. Les cadres rouges sont des blocages.</figcaption></figure>

Les transitions `refuser_U1` et `refuser_U2` ne sont **jamais** franchies : `Libres` n'est jamais vide. Le réseau
n'est donc même pas quasi-vivant, et le refus prévu par le cahier des charges ne se produit pas.

> **Problème → étape 1.** La place doit être **consommée au moment même où elle est attribuée**. Il faut une
> ressource partagée dont le jeton disparaît à la réservation.

## 5. Étape 1 — Le réseau de Walid : une ressource partagée

**Modélisation.** Le jeton de `Libres` représente la place. `reserver_Ui` le **consomme** et dépose un jeton dans
`Occupees`. `annuler_Ui` le rend. Le refus est gardé par un **arc inhibiteur** `Libres ⊸ refuser_Ui` : on ne refuse
que lorsqu'il ne reste aucune place. Chaque utilisateur suit le cycle `Attente → Confirmee / Refusee / Annulee`.

<figure><img src="figures/E1.png"><figcaption>Figure 3 — E1 : réseau de Walid BECHAR. Les places en rouge
(Refusee, Annulee) n'ont aucune transition de sortie.</figcaption></figure>

**Propriétés obtenues.**

- **Sauf** : chaque place contient au plus {E1["borne"]} jeton ; {E1["marquages"]} marquages accessibles.
- **P-invariants** (l'espace des invariants est de dimension {E1["dim_inv"]}) :
  `Libres + Occupees = 1`, `Attente_Ui + Confirmee_Ui + Refusee_Ui + Annulee_Ui = 1` pour chaque utilisateur, et
  `Occupees − Confirmee_U1 − Confirmee_U2 = 0`.
  Avec le premier invariant, le dernier donne `Confirmee_U1 + Confirmee_U2 = Occupees ≤ 1` : **l'exclusion
  mutuelle est démontrée structurellement**, sans parcourir le graphe.
- **Conflit** : {", ".join("`%s` / `%s`" % (a, b) for a, b, _ in conf1)} partagent la place `Libres`. C'est le
  conflit voulu : un seul obtient le jeton, et l'autre ne peut plus que refuser ou abandonner.
- **Quasi-vivant** : toutes les transitions peuvent être franchies au moins une fois.

<figure><img src="figures/graphe-E1.png" style="width:82%"><figcaption>Figure 4 — Graphe des marquages de E1 :
{E1["marquages"]} marquages, dont {len(E1["morts"])} blocages (cadres rouges).</figcaption></figure>

**Problème constaté.** Le graphe se termine par **{len(E1["morts"])} marquages morts**, où les deux utilisateurs sont
refusés ou ont annulé. Le réseau **n'est pas vivant**. Dans ces marquages, **aucune** des {len(E1["non_vivantes"])} transitions ne
peut plus jamais être franchie. Depuis ces marquages, M0 n'est plus accessible : le réseau **n'est pas réversible**.
`Refusee_Ui` et `Annulee_Ui` sont des **puits**. Un utilisateur refusé ou qui a annulé ne peut jamais
redemander la place, même si elle se libère, ce qui ne correspond pas à un vrai système de réservation.

> **Remarque — deux interprétations du refus.** Notre version d'origine garde `refuser_Ui` par un **arc de lecture**
> sur `Occupees` (boucle `Occupees → refuser_Ui → Occupees`) au lieu de l'arc inhibiteur sur `Libres`. Comme
> `Libres + Occupees = 1`, « Libres vide » équivaut à « Occupees marquée » : les deux réseaux ont le même graphe de
> marquages. La version à arc de lecture reste un réseau P/T ordinaire. Le dossier `../2/mimobn/` contient cette
> variante pour chaque étape, avec les mêmes résultats.

> **Problème → étape 2.** Il faut permettre de **revenir en attente** après un refus ou une annulation, afin de
> supprimer les blocages et de rendre le réseau vivant et réversible.

## 6. Étape 2 — Retour après refus ou annulation

**Modélisation.** Deux transitions sont ajoutées par utilisateur (en vert) : `retour_refus_Ui`
(`Refusee_Ui → Attente_Ui`) et `reessayer_Ui` (`Annulee_Ui → Attente_Ui`). L'abandon d'une attente mène aussi à
`Annulee_Ui`, ce qui permet de réessayer après un abandon.

<figure><img src="figures/E2.png"><figcaption>Figure 5 — E2 : les transitions de retour (en vert) referment le cycle
de chaque utilisateur.</figcaption></figure>

**Propriétés obtenues.** {E2["marquages"]} marquages et **aucun blocage**. Le réseau est **vivant** : depuis
n'importe quel marquage, chacune des {E2["transitions"]} transitions peut encore être franchie. Il est
**réversible**, M0 étant un état d'accueil. Les invariants de l'étape 1 sont conservés : les transitions de retour
déplacent le jeton de l'utilisateur sans toucher à la ressource. Le réseau reste donc **sauf**, avec exclusion
mutuelle.

<figure><img src="figures/graphe-E2.png" style="width:92%"><figcaption>Figure 6 — Graphe des marquages de E2 : plus
aucun cadre rouge. Les arcs gris remontent vers des marquages antérieurs (b = abandonner, e = réessayer,
t = retour après refus, f = refuser, x = annuler, r = réserver).</figcaption></figure>

**Problème constaté.** Avec deux utilisateurs, un seul peut attendre pendant que l'autre détient la place. Avec
**trois utilisateurs** (réseau E2b : même structure étendue à U3, avec U1 confirmé et U2, U3 en attente),
l'annulation de U1 rend la place alors que deux utilisateurs attendent :

{table_scenario(sc2b, U3)}

Les transitions {" et ".join("`%s`" % t for t in act2b)} sont alors **en conflit** sur l'unique jeton de `Libres`.
Le réseau ne dit pas laquelle doit l'emporter : le choix est **non déterministe**. E2b est vivant et réversible
({E2b["marquages"]} marquages), mais il n'est **pas équitable**. Pour chacun des trois utilisateurs, il existe un
cycle où il reste en attente pendant que les autres réservent, annulent et reviennent : **famine possible**
pour U1, U2 et U3.

> **Problème → étape 3.** Il faut une **règle d'arbitrage** qui résout le conflit : une priorité entre utilisateurs.

## 7. Étape 3 — Trois utilisateurs et priorité U1 > U2 > U3

**Scénario.** U1 a déjà confirmé, U2 attend et U3 arrive. **Modélisation.** Trois **arcs inhibiteurs** (en vert)
expriment la priorité : `Attente_U1 ⊸ reserver_U2`, `Attente_U1 ⊸ reserver_U3` et `Attente_U2 ⊸ reserver_U3`.
Un utilisateur ne peut réserver que si aucun utilisateur plus prioritaire n'attend. Seul le test à zéro de l'arc
inhibiteur permet d'exprimer « personne n'attend » sans consommer de jeton.

<figure><img src="figures/E3.png"><figcaption>Figure 7 — E3 : arcs de priorité en vert. Ils partent des places
d'attente des utilisateurs prioritaires.</figcaption></figure>

**Propriétés obtenues.** {E3["marquages"]} marquages, aucun blocage, vivant, réversible, sauf, exclusion mutuelle.
**Priorité respectée** : aucun franchissement de `reserver_X` n'a lieu alors qu'un utilisateur plus prioritaire
attend ({E3["viol"]} violation sur les {E3["arcs"]} arcs du graphe). Le conflit de l'étape 2 est résolu : U1 n'est
plus jamais dépassé (famine impossible pour U1). En revanche, **famine possible** pour U2 et U3 : une priorité
fixe laisse les moins prioritaires attendre tant que les plus prioritaires reviennent.

**Problème constaté.** Le cahier des charges a ensuite précisé un autre scénario : **U3 détient la place**, U1 et U2
attendent, et **U1 doit passer après U2**. L'ordre U1 > U2 > U3 ne convient plus.

> **Problème → étape 4.** Il faut adapter les arcs de priorité au nouvel ordre U2 > U1 > U3.

## 8. Étape 4 — U3 confirmé, priorité U2 > U1 > U3

**Modélisation.** Le marquage initial devient `Confirmee_U3 = Occupees = 1`, avec U1 et U2 en attente. L'arc
`Attente_U1 ⊸ reserver_U2` est remplacé par `Attente_U2 ⊸ reserver_U1` (en vert). Les deux arcs vers `reserver_U3`
sont conservés.

<figure><img src="figures/E4.png"><figcaption>Figure 8 — E4 : le nouvel arc de priorité (en vert) fait passer U2
avant U1.</figcaption></figure>

**Propriétés obtenues.** {E4["marquages"]} marquages, aucun blocage, vivant, réversible, sauf, exclusion mutuelle,
et la priorité U2 > U1 > U3 est respectée ({E4["viol"]} violation).

**Problème constaté — perte d'équité.** En simulant le réseau, nous avons rejoué le scénario suivant : U2 abandonne,
puis réessaie, puis U3 libère la place.

{table_scenario(sc4, U3)}

Dans M3, la seule réservation possible est {", ".join("`%s`" % t for t in act4)}. U2 est revenu **directement dans
`Attente_U2`** et a **retrouvé sa priorité**. Il passe donc devant U1, qui attendait depuis le début. La priorité
est attachée à la personne et non à sa position dans la file : quitter puis revenir permet de doubler les autres.
Le graphe le confirme : **famine possible** pour U1 et U3, car un cycle « U2 réserve, annule, revient » peut se
répéter indéfiniment pendant qu'ils attendent.

> **Problème → étape 5.** Un utilisateur qui revient ne doit pas retrouver sa place devant ceux qui attendent déjà.
> Il faut distinguer « revenir » de « attendre ».

## 9. Étape 5 — Un état Demande avant l'attente (version actuelle)

**Modélisation.** Une place `Demande_Ui` (en vert) est ajoutée **avant** `Attente_Ui`. Les retours (`retour_refus_Ui`,
`reessayer_Ui`) mènent désormais à `Demande_Ui`. La nouvelle transition `rejoindre_Ui` fait passer de
`Demande_Ui` à `Attente_Ui`. Elle est gardée par des arcs inhibiteurs : un utilisateur ne rejoint l'attente que
s'il ne dépasse personne qui attend déjà.

| Transition | Arcs inhibiteurs | Justification |
|---|---|---|
| `rejoindre_U2` | `Attente_U1`, `Attente_U3` | U2, le plus prioritaire, dépasserait tous ceux qui attendent |
| `rejoindre_U1` | `Attente_U3` | U1 ne dépasse que U3 (U2 passe déjà avant U1) |
| `rejoindre_U3` | — | U3, le moins prioritaire, ne dépasse personne |

<figure><img src="figures/E5.png"><figcaption>Figure 9 — E5 : états Demande, transitions rejoindre et arcs qui
empêchent de doubler (en vert).</figcaption></figure>

**Vérification du correctif.** Même scénario que dans E4 :

{table_scenario(sc5, U3)}

Dans M3, U2 est retenu dans `Demande_U2`, car U1 attend toujours. La seule réservation possible est
{", ".join("`%s`" % t for t in act5)} : **c'est bien U1 qui obtient la place.**

**Propriétés obtenues.**

- {E5["marquages"]} marquages, **aucun blocage**, **vivant**, **réversible**, **sauf**.
- **P-invariants** (dimension {E5["dim_inv"]}) : `Libres + Occupees = 1`, `Occupees = Σ Confirmee_Ui`, et
  `Demande_Ui + Attente_Ui + Confirmee_Ui + Refusee_Ui + Annulee_Ui = 1` pour chaque utilisateur. L'exclusion
  mutuelle reste démontrée structurellement.
- **Priorité U2 > U1 > U3 respectée** : {E5["viol"]} violation.
- **Plus de famine par dépassement** : aucun cycle ne permet de dépasser indéfiniment un utilisateur en attente.
  Le nombre maximal de réservations faites par d'autres pendant qu'un utilisateur attend est **borné** :

| Utilisateur en attente | E2b (sans priorité) | E4 (avant correctif) | E5 (après correctif) |
|---|---|---|---|
| U1 | {dep(E2b, "U1")} | {dep(E4, "U1")} | **{dep(E5, "U1")}** |
| U2 | {dep(E2b, "U2")} | {dep(E4, "U2")} | **{dep(E5, "U2")}** |
| U3 | {dep(E2b, "U3")} | {dep(E4, "U3")} | **{dep(E5, "U3")}** |

U1 peut être doublé au plus une fois (par U2, prioritaire). U3 peut l'être au plus deux fois (par U2 et U1, s'ils
attendaient déjà). Personne ne peut l'être indéfiniment : l'attente est **bornée**.

## 10. Bilan

| Propriété | E0 | E1 | E2 | E3 | E4 | E5 |
|---|---|---|---|---|---|---|
| Sauf (1-borné) | {oui(E0["sauf"])} ({E0["borne"]}-borné) | {oui(E1["sauf"])} | {oui(E2["sauf"])} | {oui(E3["sauf"])} | {oui(E4["sauf"])} | {oui(E5["sauf"])} |
| Exclusion mutuelle | {oui(E0["exclusion"])} | {oui(E1["exclusion"])} | {oui(E2["exclusion"])} | {oui(E3["exclusion"])} | {oui(E4["exclusion"])} | {oui(E5["exclusion"])} |
| Invariant `Libres + Occupees = 1` | {oui(E0["inv_ressource"])} | {oui(E1["inv_ressource"])} | {oui(E2["inv_ressource"])} | {oui(E3["inv_ressource"])} | {oui(E4["inv_ressource"])} | {oui(E5["inv_ressource"])} |
| Sans blocage | {oui(not E0["morts"])} | {oui(not E1["morts"])} | {oui(not E2["morts"])} | {oui(not E3["morts"])} | {oui(not E4["morts"])} | {oui(not E5["morts"])} |
| Quasi-vivant | {oui(E0["quasi"])} | {oui(E1["quasi"])} | {oui(E2["quasi"])} | {oui(E3["quasi"])} | {oui(E4["quasi"])} | {oui(E5["quasi"])} |
| Vivant | {oui(E0["vivant"])} | {oui(E1["vivant"])} | {oui(E2["vivant"])} | {oui(E3["vivant"])} | {oui(E4["vivant"])} | {oui(E5["vivant"])} |
| Réversible | {oui(E0["reversible"])} | {oui(E1["reversible"])} | {oui(E2["reversible"])} | {oui(E3["reversible"])} | {oui(E4["reversible"])} | {oui(E5["reversible"])} |
| Arbitrage du conflit | — | — | **non** | oui | oui | oui |
| Sans famine par dépassement | — | — | **non** | **non** | **non** | oui |

Chaque étape conserve les acquis de la précédente et corrige un défaut précis :

1. **E0 → E1** : la sûreté et l'exclusion mutuelle ont été obtenues en consommant la ressource au moment de
   l'attribution. Elles sont démontrées par P-invariants.
2. **E1 → E2** : les blocages ont été supprimés par les transitions de retour, ce qui donne un réseau vivant et
   réversible.
3. **E2 → E3** : le conflit entre utilisateurs a été arbitré par des arcs inhibiteurs de priorité.
4. **E3 → E4** : l'ordre de priorité a été adapté au scénario « U3 confirmé, U2 avant U1 ».
5. **E4 → E5** : la reprise de priorité a été supprimée par l'état `Demande`. Ce changement élimine la famine
   par dépassement et donne une attente bornée.

**Limites et prolongements.** La priorité reste fixe entre utilisateurs qui attendent en même temps. Une vraie
file FIFO, qui sert les utilisateurs dans l'ordre d'arrivée, demanderait de mémoriser l'ordre d'arrivée. Cela
passe par un réseau **coloré** (jetons portant un numéro) ou par un compteur d'ancienneté. Le temps d'attente
réel pourrait ensuite être étudié avec un réseau **temporisé** ou **stochastique**.

<div class="annex"><b>Annexe — reproduire les résultats.</b> Dans <code>pipe/rapport-evolution/</code> :
<code>python construire.py</code> reconstruit <code>modeles/</code>, les figures, <code>rapport.md</code>,
<code>rapport.pdf</code> et <code>resultats.json</code>. Les fichiers <code>modeles/E*.pnml</code> s'ouvrent dans
PIPE 5 (Fichier &gt; Ouvrir). Les variantes à arc de lecture se trouvent dans <code>../2/mimobn/</code>. Pour
ouvrir directement un fichier, utiliser <code>PIPE-ouvrir.bat fichier.pnml</code>. Les fichiers d'origine ne
s'ouvraient pas dans PIPE 5, qui refusait les balises <code>&lt;graphics/&gt;</code> et <code>&lt;tagged&gt;</code>
dans les arcs ainsi que le format ISO PNML avec espace de noms. Ils ont été corrigés avant cette étude.</div>
"""


CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; line-height: 1.45; color: #1f2937; }
h1 { font-size: 19pt; color: #1e3a5f; margin: 0 0 2px; }
.subtitle { font-size: 12pt; color: #475569; margin: 0 0 6px; }
.meta { font-size: 9.5pt; color: #334155; border-bottom: 2px solid #1e3a5f; padding-bottom: 8px; margin-bottom: 14px; }
h2 { font-size: 14pt; color: #1e3a5f; border-bottom: 1px solid #cbd5e1; padding-bottom: 3px; margin-top: 20px; page-break-after: avoid; }
h3 { font-size: 11.5pt; color: #0f766e; margin-top: 14px; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 10px; font-size: 8.8pt; }
tr { page-break-inside: avoid; }
th { background: #1e3a5f; color: white; text-align: left; padding: 4px 6px; }
td { border: 1px solid #cbd5e1; padding: 3px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #f8fafc; }
code { font-family: Consolas, monospace; font-size: 8.6pt; background: #f1f5f9; padding: 0 3px; border-radius: 3px; }
figure { margin: 10px 0; text-align: center; page-break-inside: avoid; }
figure img { width: 100%; }
figcaption { font-size: 8.8pt; color: #475569; margin-top: 3px; font-style: italic; }
blockquote { margin: 10px 0; padding: 6px 12px; background: #fff7ed; border-left: 4px solid #ea580c; page-break-inside: avoid; }
blockquote p { margin: 2px 0; }
ul, ol { margin: 4px 0 8px; padding-left: 20px; }
li { margin: 2px 0; }
.legend { font-size: 8.8pt; background: #f1f5f9; border-left: 3px solid #0f766e; padding: 6px 8px; }
.annex { margin-top: 16px; font-size: 8.8pt; background: #f8fafc; border: 1px solid #cbd5e1; padding: 6px 12px; page-break-inside: avoid; }
"""


def pdf(md):
    html = markdown.markdown(md, extensions=["tables", "md_in_html"])
    page = ('<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Évolution du réseau de Petri - '
            'Mohamed BENALIA</title><style>%s</style></head><body>%s</body></html>' % (CSS, html))
    tmp = ICI / "_rapport.html"
    tmp.write_text(page, encoding="utf-8")
    sys.path.insert(0, str(ICI.parents[4] / ".formal-tools" / "browser-tools"))
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True)
        pg = b.new_page()
        pg.goto(tmp.as_uri())
        pg.wait_for_timeout(800)
        pg.pdf(path=str(ICI / "rapport.pdf"), format="A4", print_background=True,
               margin={"top": "16mm", "bottom": "16mm", "left": "15mm", "right": "15mm"},
               display_header_footer=True, header_template="<span></span>",
               footer_template='<div style="width:100%;font-size:8px;color:#94a3b8;text-align:center;'
                               'font-family:Segoe UI,Arial">Mohamed BENALIA · Méthodes formelles · Évolution du '
                               'réseau de Petri · page <span class="pageNumber"></span> / '
                               '<span class="totalPages"></span></div>')
        b.close()
    tmp.unlink()


if __name__ == "__main__":
    main()
