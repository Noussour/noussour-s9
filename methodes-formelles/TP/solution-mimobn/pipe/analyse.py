"""Analyse des modeles PIPE (.pnml) : graphe des marquages, blocages, reversibilite, invariants, priorite,
et rejeu de scenarios. Semantique PIPE : arc normal = consomme 1 jeton, arc inhibiteur = place vide.

Usage : python analyse.py fichier.pnml [...]        -> resume de chaque reseau
        python analyse.py --scenario                 -> rejoue le scenario « U2 abandonne puis revient »
"""
import sys
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path


class Petri:
    def __init__(self, chemin):
        net = ET.parse(chemin).getroot().find("net")
        self.m0 = {p.get("id"): int((p.findtext("initialMarking/value") or "Default,0").split(",")[1])
                   for p in net.findall("place")}
        self.trans = [t.get("id") for t in net.findall("transition")]
        self.pre = {t: [] for t in self.trans}
        self.post = {t: [] for t in self.trans}
        for a in net.findall("arc"):
            s, d = a.get("source"), a.get("target")
            typ = a.find("type").get("value") if a.find("type") is not None else "normal"
            poids = int((a.findtext("inscription/value") or "Default,1").split(",")[1])
            if s in self.m0:
                self.pre[d].append((s, poids, typ))
            else:
                self.post[s].append((d, poids))

    def actives(self, m):
        return [t for t in self.trans
                if all((m[p] >= w) if typ == "normal" else (m[p] < w) for p, w, typ in self.pre[t])]

    def tirer(self, m, t):
        assert t in self.actives(m), "%s n'est pas franchissable" % t
        m = dict(m)
        for p, w, typ in self.pre[t]:
            if typ == "normal":
                m[p] -= w
        for p, w in self.post[t]:
            m[p] += w
        return m

    def graphe(self):
        cle = lambda m: tuple(sorted(m.items()))
        vus, file, arcs = {cle(self.m0): self.m0}, deque([self.m0]), {}
        while file:
            m = file.popleft()
            arcs[cle(m)] = []
            for t in self.actives(m):
                n = self.tirer(m, t)
                arcs[cle(m)].append((t, cle(n)))
                if cle(n) not in vus:
                    vus[cle(n)] = n
                    file.append(n)
        return vus, arcs

    def resume(self):
        vus, arcs = self.graphe()
        depart = tuple(sorted(self.m0.items()))
        inverse = {}
        for m, succ in arcs.items():
            for _, n in succ:
                inverse.setdefault(n, []).append(m)
        retour, file = {depart}, deque([depart])
        while file:
            for m in inverse.get(file.popleft(), []):
                if m not in retour:
                    retour.add(m)
                    file.append(m)
        etats = list(vus.values())
        L = next((p for p in self.m0 if p.startswith("Libre")), None)
        O = next((p for p in self.m0 if p.startswith("Occup")), None)
        conf = [p for p in self.m0 if p.startswith(("Conf", "Reservee"))]
        r = dict(marquages=len(etats), blocages=sum(1 for s in arcs.values() if not s),
                 reversible=len(retour) == len(etats), borne=max(max(m.values()) for m in etats))
        if L and O:
            r["invariant"] = all(m[L] + m[O] == 1 for m in etats)
            r["exclusion"] = all(sum(m[c] for c in conf) <= 1 for m in etats)
        return r


def dessiner(chemin, png, titre=None):
    """Apercu d'un .pnml tel que PIPE le place : centre d'une place = position + 15, d'une transition = position
    + (5, 15) ; les points intermediaires des arcpath sont repris, les extremites relient les centres."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    net = ET.parse(chemin).getroot().find("net")
    pos = lambda e, dx, dy: (float(e.find("graphics/position").get("x")) + dx,
                             float(e.find("graphics/position").get("y")) + dy)
    places = {p.get("id"): (pos(p, 15, 15), int((p.findtext("initialMarking/value") or "D,0").split(",")[1]))
              for p in net.findall("place")}
    trans = {t.get("id"): pos(t, 5, 15) for t in net.findall("transition")}
    c = lambda i: places[i][0] if i in places else trans[i]
    arcs = []
    for a in net.findall("arc"):
        mid = [(float(p.get("x")), float(p.get("y"))) for p in a.findall("arcpath")][1:-1]
        typ = a.find("type").get("value") if a.find("type") is not None else "normal"
        arcs.append(([c(a.get("source"))] + mid + [c(a.get("target"))], typ))
    xs = [p[0] for pts, _ in arcs for p in pts]; ys = [p[1] for pts, _ in arcs for p in pts]
    w, h = max(xs) - min(xs) + 220, max(ys) - min(ys) + 160
    fig, ax = plt.subplots(figsize=(w / 95, h / 95))
    for pts, typ in arcs:
        rouge = typ == "inhibitor"
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color="#c0392b" if rouge else "#333", lw=1.1, zorder=1)
        ax.annotate("", xy=pts[-1], xytext=pts[-2], zorder=2, arrowprops=dict(
            arrowstyle="-[" if rouge else "-|>", lw=0.9, color="#c0392b" if rouge else "#333", shrinkA=0,
            shrinkB=16, mutation_scale=7 if rouge else 9))
    for i, ((x, y), m) in places.items():
        ax.add_patch(plt.Circle((x, y), 15, fc="white", ec="#111", lw=1.4, zorder=3))
        if m:
            ax.text(x, y, "●" if m == 1 else str(m), ha="center", va="center", fontsize=9 if m == 1 else 8, zorder=4)
        ax.text(x, y + 30, i, ha="center", va="top", fontsize=7, zorder=5)
    for i, (x, y) in trans.items():
        ax.add_patch(plt.Rectangle((x - 5, y - 15), 10, 30, color="#111", zorder=3))
        ax.text(x + 9, y - 18, i, ha="left", va="bottom", fontsize=6.5, color="#1f4e79", zorder=5)
    ax.set_xlim(min(xs) - 110, max(xs) + 110); ax.set_ylim(max(ys) + 80, min(ys) - 80)
    ax.set_aspect("equal"); ax.axis("off")
    if titre:
        ax.set_title(titre, fontsize=10)
    fig.savefig(png, dpi=110, bbox_inches="tight"); plt.close(fig)


def scenario(chemin):
    """U3 confirme, U1 et U2 attendent. U2 abandonne puis revient ; U3 libere la place.
    Qui peut reserver ? U1 attendait depuis plus longtemps : c'est lui qui doit passer."""
    n = Petri(chemin)
    pref = "reserver_" if any(t.startswith("reserver_") for t in n.trans) else "Confirmer_"
    ab = "abandonner_U2" if "abandonner_U2" in n.trans else "Abandonner_U2"
    ra = next(t for t in n.trans if t.endswith("U2") and t.lower().startswith(("reessayer", "retourannulee")))
    an = "annuler_U3" if "annuler_U3" in n.trans else "Annuler_U3"
    m, trace = n.m0, []
    for t in (ab, ra, an):
        m = n.tirer(m, t)
        trace.append(t)
    act = [t for t in n.actives(m) if t.startswith(pref)]
    return trace, act


if __name__ == "__main__":
    if "--scenario" in sys.argv:
        for f in sys.argv[2:]:
            trace, act = scenario(f)
            print(Path(f).name, "|", " -> ".join(trace), "| reservations possibles :", act or "aucune")
    else:
        for f in sys.argv[1:]:
            print(Path(f).name, Petri(f).resume())
