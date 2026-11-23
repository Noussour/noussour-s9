"""Petit moteur de reseaux de Petri avec arcs inhibiteurs.

Regle de franchissement utilisee (semantique classique, poids 1 par defaut) :
  - arc normal p -> t de poids w : t demande au moins w jetons dans p, et les consomme ;
  - arc inhibiteur p -o t de poids w : t n'est franchissable que si p contient
    STRICTEMENT moins de w jetons (avec w = 1 : p doit etre vide). Un arc
    inhibiteur ne consomme rien.

Le module calcule le graphe d'accessibilite (parcours en largeur), les etats morts,
la borne de chaque place et verifie des P-invariants avec la matrice d'incidence.
"""
from __future__ import annotations

from collections import deque


class PetriNet:
    def __init__(self, name: str):
        self.name = name
        self.places: list[str] = []
        self.initial: dict[str, int] = {}
        self.transitions: list[dict] = []   # {name, pre, post, inhib}

    # ------------------------------------------------------------------ build
    def place(self, name: str, tokens: int = 0) -> None:
        self.places.append(name)
        self.initial[name] = tokens

    def transition(self, name: str, pre: dict, post: dict, inhib: dict | None = None) -> None:
        self.transitions.append({"name": name, "pre": dict(pre), "post": dict(post), "inhib": dict(inhib or {})})

    # -------------------------------------------------------------- semantics
    def key(self, m: dict) -> tuple:
        return tuple(m[p] for p in self.places)

    def enabled(self, m: dict, t: dict) -> bool:
        if any(m[p] < w for p, w in t["pre"].items()):
            return False
        if any(m[p] >= w for p, w in t["inhib"].items()):
            return False
        return True

    def enabled_names(self, m: dict) -> list[str]:
        return [t["name"] for t in self.transitions if self.enabled(m, t)]

    def fire(self, m: dict, name: str) -> dict:
        t = self.get(name)
        if not self.enabled(m, t):
            raise ValueError(f"{name} n'est pas franchissable dans {m}")
        m2 = dict(m)
        for p, w in t["pre"].items():
            m2[p] -= w
        for p, w in t["post"].items():
            m2[p] += w
        return m2

    def get(self, name: str) -> dict:
        for t in self.transitions:
            if t["name"] == name:
                return t
        raise KeyError(name)

    def run(self, sequence: list[str]) -> list[tuple[str | None, dict]]:
        """Joue une sequence et renvoie [(transition franchie, marquage obtenu)]."""
        m = dict(self.initial)
        steps = [(None, m)]
        for name in sequence:
            m = self.fire(m, name)
            steps.append((name, m))
        return steps

    # --------------------------------------------------------------- analysis
    def reachability(self, limit: int = 200000) -> dict:
        m0 = dict(self.initial)
        index = {self.key(m0): 0}
        states = [m0]
        edges = []
        queue = deque([m0])
        while queue:
            m = queue.popleft()
            src = index[self.key(m)]
            for t in self.transitions:
                if self.enabled(m, t):
                    m2 = self.fire(m, t["name"])
                    k = self.key(m2)
                    if k not in index:
                        if len(states) >= limit:
                            raise RuntimeError("graphe trop grand")
                        index[k] = len(states)
                        states.append(m2)
                        queue.append(m2)
                    edges.append((src, t["name"], index[k]))
        dead = [i for i, m in enumerate(states) if not self.enabled_names(m)]
        bounds = {p: max(m[p] for m in states) for p in self.places}
        return {"states": states, "edges": edges, "dead": dead, "bounds": bounds}

    def arc_counts(self) -> dict:
        normal = sum(len(t["pre"]) + len(t["post"]) for t in self.transitions)
        inhib = sum(len(t["inhib"]) for t in self.transitions)
        return {"normal": normal, "inhibitor": inhib, "total": normal + inhib}

    def incidence(self) -> dict:
        """C[p][t] = post(p, t) - pre(p, t). Les arcs inhibiteurs n'y apparaissent pas."""
        return {p: {t["name"]: t["post"].get(p, 0) - t["pre"].get(p, 0) for t in self.transitions}
                for p in self.places}

    def is_p_invariant(self, weights: dict) -> bool:
        """Vrai si la somme ponderee des jetons ne change par aucune transition (y^T . C = 0)."""
        C = self.incidence()
        return all(sum(w * C[p][t["name"]] for p, w in weights.items()) == 0 for t in self.transitions)
