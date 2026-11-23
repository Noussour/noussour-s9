"""Analyse des trois reseaux de Petri (graphe d'accessibilite, invariants, blocages)
et export au format PNML de PIPE.

Semantique : une transition est franchissable si chaque place d'entree contient au
moins le poids de l'arc et si chaque place reliee par un arc inhibiteur contient
strictement moins de jetons que le poids de cet arc (poids 1 : place vide).
"""
import itertools, json, sys
from collections import deque

def make_net(n_users, seats, inhib=False, cancel=False, cancel_lost=False):
    U = [f"U{i}" for i in range(1, n_users + 1)]
    places = ["Libres"]
    m0 = {"Libres": seats}
    for u in U:
        for p in ["Idle", "Attente", "Confirmee"] + (["Annulee"] if cancel else []):
            places.append(f"{p}_{u}")
            m0[f"{p}_{u}"] = 1 if p == "Idle" else 0
    T = {}
    for u in U:
        others = [v for v in U if v != u]
        T[f"demander_{u}"] = dict(
            pre={f"Idle_{u}": 1}, post={f"Attente_{u}": 1},
            inh={f"Attente_{v}": 1 for v in others} if inhib else {})
        T[f"attribuer_{u}"] = dict(
            pre={f"Attente_{u}": 1, "Libres": 1}, post={f"Confirmee_{u}": 1}, inh={})
        if cancel:
            post = {f"Annulee_{u}": 1}
            if not cancel_lost:
                post["Libres"] = 1
            T[f"annuler_{u}"] = dict(pre={f"Confirmee_{u}": 1}, post=post, inh={})
    return places, m0, T

def enabled(m, t):
    return all(m[p] >= w for p, w in t["pre"].items()) and \
           all(m[p] < w for p, w in t["inh"].items())

def fire(m, t):
    m = dict(m)
    for p, w in t["pre"].items(): m[p] -= w
    for p, w in t["post"].items(): m[p] += w
    return m

def key(m, places):
    return tuple(m[p] for p in places)

def explore(net):
    places, m0, T = net
    seen = {key(m0, places): m0}
    q = deque([m0]); edges = 0; dead = []; fired = set()
    while q:
        m = q.popleft()
        en = [n for n, t in T.items() if enabled(m, t)]
        if not en:
            dead.append(m)
        for n in en:
            edges += 1; fired.add(n)
            m2 = fire(m, T[n]); k = key(m2, places)
            if k not in seen:
                seen[k] = m2; q.append(m2)
    bound = max(max(m.values()) for m in seen.values())
    return dict(states=len(seen), edges=edges, dead=dead, bound=bound,
                transitions=len(T), dead_transitions=sorted(set(T) - fired),
                markings=list(seen.values()))

def describe(m):
    return ", ".join(f"{p}={v}" for p, v in m.items() if v)

def report():
    out = {}
    configs = {
        "R1": dict(inhib=True), "R2": dict(), "R3": dict(cancel=True),
        "R3_perte": dict(cancel=True, cancel_lost=True),
    }
    for name, cfg in configs.items():
        for n, s in [(2, 1), (2, 2), (3, 1), (3, 2)]:
            net = make_net(n, s, **cfg)
            r = explore(net)
            # verification de l'invariant Libres + sum(Confirmee) + (annulees si perte) = seats
            places = net[0]
            inv_ok = all(m["Libres"] + sum(m[p] for p in places if p.startswith("Confirmee")) == s
                         for m in r["markings"])
            double = any(sum(m[p] for p in places if p.startswith("Confirmee")) > s for m in r["markings"])
            stuck = sum(1 for m in r["dead"] if any(m[p] for p in places if p.startswith("Attente")))
            out[f"{name}_{n}u_{s}p"] = dict(
                states=r["states"], edges=r["edges"], transitions=r["transitions"],
                dead=len(r["dead"]), dead_with_waiting=stuck, bound=r["bound"],
                invariant=inv_ok, surreservation=double,
                dead_markings=[describe(m) for m in r["dead"]])
    return out

# ---------------------------------------------------------------- export PNML (PIPE)
LAYOUT = {  # coordonnees PIPE (pixels)
    "Idle_U1": (100, 60), "Idle_U2": (700, 60),
    "demander_U1": (110, 180), "demander_U2": (710, 180),
    "Attente_U1": (100, 300), "Libres": (400, 300), "Attente_U2": (700, 300),
    "attribuer_U1": (260, 420), "attribuer_U2": (550, 420),
    "Confirmee_U1": (250, 540), "Confirmee_U2": (540, 540),
    "annuler_U1": (360, 650), "annuler_U2": (440, 650),
    "Annulee_U1": (250, 760), "Annulee_U2": (540, 760),
}

def pnml(net, comment):
    places, m0, T = net
    L = ['<?xml version="1.0" encoding="UTF-8"?>', f"<!-- {comment} -->", "<pnml>", "<net>",
         '<token id="Default" red="0" green="0" blue="0"/>']
    for p in places:
        x, y = LAYOUT[p]
        L.append(f'<place id="{p}"><graphics><position x="{x}.0" y="{y}.0"/></graphics>'
                 f'<name><value>{p}</value><graphics><offset x="0.0" y="-10.0"/></graphics></name>'
                 f'<initialMarking><value>Default,{m0[p]}</value><graphics><offset x="0.0" y="0.0"/></graphics></initialMarking>'
                 f'<capacity><value>0</value></capacity></place>')
    for t in T:
        x, y = LAYOUT[t]
        L.append(f'<transition id="{t}"><graphics><position x="{x}.0" y="{y}.0"/></graphics>'
                 f'<name><value>{t}</value><graphics><offset x="0.0" y="-10.0"/></graphics></name>'
                 f'<orientation><value>0</value></orientation><rate><value>1.0</value></rate>'
                 f'<timed><value>false</value></timed><infiniteServer><value>false</value></infiniteServer>'
                 f'<priority><value>1</value></priority></transition>')
    def arc(src, dst, kind):
        (x1, y1), (x2, y2) = LAYOUT[src], LAYOUT[dst]
        return (f'<arc id="{src} TO {dst}" source="{src}" target="{dst}">'
                f'<arcpath id="000" x="{x1 + 15}.0" y="{y1 + 15}.0" curvePoint="false"/>'
                f'<arcpath id="001" x="{x2 + 15}.0" y="{y2 + 15}.0" curvePoint="false"/>'
                f'<type value="{kind}"/><inscription><value>Default,1</value></inscription></arc>')
    for n, t in T.items():
        for p in t["pre"]: L.append(arc(p, n, "normal"))
        for p in t["inh"]: L.append(arc(p, n, "inhibitor"))
        for p in t["post"]: L.append(arc(n, p, "normal"))
    L += ["</net>", "</pnml>"]
    return "\n".join(L) + "\n"

if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    files = {
        "reseau1_inhibiteur.pnml": (make_net(2, 1, inhib=True),
            "Reseau 1 : arc inhibiteur, une seule demande en attente a la fois. 2 utilisateurs, 1 place."),
        "reseau2_concurrent.pnml": (make_net(2, 1),
            "Reseau 2 : demandes concurrentes, conflit sur Libres. 2 utilisateurs, 1 place."),
        "reseau3_annulation.pnml": (make_net(2, 1, cancel=True),
            "Reseau 3 : reseau 2 + annulation (la place est rendue a Libres). 2 utilisateurs, 1 place."),
    }
    for f, (net, c) in files.items():
        open(os.path.join(here, f), "w").write(pnml(net, c))
    res = report()
    json.dump(res, open(os.path.join(here, "resultats.json"), "w"), indent=1, ensure_ascii=False)
    for k, v in res.items():
        print(k, {a: b for a, b in v.items() if a != "dead_markings"})
        if k.endswith("2u_1p"):
            for d in v["dead_markings"]: print("   dead:", d)
