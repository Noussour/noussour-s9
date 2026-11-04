import math, sys
OUT = sys.argv[1]
INK, MUTED, ACCENT = "#141413", "#87867f", "#c96442"

def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'font-family="Helvetica, Arial, sans-serif">'
            '<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker></defs>' + body + '</svg>')

def trim_circle(c, r, p):
    dx, dy = p[0]-c[0], p[1]-c[1]; d = math.hypot(dx, dy)
    return (c[0]+dx/d*r, c[1]+dy/d*r)
def trim_rect(c, hw, hh, p):
    dx, dy = p[0]-c[0], p[1]-c[1]
    s = min(hw/abs(dx) if dx else 1e9, hh/abs(dy) if dy else 1e9)
    return (c[0]+dx*s, c[1]+dy*s)

# ---------- Reseau de Petri ----------
R, HW, HH = 22, 7, 20
def petri():
    P, T = {}, {}
    P["Libres"] = (450, 80); P["Occupees"] = (450, 440)
    for i, m in ((1, lambda x: x), (2, lambda x: 900-x)):
        P[f"Attente_U{i}"] = (m(110), 80); T[f"reserver_U{i}"] = (m(280), 80)
        T[f"abandonner_U{i}"] = (m(110), 200); P[f"Confirmee_U{i}"] = (m(280), 200)
        P[f"Annulee_U{i}"] = (m(110), 320); T[f"annuler_U{i}"] = (m(280), 320)
        T[f"refuser_U{i}"] = (m(110), 440); P[f"Refusee_U{i}"] = (m(110), 545)
    def node_trim(n, toward):
        return trim_circle(P[n], R, toward) if n in P else trim_rect(T[n], HW, HH, toward)
    def pos(n): return P.get(n) or T[n]
    b = []
    def arc(a, z, via=(), dash=False, off=(0, 0)):
        pts = [pos(a)] + list(via) + [pos(z)]
        pts = [(x+off[0], y+off[1]) for x, y in pts]
        s = node_trim(a, pts[1]) if not off[1] else (pts[0][0] + (R if pts[1][0] > pts[0][0] else -R) * (1 if a in P else HW/R), pts[0][1])
        e = node_trim(z, pts[-2]) if not off[1] else (pts[-1][0] + (-R if pts[-2][0] < pts[-1][0] else R) * (1 if z in P else HW/R), pts[-1][1])
        pts[0], pts[-1] = s, e
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        b.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="1.4" marker-end="url(#ar)"/>')
    for i, sgn in ((1, 1), (2, -1)):
        A, C, X, Rf = (f"{p}_U{i}" for p in ("Attente", "Confirmee", "Annulee", "Refusee"))
        res, ab, an, rf = (f"{t}_U{i}" for t in ("reserver", "abandonner", "annuler", "refuser"))
        xl = 40 if i == 1 else 860
        arc(A, res); arc("Libres", res); arc(res, C); arc(res, "Occupees")
        arc(A, ab); arc(ab, X)
        arc(C, an); arc("Occupees", an); arc(an, X); arc(an, "Libres")
        arc(A, rf, via=[(xl, 80), (xl, 440)]); arc(rf, Rf)
        arc("Occupees", rf, off=(0, -6)); arc(rf, "Occupees", off=(0, 6))
        b.append(f'<text x="{450 - sgn*170}" y="425" font-size="12" font-style="italic" fill="{INK}" text-anchor="middle">N</text>')
    for n, (x, y) in P.items():
        b.append(f'<circle cx="{x}" cy="{y}" r="{R}" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
    for n, tok in (("Libres", 1), ("Attente_U1", 1), ("Attente_U2", 1)):
        x, y = P[n]; b.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{INK}"/>')
    for n, (x, y) in T.items():
        b.append(f'<rect x="{x-HW}" y="{y-HH}" width="{2*HW}" height="{2*HH}" fill="{INK}"/>')
    def label(t, x, y, anchor="middle", color=INK, size=12):
        b.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{t}</text>')
    label("Libres", 450, 46); label("Occupees", 450, 482)
    for i, m in ((1, lambda x: x), (2, lambda x: 900-x)):
        L = "start" if i == 1 else "end"; Lr = "end" if i == 1 else "start"
        label(f"Attente_U{i}", m(110), 46)
        label(f"reserver_U{i}", m(280), 50, color=ACCENT, size=11)
        label(f"abandonner_U{i}", m(124), 186, L, ACCENT, 11)
        label(f"Confirmee_U{i}", m(254), 236, Lr)
        label(f"Annulee_U{i}", m(110), 358)
        label(f"annuler_U{i}", m(280), 358, color=ACCENT, size=11)
        label(f"refuser_U{i}", m(124), 476, L, ACCENT, 11)
        label(f"Refusee_U{i}", m(110), 583)
    return svg(900, 600, "".join(b))

# ---------- Automate JFLAP ----------
def automate():
    S = {"EnAttente": (110, 150), "Confirmee": (330, 60), "Refusee": (330, 240), "Annulee": (550, 150)}
    fin = {"Confirmee", "Refusee", "Annulee"}; r = 34; b = []
    def edge(a, z, lab, lx, ly):
        s, e = trim_circle(S[a], r + (4 if a in fin else 0), S[z]), trim_circle(S[z], r + 4, S[a])
        b.append(f'<path d="M{s[0]:.1f},{s[1]:.1f} L{e[0]:.1f},{e[1]:.1f}" stroke="{INK}" stroke-width="1.4" marker-end="url(#ar)"/>')
        b.append(f'<text x="{lx}" y="{ly}" font-size="15" fill="{ACCENT}" font-weight="bold" text-anchor="middle">{lab}</text>')
    edge("EnAttente", "Confirmee", "c", 205, 90); edge("EnAttente", "Refusee", "r", 205, 222)
    edge("EnAttente", "Annulee", "a", 330, 142); edge("Confirmee", "Annulee", "a", 455, 90)
    b.append(f'<path d="M20,150 L{110-r-1},150" stroke="{INK}" stroke-width="1.4" marker-end="url(#ar)"/>')
    b.append(f'<text x="20" y="140" font-size="11" fill="{MUTED}">début</text>')
    for n, (x, y) in S.items():
        b.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
        if n in fin: b.append(f'<circle cx="{x}" cy="{y}" r="{r+4}" fill="none" stroke="{INK}" stroke-width="1.2"/>')
        b.append(f'<text x="{x}" y="{y+4}" font-size="12" fill="{INK}" text-anchor="middle">{n}</text>')
    return svg(620, 300, "".join(b))

# ---------- Courbe PRISM ----------
def courbe(path):
    rows = []
    lines = open(path).read().splitlines()
    i = lines.index("T\tResult") + 1
    while i < len(lines) and lines[i].strip() and lines[i][0].isdigit():
        t, v = lines[i].split("\t"); rows.append((int(t), float(v))); i += 1
    W, H, l, rgt, top, bot = 640, 300, 56, 24, 20, 44
    X = lambda t: l + (t - 0) / 10 * (W - l - rgt)
    Y = lambda v: top + (1 - v) * (H - top - bot)
    b = []
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        b.append(f'<line x1="{l}" x2="{W-rgt}" y1="{Y(v)}" y2="{Y(v)}" stroke="#e8e6dc" stroke-width="1"/>')
        b.append(f'<text x="{l-8}" y="{Y(v)+4}" font-size="11" fill="{MUTED}" text-anchor="end">{format(v, "g").replace(".", ",")}</text>')
    for t in range(0, 11):
        b.append(f'<text x="{X(t)}" y="{H-bot+18}" font-size="11" fill="{MUTED}" text-anchor="middle">{t}</text>')
    b.append(f'<line x1="{l}" x2="{W-rgt}" y1="{Y(0)}" y2="{Y(0)}" stroke="{MUTED}" stroke-width="1"/>')
    lim = 0.971689
    b.append(f'<line x1="{l}" x2="{W-rgt}" y1="{Y(lim)}" y2="{Y(lim)}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="4 4"/>')
    b.append(f'<text x="{W-rgt}" y="{Y(lim)-6}" font-size="11" fill="{MUTED}" text-anchor="end">limite sans échéance : 0,9717</text>')
    d = "M" + " L".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in rows)
    b.append(f'<path d="{d}" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-linejoin="round"/>')
    for t, v in rows:
        b.append(f'<circle cx="{X(t):.1f}" cy="{Y(v):.1f}" r="4.5" fill="{ACCENT}" stroke="#fff" stroke-width="2"/>')
    for t, v in rows:
        if t in (1, 2, 3):
            b.append(f'<text x="{X(t)+8:.1f}" y="{Y(v)+16:.1f}" font-size="11" fill="{INK}">{format(v, ".3f").replace(".", ",")}</text>')
    b.append(f'<text x="{(l+W-rgt)/2}" y="{H-6}" font-size="12" fill="{INK}" text-anchor="middle">échéance T (pas de temps)</text>')
    b.append(f'<text x="14" y="{(top+H-bot)/2}" font-size="12" fill="{INK}" text-anchor="middle" transform="rotate(-90 14 {(top+H-bot)/2})">P(confirmée avant T)</text>')
    return svg(W, H, "".join(b))

open(f"{OUT}/petri.svg", "w").write(petri())
open(f"{OUT}/automate_jflap.svg", "w").write(automate())
open(f"{OUT}/prism_courbe.svg", "w").write(courbe(sys.argv[2]))
print("ok")
