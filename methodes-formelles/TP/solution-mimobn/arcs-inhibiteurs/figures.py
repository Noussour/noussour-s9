"""Dessins : reseaux (avec marquage et transitions franchissables), etapes de
simulation et graphes d'accessibilite."""
from __future__ import annotations

import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

from modeles import position

NAVY = "#1e3a5f"
FIRED = "#f59e0b"       # transition qui vient d'etre franchie
ENABLED = "#34d399"     # transition franchissable
DISABLED = "#e2e8f0"    # transition non franchissable
INHIB = "#dc2626"       # arcs inhibiteurs
R_PLACE = 0.42
T_W, T_H = 1.25, 0.34


def _boundary(name, toward, is_place):
    """Point du bord de l'objet `name` dans la direction de `toward`."""
    x, y = position(name)
    dx, dy = toward[0] - x, toward[1] - y
    d = math.hypot(dx, dy) or 1
    ux, uy = dx / d, dy / d
    if is_place:
        r = R_PLACE
    else:
        r = min((T_W / 2) / abs(ux) if ux else 1e9, (T_H / 2) / abs(uy) if uy else 1e9)
    return x + ux * r, y + uy * r


def _arc(ax, src, dst, src_place, inhibitor=False):
    a = _boundary(src, position(dst), src_place)
    b = _boundary(dst, position(src), not src_place)
    cross = inhibitor and abs(position(src)[0] - position(dst)[0]) > 1
    style = "arc3,rad=0.12" if cross else "arc3"
    if inhibitor:
        # ligne qui s'arrete avant la transition + petit cercle (tete d'inhibiteur)
        ux, uy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(ux, uy)
        end = (b[0] - ux / d * 0.13, b[1] - uy / d * 0.13)
        ax.add_patch(FancyArrowPatch(a, end, arrowstyle="-", connectionstyle=style, color=INHIB, lw=1.4, zorder=1))
        ax.add_patch(Circle((b[0] - ux / d * 0.07, b[1] - uy / d * 0.07), 0.08, fc="white", ec=INHIB, lw=1.4, zorder=4))
    else:
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=11, color=NAVY, lw=1.2, zorder=1))


def draw_net(ax, net, marking, fired=None, title=None, compact=False):
    enabled = set(net.enabled_names(marking))
    for t in net.transitions:
        for p in t["pre"]:
            _arc(ax, p, t["name"], True)
        for p in t["post"]:
            _arc(ax, t["name"], p, False)
        for p in t["inhib"]:
            _arc(ax, p, t["name"], True, inhibitor=True)

    fs = 7.2 if compact else 8.2
    for p in net.places:
        x, y = position(p)
        ax.add_patch(Circle((x, y), R_PLACE, fc="white", ec=NAVY, lw=1.6, zorder=3))
        n = marking[p]
        if n == 1:
            ax.add_patch(Circle((x, y), 0.11, fc="black", zorder=5))
        elif n > 1:
            ax.text(x, y, str(n), ha="center", va="center", fontsize=11, weight="bold", zorder=5)
        if p == "Disponible":
            ax.text(x, y - 0.62, p, ha="center", va="top", fontsize=fs, color=NAVY, weight="bold")
        else:
            left = x < 4
            ax.text(x + (-0.55 if left else 0.55), y, p, ha="right" if left else "left", va="center", fontsize=fs, color=NAVY)

    for t in net.transitions:
        x, y = position(t["name"])
        name = t["name"]
        fc = FIRED if name == fired else (ENABLED if name in enabled else DISABLED)
        ax.add_patch(Rectangle((x - T_W / 2, y - T_H / 2), T_W, T_H, fc=fc, ec=NAVY, lw=1.2, zorder=3))
        left = x < 4
        ax.text(x + (-0.75 if left else 0.75), y, name, ha="right" if left else "left", va="center",
                fontsize=fs, color="#334155", style="italic")

    ymin = min(position(p)[1] for p in net.places) - 0.9
    ax.set_xlim(-3.6, 11.6)
    ax.set_ylim(ymin, 7.7)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=9.5 if compact else 11, color=NAVY, weight="bold", pad=4)


def net_figure(net, path, title=None):
    h = 6.4 if any(p.startswith("Annulee") for p in net.places) else 5.0
    fig, ax = plt.subplots(figsize=(7.4, h))
    draw_net(ax, net, dict(net.initial), title=title)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def scenario_figure(net, steps, path, cols=2, offset=0):
    """steps : [(transition franchie ou None, marquage)] ; offset : numero de la 1re etape montree"""
    rows = math.ceil(len(steps) / cols)
    tall = any(p.startswith("Annulee") for p in net.places)
    fig, axes = plt.subplots(rows, cols, figsize=(7.8, rows * (2.35 if tall else 1.85)))
    axes = axes.flatten() if hasattr(axes, "flatten") else [axes]
    for i, ax in enumerate(axes):
        if i >= len(steps):
            ax.axis("off")
            continue
        fired, m = steps[i]
        title = "État initial" if fired is None else "%d. après %s" % (i + offset, fired)
        draw_net(ax, net, m, fired=fired, title=title, compact=True)
    fig.tight_layout(pad=0.6)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- reachability
LETTER = {"Repos": "R", "Demande": "D", "Reservee": "S", "Annulee": "A"}


def state_label(net, m):
    users = sorted({p.rsplit("_", 1)[1] for p in net.places if "_" in p})
    parts = []
    for u in users:
        for base, letter in LETTER.items():
            if m.get(base + "_" + u, 0):
                parts.append(letter)
    return " ".join(parts) + "  |  %d" % m["Disponible"]


def short(tname):
    base, u = tname.rsplit("_", 1)
    return {"demander": "d", "accorder": "a", "annuler": "x"}[base] + u[1:]


def reach_figure(net, rg, path, title=None):
    edges = rg["edges"]
    n = len(rg["states"])
    depth = [None] * n
    depth[0] = 0
    changed = True
    while changed:
        changed = False
        for s, _, d in edges:
            if depth[s] is not None and (depth[d] is None or depth[d] > depth[s] + 1):
                depth[d] = depth[s] + 1
                changed = True
    layers = {}
    for i, dpt in enumerate(depth):
        layers.setdefault(dpt, []).append(i)
    pos = {}
    for dpt, ids in layers.items():
        for j, i in enumerate(ids):
            pos[i] = ((j - (len(ids) - 1) / 2) * 2.6, -dpt * 1.25)

    width = max(len(v) for v in layers.values())
    fig, ax = plt.subplots(figsize=(max(5.2, width * 2.2), 1.0 + len(layers) * 0.95))
    for s, t, d in edges:
        (x1, y1), (x2, y2) = pos[s], pos[d]
        ax.add_patch(FancyArrowPatch((x1, y1 - 0.24), (x2, y2 + 0.24), arrowstyle="-|>", mutation_scale=10,
                                     color="#64748b", lw=1.0, connectionstyle="arc3,rad=0.06", zorder=1))
        ax.text((x1 + x2) / 2 + 0.12, (y1 + y2) / 2, short(t), fontsize=7.5, color="#b45309", ha="left", va="center",
                bbox=dict(fc="white", ec="none", pad=0.4), zorder=2)
    for i, m in enumerate(rg["states"]):
        x, y = pos[i]
        dead = i in rg["dead"]
        ax.add_patch(FancyBboxPatch((x - 1.0, y - 0.24), 2.0, 0.48, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc="#fee2e2" if dead else ("#dbeafe" if i == 0 else "white"),
                                    ec="#dc2626" if dead else NAVY, lw=1.3, zorder=3))
        ax.text(x, y, "M%d  %s" % (i, state_label(net, m)), ha="center", va="center", fontsize=7.3, zorder=4,
                family="DejaVu Sans Mono")
    xs = [p[0] for p in pos.values()]
    ax.set_xlim(min(xs) - 1.3, max(xs) + 1.3)
    ax.set_ylim(min(p[1] for p in pos.values()) - 0.5, 0.5)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=10, color=NAVY, weight="bold")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
