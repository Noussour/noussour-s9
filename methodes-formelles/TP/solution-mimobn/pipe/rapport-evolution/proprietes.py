"""Proprietes comportementales et structurelles d'un reseau PIPE (.pnml), pour le rapport d'evolution.

Semantique de PIPE : un arc normal consomme / produit des jetons, un arc inhibiteur de poids w rend la
transition franchissable seulement si la place contient moins de w jetons (ici : place vide).
"""
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyse import Petri  # noqa: E402


def cle(m):
    return tuple(sorted(m.items()))


def explorer(n):
    """Graphe des marquages accessibles : etats {cle: marquage}, succ {cle: [(t, cle)]}, ordre BFS."""
    etats, succ, ordre, file = {cle(n.m0): n.m0}, {}, [cle(n.m0)], deque([n.m0])
    while file:
        m = file.popleft()
        succ[cle(m)] = []
        for t in n.actives(m):
            k = n.tirer(m, t)
            succ[cle(m)].append((t, cle(k)))
            if cle(k) not in etats:
                etats[cle(k)] = k
                ordre.append(cle(k))
                file.append(k)
    return etats, succ, ordre


def accessibles_depuis(succ, depart):
    vus, file = {depart}, deque([depart])
    while file:
        for _, k in succ[file.popleft()]:
            if k not in vus:
                vus.add(k)
                file.append(k)
    return vus


def incidence(n):
    """C[p][t] = Post - Pre (les arcs inhibiteurs ne modifient pas le marquage)."""
    C = {p: {t: 0 for t in n.trans} for p in n.m0}
    for t in n.trans:
        for p, w, typ in n.pre[t]:
            if typ == "normal":
                C[p][t] -= w
        for p, w in n.post[t]:
            C[p][t] += w
    return C


def est_invariant(n, poids):
    """Verifie structurellement y . C = 0 pour le vecteur de poids {place: coefficient}."""
    C = incidence(n)
    return all(sum(c * C[p][t] for p, c in poids.items()) == 0 for t in n.trans)


def proprietes(chemin, utilisateurs=("U1", "U2")):
    n = Petri(chemin)
    etats, succ, ordre = explorer(n)
    m0 = cle(n.m0)
    nb_arcs = sum(len(s) for s in succ.values())
    borne = max(max(m.values()) for m in etats.values())
    morts = [k for k, s in succ.items() if not s]
    tirees = {t for s in succ.values() for t, _ in s}
    quasi = set(n.trans) <= tirees
    # vivacite : depuis tout marquage accessible, chaque transition peut encore etre franchie
    futur = {k: accessibles_depuis(succ, k) for k in etats}
    tir_depuis = {k: {t for e in futur[k] for t, _ in succ[e]} for k in etats}
    vivantes = [t for t in n.trans if all(t in tir_depuis[k] for k in etats)]
    reversible = all(m0 in futur[k] for k in etats)
    L = next(p for p in n.m0 if p.startswith("Libre"))
    O = next(p for p in n.m0 if p.startswith("Occup"))
    conf = [p for p in n.m0 if p.startswith("Confirmee_")]
    exclusion = all(sum(etats[k][c] for c in conf) <= 1 for k in etats)
    inv_ressource = est_invariant(n, {L: 1, O: 1})
    inv_occ = est_invariant(n, {O: 1, **{c: -1 for c in conf}})
    inv_users = all(est_invariant(n, {p: 1 for p in n.m0 if p.endswith("_" + u)}) for u in utilisateurs)
    return dict(n=n, etats=etats, succ=succ, ordre=ordre, marquages=len(etats), arcs=nb_arcs, borne=borne,
                sauf=borne <= 1, morts=morts, quasi=quasi, non_tirees=sorted(set(n.trans) - tirees),
                vivant=len(vivantes) == len(n.trans), non_vivantes=sorted(set(n.trans) - set(vivantes)),
                reversible=reversible, exclusion=exclusion, inv_ressource=inv_ressource, inv_occ=inv_occ,
                inv_users=inv_users, places=len(n.m0), transitions=len(n.trans),
                inhibiteurs=sum(1 for t in n.trans for _, _, typ in n.pre[t] if typ == "inhibitor"))


def violations_priorite(r, ordre_prio):
    """Nombre de franchissements de reserver_X alors qu'un utilisateur plus prioritaire est en attente."""
    rang = {u: i for i, u in enumerate(ordre_prio)}
    v = 0
    for k, s in r["succ"].items():
        m = r["etats"][k]
        for t, _ in s:
            if t.startswith("reserver_"):
                u = t.split("_")[1]
                if any(m["Attente_" + w] for w in ordre_prio if rang[w] < rang[u]):
                    v += 1
    return v


def famine(r, u):
    """Vrai s'il existe un cycle accessible ou u reste en attente sans fin pendant que d'autres reservent."""
    S = {k for k, m in r["etats"].items() if m["Attente_" + u] == 1}
    arcs = {k: [(t, d) for t, d in r["succ"][k] if d in S] for k in S}
    # composantes fortement connexes (Tarjan iteratif simplifie par recherche de cycle contenant un 'reserver_')
    for k in S:
        for t, d in arcs[k]:
            if t.startswith("reserver_") and k in accessibles_sous(arcs, d):
                return True
    return False


def accessibles_sous(arcs, depart):
    vus, file = {depart}, deque([depart])
    while file:
        for _, k in arcs[file.popleft()]:
            if k not in vus:
                vus.add(k)
                file.append(k)
    return vus


def conflits(n):
    """Paires de transitions en conflit structurel (une place d'entree commune, arcs normaux)."""
    entrees = {t: {p for p, _, typ in n.pre[t] if typ == "normal"} for t in n.trans}
    paires = []
    for i, a in enumerate(n.trans):
        for b in n.trans[i + 1:]:
            commun = entrees[a] & entrees[b]
            if commun:
                paires.append((a, b, sorted(commun)))
    return paires
