import math, sys
import html
import xml.etree.ElementTree as ET
from pathlib import Path
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
def petri():
    """Render the current PIPE model, including its layout and inhibitor arcs."""
    net = ET.parse(Path(__file__).resolve().parent.parent / "3-petri/reservation.pnml").getroot().find("net")
    places = {n.attrib["id"]: n for n in net.findall("place")}
    transitions = {n.attrib["id"]: n for n in net.findall("transition")}
    nodes = {**places, **transitions}
    centers = {}
    for name, node in nodes.items():
        p = node.find("graphics/position")
        centers[name] = (float(p.attrib["x"]) + (15 if name in places else 5),
                         float(p.attrib["y"]) + 15)
    b = ['<defs><marker id="inhibitor" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto"><circle cx="6" cy="6" r="4" fill="#fff" stroke="'+INK+'" stroke-width="1.4"/></marker></defs><g transform="translate(-80,-20)">']
    for arc in net.findall("arc"):
        a, z = arc.attrib["source"], arc.attrib["target"]
        pts = [(float(p.attrib["x"]), float(p.attrib["y"])) for p in arc.findall("arcpath")]
        pts[0], pts[-1] = centers[a], centers[z]
        pts[0] = trim_circle(centers[a], 15, pts[1]) if a in places else trim_rect(centers[a], 5, 15, pts[1])
        pts[-1] = trim_circle(centers[z], 15, pts[-2]) if z in places else trim_rect(centers[z], 5, 15, pts[-2])
        marker = "inhibitor" if arc.find("type").attrib["value"] == "inhibitor" else "ar"
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        b.append(f'<path data-source="{a}" data-target="{z}" d="{d}" fill="none" stroke="{INK}" stroke-width="1.4" marker-end="url(#{marker})"/>')
    for name, node in nodes.items():
        x, y = centers[name]
        if name in places:
            b.append(f'<circle cx="{x}" cy="{y}" r="15" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
            tokens = int(node.findtext("initialMarking/value").split(",")[-1])
            if tokens == 1:
                b.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{INK}"/>')
            elif tokens:
                b.append(f'<text x="{x}" y="{y+5}" text-anchor="middle">{tokens}</text>')
            label_y = y - 28 if name.startswith(("Attente", "Occupees")) else y + 39
            if name == "Libres": label_y = y - 72
            color = INK
        else:
            b.append(f'<rect x="{x-5}" y="{y-15}" width="10" height="30" fill="{INK}"/>')
            label_y, color = y + 34, ACCENT
        label = html.escape(node.findtext("name/value", name))
        b.append(f'<text x="{x}" y="{label_y}" font-size="14" fill="{color}" stroke="#faf9f5" stroke-width="5" paint-order="stroke" stroke-linejoin="round" text-anchor="middle">{label}</text>')
    b.append('</g>')
    return svg(1040, 600, "".join(b))

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
