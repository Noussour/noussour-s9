"""Construit tout le rendu : analyse des reseaux, figures, fichiers PIPE (.pnml),
resultats.json, rapport.md et rapport.pdf.

Usage : python construire.py
(le PDF est imprime par Microsoft Edge via Playwright, comme dans les autres TP du depot)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import markdown

from figures import net_figure, reach_figure, scenario_figure, state_label
from modeles import TITRES, build, to_pnml, users

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
PIPE = ROOT / "pipe"
FIG.mkdir(exist_ok=True)
PIPE.mkdir(exist_ok=True)

ETAT = {"Repos": "au repos", "Demande": "en attente", "Reservee": "place réservée", "Annulee": "a annulé"}


# ------------------------------------------------------------------ analyse
def describe(m):
    parts = []
    for u in users(2):
        for base, txt in ETAT.items():
            if m.get(base + "_" + u, 0):
                parts.append("%s %s" % (u, txt))
    return ", ".join(parts) + ", Disponible = %d" % m["Disponible"]


def analyse(kind, n=2, k=1):
    net = build(kind, n, k)
    rg = net.reachability()
    U = users(n)
    res = {
        "places": len(net.places),
        "transitions": len(net.transitions),
        "arcs": net.arc_counts(),
        "etats": len(rg["states"]),
        "arcs_graphe": len(rg["edges"]),
        "etats_morts": len(rg["dead"]),
        "max_reservees": max(sum(m["Reservee_" + u] for u in U) for m in rg["states"]),
        "max_attente": max(sum(m["Demande_" + u] for u in U) for m in rg["states"]),
    }
    seat = {"Disponible": 1, **{"Reservee_" + u: 1 for u in U}}
    res["inv_place"] = net.is_p_invariant(seat)
    if kind in ("r3", "r3_perte"):
        res["inv_place_annulee"] = net.is_p_invariant({**seat, **{"Annulee_" + u: 1 for u in U}})
    per_user = []
    for u in U:
        w = {p: 1 for p in net.places if p.endswith("_" + u)}
        per_user.append(net.is_p_invariant(w))
    res["inv_utilisateur"] = all(per_user)
    if n == 2 and k == 1:
        res["morts"] = [describe(rg["states"][i]) for i in rg["dead"]]
        res["morts_ids"] = rg["dead"]
    return net, rg, res


def main():
    results, nets = {}, {}
    for kind in ("r1", "r2", "r3", "r3_perte"):
        net, rg, res = analyse(kind)
        nets[kind] = (net, rg)
        results[kind] = res
        (PIPE / ("%s.pnml" % kind)).write_text(to_pnml(net), encoding="iso-8859-1")

    scale = []
    for n in (2, 3, 4):
        for k in (1, 2):
            if k >= n:
                continue
            row = {"n": n, "k": k}
            for kind in ("r1", "r2", "r3"):
                _, _, r = analyse(kind, n, k)
                row[kind] = r["etats"]
                row[kind + "_morts"] = r["etats_morts"]
                row[kind + "_ok"] = r["max_reservees"] <= k
            scale.append(row)
    results["passage_echelle"] = scale
    (ROOT / "resultats.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---------------------------------------------------------------- figures
    r1, g1 = nets["r1"]
    r2, g2 = nets["r2"]
    r3, g3 = nets["r3"]
    rp, gp = nets["r3_perte"]
    net_figure(r1, FIG / "r1_reseau.png")
    net_figure(r3, FIG / "r3_reseau.png")
    scenario_figure(r1, r1.run(["demander_U1", "accorder_U1", "demander_U2"]), FIG / "r1_simulation.png")
    scenario_figure(r2, r2.run(["demander_U1", "demander_U2", "accorder_U2"]), FIG / "r2_simulation.png")
    scenario_figure(r3, r3.run(["demander_U1", "accorder_U1", "demander_U2", "annuler_U1", "accorder_U2"]),
                    FIG / "r3_simulation.png")
    scenario_figure(rp, rp.run(["demander_U1", "accorder_U1", "demander_U2", "annuler_U1"])[3:],
                    FIG / "r3_perte_simulation.png", offset=3)
    reach_figure(r1, g1, FIG / "r1_accessibilite.png")
    reach_figure(r2, g2, FIG / "r2_accessibilite.png")
    reach_figure(r3, g3, FIG / "r3_accessibilite.png")
    for old in FIG.glob("test_*.png"):
        old.unlink()

    md = rapport(results, r3)
    (ROOT / "rapport.md").write_text(md, encoding="utf-8")
    pdf(md)
    print("ok :", {k: (v["etats"], v["etats_morts"]) for k, v in results.items() if k != "passage_echelle"})


# ------------------------------------------------------------------ rapport
def oui(b):
    return "oui" if b else "**non**"


def rapport(R, r3net):
    r1, r2, r3, rp = R["r1"], R["r2"], R["r3"], R["r3_perte"]

    # matrice d'incidence du reseau 3
    C = r3net.incidence()
    tnames = [t["name"] for t in r3net.transitions]
    head = "| Place | " + " | ".join(t.replace("_", "\\_") for t in tnames) + " |"
    sep = "|---" * (len(tnames) + 1) + "|"
    rows = ["| %s | %s |" % (p.replace("_", "\\_"), " | ".join(("%+d" % C[p][t]) if C[p][t] else "0" for t in tnames))
            for p in r3net.places]
    incidence = "\n".join([head, sep] + rows)

    scale = "\n".join("| %d | %d | %d (%d) | %d (%d) | %d (%d) |" % (
        s["n"], s["k"], s["r1"], s["r1_morts"], s["r2"], s["r2_morts"], s["r3"], s["r3_morts"])
        for s in R["passage_echelle"])
    all_safe = all(s["r1_ok"] and s["r2_ok"] and s["r3_ok"] for s in R["passage_echelle"])

    return f"""# Arcs inhibiteurs, concurrence et annulation

<p class="subtitle">Modélisation d'un système de réservation par réseaux de Petri</p>

<p class="meta"><b>Étudiant :</b> Mohamed BENALIA &nbsp;·&nbsp; <b>Module :</b> Méthodes formelles &nbsp;·&nbsp; <b>Enseignant :</b> M. Mekahlia &nbsp;·&nbsp; Novembre 2026</p>

## 1. Hypothèses et modélisation

Deux utilisateurs, `U1` et `U2`, veulent réserver **une seule place**. Chaque utilisateur suit le même cycle et la place libre est représentée par un jeton partagé.

| Place | Signification | Marquage initial |
|---|---|---|
| `Repos_Ui` | l'utilisateur n'a encore rien demandé | 1 |
| `Demande_Ui` | demande soumise, en attente de réponse | 0 |
| `Reservee_Ui` | la place est attribuée à l'utilisateur | 0 |
| `Annulee_Ui` | réservation annulée (réseau 3 uniquement) | 0 |
| `Disponible` | nombre de places encore libres | 1 |

| Transition | Rôle |
|---|---|
| `demander_Ui` | l'utilisateur soumet sa demande |
| `accorder_Ui` | le système lui attribue la place (consomme le jeton de `Disponible`) |
| `annuler_Ui` | l'utilisateur annule sa réservation (réseau 3) |

**Sémantique de l'arc inhibiteur.** Un arc inhibiteur `p ⊸ t` de poids 1 rend `t` franchissable seulement si `p` est **vide**. Il teste une absence de jeton et ne consomme rien.

**Outils.** Chaque réseau est fourni au format PIPE 5 (`pipe/*.pnml`). Les figures de simulation, les graphes d'accessibilité et tous les chiffres du rapport sont produits par le programme du dossier (`petri.py`, `construire.py`). Ce programme applique la même règle de franchissement que PIPE.

<p class="legend"><b>Lecture des figures :</b> <span class="sw" style="background:#f59e0b"></span> transition qui vient d'être franchie, <span class="sw" style="background:#34d399"></span> transition franchissable, <span class="sw" style="background:#e2e8f0"></span> transition bloquée, <span style="color:#dc2626"><b>arc rouge terminé par un cercle</b></span> : arc inhibiteur. Dans les graphes d'accessibilité, un état s'écrit « état de U1, état de U2 | jetons de Disponible » avec R = repos, D = demande, S = réservée, A = annulée. Les arcs sont notés d = demander, a = accorder, x = annuler. Un cadre rouge signale un état mort.</p>

## 2. Partie 1

### 2.1 Réseau 1 : admission contrôlée par arcs inhibiteurs

L'arc inhibiteur sert à n'accepter qu'**une demande en attente à la fois** : `demander_U1` est bloquée tant que `Demande_U2` contient un jeton, et inversement.

| Transition | Consomme | Produit | Arc inhibiteur depuis |
|---|---|---|---|
| `demander_U1` | `Repos_U1` | `Demande_U1` | `Demande_U2` |
| `demander_U2` | `Repos_U2` | `Demande_U2` | `Demande_U1` |
| `accorder_U1` | `Demande_U1`, `Disponible` | `Reservee_U1` | aucun |
| `accorder_U2` | `Demande_U2`, `Disponible` | `Reservee_U2` | aucun |

<figure><img src="figures/r1_reseau.png" style="width:78%"><figcaption>Figure 1 : réseau 1 dans son état initial. Les deux demandes sont possibles.</figcaption></figure>

<figure><img src="figures/r1_simulation.png"><figcaption>Figure 2 : simulation du réseau 1.</figcaption></figure>

- **Étape 1.** `U1` demande. L'arc inhibiteur depuis `Demande_U1` **bloque `demander_U2`** (grise) : `U2` ne peut même pas déposer sa demande.
- **Étape 2.** La place est accordée à `U1` (`Disponible` = 0). `Demande_U1` est vide, donc `demander_U2` redevient franchissable.
- **Étape 3.** `U2` demande, mais `accorder_U2` est bloquée faute de jeton dans `Disponible`. Plus aucune transition n'est franchissable : c'est un **état mort**.

<figure><img src="figures/r1_accessibilite.png" style="width:64%"><figcaption>Figure 3 : graphe d'accessibilité du réseau 1 ({r1['etats']} états, {r1['arcs_graphe']} arcs).</figcaption></figure>

Le graphe ne contient jamais l'état « D D » où les deux utilisateurs attendent en même temps. Les {r1['etats_morts']} états morts sont symétriques : {r1['morts'][0]} ; et {r1['morts'][1]}.

### 2.2 Réseau 2 : demandes concurrentes

Même réseau **sans arc inhibiteur** : chaque utilisateur peut demander à tout moment. Seul le jeton de `Disponible` arbitre l'attribution.

<figure><img src="figures/r2_simulation.png"><figcaption>Figure 4 : simulation du réseau 2.</figcaption></figure>

- **Étape 1.** `U1` demande. Contrairement au réseau 1, `demander_U2` reste franchissable.
- **Étape 2.** Les deux utilisateurs attendent. `accorder_U1` et `accorder_U2` sont franchissables ensemble mais se disputent le même jeton : c'est un **conflit**.
- **Étape 3.** Le système choisit `U2`. Le jeton est consommé et `accorder_U1` est aussitôt désactivée : la place ne peut pas être donnée deux fois. `U1` reste en attente sans issue.

<figure><img src="figures/r2_accessibilite.png" style="width:82%"><figcaption>Figure 5 : graphe d'accessibilité du réseau 2 ({r2['etats']} états, {r2['arcs_graphe']} arcs).</figcaption></figure>

L'état supplémentaire « D D | 1 » (les deux en attente) est le point de conflit : deux arcs en sortent, un par gagnant possible. On retrouve les deux mêmes états morts que dans le réseau 1.

### 2.3 Comparaison des deux réseaux

| Critère | Réseau 1 (arcs inhibiteurs) | Réseau 2 (concurrent) |
|---|---|---|
| Traitement des demandes | une seule demande en attente à la fois ; les autres ne peuvent pas être déposées | toutes les demandes sont acceptées en attente |
| Condition d'acceptation | `Demande_Ui` = 1 et `Disponible` ≥ 1 | identique |
| Rôle de l'arc inhibiteur | contrôle l'**entrée** et évite que deux demandes coexistent | aucun |
| Conflit pour la place | jamais (au plus {r1['max_attente']} demande en attente) | oui, jusqu'à {r2['max_attente']} demandes en attente |
| Situations de blocage | {r1['etats_morts']} états morts : l'utilisateur non servi attend sans fin | {r2['etats_morts']} états morts, mêmes situations |
| Transitions / arcs du réseau | {r1['transitions']} / {r1['arcs']['total']} dont {r1['arcs']['inhibitor']} inhibiteurs | {r2['transitions']} / {r2['arcs']['total']} |
| États accessibles / arcs du graphe | {r1['etats']} / {r1['arcs_graphe']} | {r2['etats']} / {r2['arcs_graphe']} |
| Double attribution | impossible (au plus {r1['max_reservees']} réservation) | impossible (au plus {r2['max_reservees']} réservation) |
| Avantages | pas de conflit, moins d'états, ordre de service clair | plus fidèle à la réalité, les demandes ne sont pas refusées à l'entrée |
| Inconvénients | restrictif : un utilisateur en attente bloque l'entrée des autres | choix non déterministe du gagnant, aucune équité garantie |

**Analyse.** Dans les deux réseaux, la sûreté (une seule réservation) vient du **jeton unique de `Disponible`**, pas de l'arc inhibiteur. Le réseau 1 a moins d'états : l'inhibiteur supprime l'entrelacement où les deux demandes sont déposées. Mais il ne supprime pas le blocage : l'utilisateur non servi reste coincé dans les deux cas, car rien ne libère la place.

**Choix : le réseau 2.** Il décrit fidèlement un système de réservation où plusieurs clients demandent en même temps la dernière place. Le conflit y est bien résolu (un seul gagnant) et il n'a pas besoin d'arc inhibiteur. Or les arcs inhibiteurs donnent aux réseaux de Petri la puissance d'une machine de Turing, si bien que l'accessibilité n'y est plus décidable en général. Le réseau 1 reste utile si l'on veut une admission strictement une par une.

## 3. Partie 2 : réseau 3, annulation

On part du réseau 2 et on ajoute pour chaque utilisateur :

| Transition | Consomme | Produit |
|---|---|---|
| `annuler_U1` | `Reservee_U1` | `Annulee_U1`, **`Disponible`** |
| `annuler_U2` | `Reservee_U2` | `Annulee_U2`, **`Disponible`** |

<figure><img src="figures/r3_simulation.png"><figcaption>Figure 6 : simulation du réseau 3. U1 réserve, U2 attend, U1 annule, U2 obtient la place.</figcaption></figure>

<figure><img src="figures/r3_accessibilite.png" style="width:100%"><figcaption>Figure 7 : graphe d'accessibilité du réseau 3 ({r3['etats']} états, {r3['arcs_graphe']} arcs).</figcaption></figure>

**La place redevient-elle disponible ?** Oui. L'arc `annuler_U1 → Disponible` remet un jeton dans `Disponible` (étape 4). L'invariant « `Disponible` + `Reservee_U1` + `Reservee_U2` = 1 » reste vrai : à tout moment la place est soit libre, soit réservée par exactement un utilisateur.

**U2 est-il accepté automatiquement ?** Non. Après l'annulation, `accorder_U2` devient **franchissable** (verte à l'étape 4), mais un réseau de Petri n'oblige jamais à franchir une transition. Il faut un franchissement explicite (étape 5) : le réseau dit ce qui *peut* arriver, pas ce qui arrive forcément.

**Conditions pour confirmer U2.** `accorder_U2` exige `Demande_U2` = 1 (U2 a demandé) **et** `Disponible` ≥ 1 (la place a été libérée). S'il y avait d'autres demandeurs, U2 devrait aussi gagner le conflit sur ce jeton, sans aucune priorité.

**Situation de blocage ou de perte ?** Aucune perte de place : l'invariant le garantit. Le seul état mort ({r3['morts'][0]}) est la fin normale du scénario, où la place est revenue libre. Il reste un risque de **famine** : dans l'état « S D | 0 », U2 attend tant que U1 n'annule pas. Cet état n'est pas mort, car `annuler_U1` reste franchissable, mais rien n'oblige U1 à annuler.

**Contre-exemple : annulation sans retour de la place.** Si l'on oublie l'arc `annuler_Ui → Disponible`, la place est **perdue**. Le réseau a alors {rp['etats']} états et {rp['etats_morts']} états morts ({rp['morts'][0]}). L'invariant de conservation de la place est violé, et le jeton disparaît dans `Annulee_U1`.

<figure><img src="figures/r3_perte_simulation.png"><figcaption>Figure 8 : variante fautive. Après l'annulation, Disponible reste vide et U2 est bloqué.</figcaption></figure>

## 4. Vérifications complémentaires

### 4.1 Invariants de place (matrice d'incidence)

La matrice d'incidence `C = Post − Pre` du réseau 3 est donnée ci-dessous. Les arcs inhibiteurs n'y figurent pas, car ils ne déplacent aucun jeton. Un vecteur de poids `y` est un P-invariant si `yᵀ·C = 0` : la somme pondérée des jetons ne change par aucun franchissement.

{incidence}

| Invariant vérifié | Réseau 1 | Réseau 2 | Réseau 3 | Variante fautive |
|---|---|---|---|---|
| `Disponible + Reservee_U1 + Reservee_U2 = 1` (conservation de la place) | {oui(r1['inv_place'])} | {oui(r2['inv_place'])} | {oui(r3['inv_place'])} | {oui(rp['inv_place'])} |
| `Disponible + Σ Reservee + Σ Annulee = 1` | sans objet | sans objet | {oui(r3['inv_place_annulee'])} | {oui(rp['inv_place_annulee'])} |
| `Repos_Ui + Demande_Ui + Reservee_Ui (+ Annulee_Ui) = 1` (un état par utilisateur) | {oui(r1['inv_utilisateur'])} | {oui(r2['inv_utilisateur'])} | {oui(r3['inv_utilisateur'])} | {oui(rp['inv_utilisateur'])} |

Dans le réseau 3, la deuxième somme n'est pas un invariant, et c'est voulu : `annuler_Ui` rend la place **et** garde une trace dans `Annulee_Ui`. Dans la variante fautive c'est l'inverse : seule la deuxième somme se conserve, car le jeton de la place est passé dans `Annulee_Ui` au lieu de revenir dans `Disponible`.

### 4.2 Passage à l'échelle

Nombre d'états accessibles (et d'états morts entre parenthèses) pour `n` utilisateurs et `k` places, calculé avec les mêmes modèles généralisés :

| n | k | Réseau 1 | Réseau 2 | Réseau 3 |
|---|---|---|---|---|
{scale}

L'arc inhibiteur limite fortement la croissance de l'espace d'états, puisqu'une seule demande peut attendre. En revanche, il **multiplie les états morts** quand le nombre d'utilisateurs augmente : un utilisateur en attente sans place bloque aussi tous ceux qui n'ont pas encore pu demander. Le réseau 3 n'a toujours qu'un seul état mort, la fin normale où tout le monde a annulé. Dans tous ces cas, aucune configuration ne dépasse `k` réservations simultanées ({'vérifié pour toutes les tailles' if all_safe else 'ATTENTION : violation détectée'}).

## 5. Conclusion

| | Réseau 1 | Réseau 2 | Réseau 3 |
|---|---|---|---|
| Admission des demandes | une à la fois | libre | libre |
| Conflit sur la place | non | oui | oui |
| États accessibles (2 utilisateurs, 1 place) | {r1['etats']} | {r2['etats']} | {r3['etats']} |
| Double attribution | impossible | impossible | impossible |
| Utilisateur bloqué sans issue | oui | oui | non (attente tant que l'autre n'annule pas) |

L'arc inhibiteur règle l'**accès** aux demandes, pas l'**exclusion** sur la place : celle-ci est assurée par le jeton de `Disponible` dans les trois réseaux. Le réseau concurrent est le plus réaliste. L'annulation avec retour du jeton supprime les blocages définitifs, à condition de ne pas oublier l'arc qui rend la place.

<div class="annex" markdown="1">

**Fichiers du dossier**

- `pipe/r1.pnml`, `pipe/r2.pnml`, `pipe/r3.pnml`, `pipe/r3_perte.pnml` : les réseaux à ouvrir dans PIPE 5 (*File → Open*), puis à simuler en mode *Animation*.
- `petri.py` : moteur de réseaux de Petri avec arcs inhibiteurs (franchissement, graphe d'accessibilité, invariants).
- `modeles.py`, `figures.py`, `construire.py` : construction des réseaux, figures et rapport. La commande `python construire.py` régénère tout.
- `resultats.json` : tous les chiffres utilisés dans ce rapport.

</div>
"""


CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; line-height: 1.45; color: #1f2937; }
h1 { font-size: 21pt; color: #1e3a5f; margin: 0 0 2px; }
.subtitle { font-size: 12pt; color: #475569; margin: 0 0 6px; }
.meta { font-size: 9.5pt; color: #334155; border-bottom: 2px solid #1e3a5f; padding-bottom: 8px; margin-bottom: 14px; }
h2 { font-size: 14pt; color: #1e3a5f; border-bottom: 1px solid #cbd5e1; padding-bottom: 3px; margin-top: 20px; page-break-after: avoid; }
h3 { font-size: 11.5pt; color: #0f766e; margin-top: 14px; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 10px; font-size: 9pt; page-break-inside: avoid; }
th { background: #1e3a5f; color: white; text-align: left; padding: 4px 6px; }
td { border: 1px solid #cbd5e1; padding: 4px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #f8fafc; }
code { font-family: Consolas, monospace; font-size: 8.8pt; background: #f1f5f9; padding: 0 3px; border-radius: 3px; }
figure { margin: 10px 0; text-align: center; page-break-inside: avoid; }
figure img { width: 96%; }
figcaption { font-size: 8.8pt; color: #475569; margin-top: 3px; font-style: italic; }
ul { margin: 4px 0 8px; padding-left: 20px; }
li { margin: 2px 0; }
.legend { font-size: 8.8pt; background: #f1f5f9; border-left: 3px solid #0f766e; padding: 6px 8px; }
.sw { display: inline-block; width: 12px; height: 8px; border: 1px solid #1e3a5f; vertical-align: middle; }
.annex { margin-top: 16px; font-size: 9pt; background: #f8fafc; border: 1px solid #cbd5e1; padding: 6px 12px; page-break-inside: avoid; }
"""


def pdf(md):
    html = markdown.markdown(md, extensions=["tables", "md_in_html"])
    page = ('<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Arcs inhibiteurs - Mohamed BENALIA</title>'
            '<style>%s</style></head><body>%s</body></html>' % (CSS, html))
    tmp = ROOT / "_rapport.html"
    tmp.write_text(page, encoding="utf-8")
    sys.path.insert(0, str(ROOT.parents[3] / ".formal-tools" / "browser-tools"))
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True)
        pg = b.new_page()
        pg.goto(tmp.as_uri())
        pg.wait_for_timeout(600)
        pg.pdf(path=str(ROOT / "rapport.pdf"), format="A4", print_background=True,
               margin={"top": "16mm", "bottom": "16mm", "left": "15mm", "right": "15mm"},
               display_header_footer=True, header_template="<span></span>",
               footer_template='<div style="width:100%;font-size:8px;color:#94a3b8;text-align:center;font-family:Segoe UI,Arial">'
                               'Mohamed BENALIA · Méthodes formelles · page <span class="pageNumber"></span> / '
                               '<span class="totalPages"></span></div>')
        b.close()
    tmp.unlink()


if __name__ == "__main__":
    main()
