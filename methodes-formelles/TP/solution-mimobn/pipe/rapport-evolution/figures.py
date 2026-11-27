"""Figures du rapport : reseaux tels que places par PIPE (avec les modifications surlignees) et graphes
des marquages accessibles."""
import xml.etree.ElementTree as ET
from collections import deque

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AJOUT = "#059669"     # element ajoute a cette etape
PROBLEME = "#dc2626"  # element en cause dans le probleme
INHIB = "#c0392b"
NAVY = "#1e3a5f"


def reseau(chemin, png, noeuds=None, arcs_couleur=None, titre=None, largeur=None):
    """noeuds = {id: couleur} (contour et texte), arcs_couleur = {(source, cible): couleur}."""
    noeuds, arcs_couleur = noeuds or {}, arcs_couleur or {}
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
        arcs.append(((a.get("source"), a.get("target")), [c(a.get("source"))] + mid + [c(a.get("target"))], typ))
    xs = [p[0] for _, pts, _ in arcs for p in pts]; ys = [p[1] for _, pts, _ in arcs for p in pts]
    w, h = max(xs) - min(xs) + 220, max(ys) - min(ys) + 150
    fig, ax = plt.subplots(figsize=(w / 95, h / 95))
    for (s, d), pts, typ in sorted(arcs, key=lambda a: a[0] in arcs_couleur):
        col = arcs_couleur.get((s, d), INHIB if typ == "inhibitor" else "#333")
        lw = 2.4 if (s, d) in arcs_couleur else 1.1
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=col, lw=lw, zorder=2 if lw > 2 else 1,
                solid_joinstyle="miter")
        if typ == "inhibitor":
            (x0, y0), (x1, y1) = pts[-2], pts[-1]
            L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 or 1
            r = 15 if d in places else 9
            ax.add_patch(plt.Circle((x1 - (x1 - x0) / L * (r + 4), y1 - (y1 - y0) / L * (r + 4)), 4,
                                    fc="white", ec=col, lw=1.4, zorder=3))
        else:
            ax.annotate("", xy=pts[-1], xytext=pts[-2], zorder=3, arrowprops=dict(
                arrowstyle="-|>", lw=0.9, color=col, shrinkA=0, shrinkB=16 if d in places else 7, mutation_scale=10))
    for i, ((x, y), m) in places.items():
        col = noeuds.get(i, "#111")
        ax.add_patch(plt.Circle((x, y), 15, fc="#ecfdf5" if col == AJOUT else "#fef2f2" if col == PROBLEME
                                else "white", ec=col, lw=2.2 if i in noeuds else 1.4, zorder=4))
        if m:
            ax.text(x, y, "●" if m == 1 else str(m), ha="center", va="center", fontsize=9, zorder=5)
        ax.text(x, y + 30, i, ha="center", va="top", fontsize=7, zorder=6, color=col,
                fontweight="bold" if i in noeuds else "normal")
    for i, (x, y) in trans.items():
        col = noeuds.get(i, "#111")
        ax.add_patch(plt.Rectangle((x - 5, y - 15), 10, 30, color=col, zorder=4))
        ax.text(x + 9, y - 18, i, ha="left", va="bottom", fontsize=6.5, zorder=6,
                color=col if i in noeuds else NAVY, fontweight="bold" if i in noeuds else "normal")
    ax.set_xlim(min(xs) - 110, max(xs) + 110); ax.set_ylim(max(ys) + 75, min(ys) - 70)
    ax.set_aspect("equal"); ax.axis("off")
    if titre:
        ax.set_title(titre, fontsize=10, color=NAVY)
    fig.savefig(png, dpi=150, bbox_inches="tight"); plt.close(fig)


LETTRE = {"Attente": "A", "Confirmee": "C", "Refusee": "R", "Annulee": "X", "Demande": "D"}
ABREGE = {"reserver": "r", "refuser": "f", "abandonner": "b", "annuler": "x", "retour": "t", "reessayer": "e",
          "rejoindre": "j"}


def etiquette(m, users):
    parts = []
    for u in users:
        e = [LETTRE[p.split("_")[0]] for p, v in m.items() if v and p.endswith("_" + u) and p.split("_")[0] in LETTRE]
        parts.append("".join(e) or "-")
    occ = m.get("Occupees", 0)
    return " ".join(parts) + "\nL%d O%d" % (m.get("Libres", 0), occ)


def graphe(r, png, users=("U1", "U2"), titre=None):
    """Graphe des marquages : couches = distance depuis M0 ; marquages morts encadres en rouge,
    marquages violant l'exclusion mutuelle (deux confirmes) sur fond rouge."""
    etats, succ = r["etats"], r["succ"]
    m0 = r["ordre"][0]
    dist, file = {m0: 0}, deque([m0])
    while file:
        k = file.popleft()
        for _, d in succ[k]:
            if d not in dist:
                dist[d] = dist[k] + 1
                file.append(d)
    couches = {}
    for k in r["ordre"]:
        couches.setdefault(dist[k], []).append(k)
    pos = {}
    for niv, ks in couches.items():
        for i, k in enumerate(ks):
            pos[k] = ((i - (len(ks) - 1) / 2) * 2.3, -niv * 1.55)
    largeur = max(len(v) for v in couches.values())
    fig, ax = plt.subplots(figsize=(max(6.5, largeur * 1.75), len(couches) * 1.25 + 0.6))
    for k, s in succ.items():
        vus = {}
        for t, d in s:
            vus.setdefault(d, []).append(t)
        for d, ts in vus.items():
            (x0, y0), (x1, y1) = pos[k], pos[d]
            nom = ",".join(ABREGE[t.split("_")[0]] + t[-1] for t in ts)
            retour = dist[d] <= dist[k]

            def bord(p, q, hx=0.78, hy=0.38):  # point du bord de la boite centree en p, vers q
                dx, dy = q[0] - p[0], q[1] - p[1]
                f = min(hx / abs(dx) if dx else 1e9, hy / abs(dy) if dy else 1e9)
                return p[0] + dx * f, p[1] + dy * f
            ax.annotate("", xy=bord((x1, y1), (x0, y0)), xytext=bord((x0, y0), (x1, y1)), arrowprops=dict(
                arrowstyle="-|>", color="#94a3b8" if retour else "#475569", lw=0.8, shrinkA=0, shrinkB=0,
                connectionstyle="arc3,rad=%s" % (0.25 if retour else 0.0), mutation_scale=10), zorder=3)
            ax.text(x0 + (x1 - x0) * 0.42, y0 + (y1 - y0) * 0.42, nom, fontsize=6, color="#0f766e",
                    ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.4), zorder=4)
    for k, (x, y) in pos.items():
        m = etats[k]
        mort = not succ[k]
        double = sum(v for p, v in m.items() if p.startswith("Confirmee_")) > 1
        ax.add_patch(matplotlib.patches.FancyBboxPatch(
            (x - 0.72, y - 0.33), 1.44, 0.66, boxstyle="round,pad=0.04", zorder=5,
            fc="#fee2e2" if double else "#e0f2fe" if k == m0 else "white",
            ec=PROBLEME if (mort or double) else NAVY, lw=2.0 if (mort or double) else 1.0))
        ax.text(x, y, etiquette(m, users), ha="center", va="center", fontsize=7, zorder=6, family="Consolas")
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - 1.1, max(xs) + 1.1); ax.set_ylim(min(ys) - 0.6, max(ys) + 0.6)
    ax.axis("off")
    if titre:
        ax.set_title(titre, fontsize=10, color=NAVY)
    fig.savefig(png, dpi=150, bbox_inches="tight"); plt.close(fig)
