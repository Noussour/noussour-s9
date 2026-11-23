"""Construction des trois reseaux du TP et export PNML pour PIPE 5.

Pour chaque utilisateur Ui :
  Repos_Ui     : n'a rien demande (1 jeton au depart)
  Demande_Ui   : demande soumise, en attente d'une reponse
  Reservee_Ui  : place obtenue
  Annulee_Ui   : reservation annulee (reseau 3 seulement)
Place partagee :
  Disponible   : nombre de places encore libres (k jetons au depart)

Variantes :
  r1        : demander_Ui inhibee par Demande_Uj (j != i)  -> une seule demande en attente
  r2        : sans inhibiteur, demandes concurrentes
  r3        : r2 + annuler_Ui qui rend la place (Disponible + 1)
  r3_perte  : r3 sans l'arc de retour vers Disponible (variante fautive)
"""
from __future__ import annotations

from xml.sax.saxutils import escape

from petri import PetriNet

TITRES = {
    "r1": "Reseau 1 - admission controlee par arcs inhibiteurs",
    "r2": "Reseau 2 - demandes concurrentes",
    "r3": "Reseau 3 - annulation avec liberation de la place",
    "r3_perte": "Variante fautive - annulation sans liberation",
}


def users(n: int) -> list[str]:
    return ["U%d" % (i + 1) for i in range(n)]


def build(kind: str, n: int = 2, k: int = 1) -> PetriNet:
    net = PetriNet(kind)
    U = users(n)
    cancel = kind in ("r3", "r3_perte")
    for u in U:
        net.place("Repos_" + u, 1)
        net.place("Demande_" + u)
        net.place("Reservee_" + u)
        if cancel:
            net.place("Annulee_" + u)
    net.place("Disponible", k)

    for u in U:
        inhib = {"Demande_" + v: 1 for v in U if v != u} if kind == "r1" else None
        net.transition("demander_" + u, {"Repos_" + u: 1}, {"Demande_" + u: 1}, inhib)
    for u in U:
        net.transition("accorder_" + u, {"Demande_" + u: 1, "Disponible": 1}, {"Reservee_" + u: 1})
    if cancel:
        for u in U:
            post = {"Annulee_" + u: 1}
            if kind == "r3":
                post["Disponible"] = 1          # la place redevient libre
            net.transition("annuler_" + u, {"Reservee_" + u: 1}, post)
    return net


# ---------------------------------------------------------------- layout
# Coordonnees (unites de dessin) pour 2 utilisateurs : U1 a gauche, U2 a droite,
# la place partagee au milieu. Utilisees par les figures et par l'export PIPE.
COL = {"U1": 0.0, "U2": 8.0}
ROW = {"Repos": 7, "demander": 6, "Demande": 5, "accorder": 4, "Reservee": 3, "annuler": 2, "Annulee": 1}


def position(name: str) -> tuple[float, float]:
    if name == "Disponible":
        return (4.0, 4.0)
    base, u = name.rsplit("_", 1)
    return (COL[u], float(ROW[base]))


# ---------------------------------------------------------------- PNML (PIPE 5)
def to_pnml(net: PetriNet) -> str:
    def px(name):
        x, y = position(name)
        return 90 + x * 62, 40 + (7 - y) * 70

    out = ['<?xml version="1.0" encoding="ISO-8859-1"?>', "<pnml>",
           '  <net id="%s" type="P/T net">' % net.name,
           '    <token id="Default" enabled="true" red="0" green="0" blue="0"/>']
    for p in net.places:
        x, y = px(p)
        out += ['    <place id="%s">' % p,
                '      <graphics><position x="%.1f" y="%.1f"/></graphics>' % (x, y),
                '      <name><value>%s</value><graphics><offset x="0.0" y="0.0"/></graphics></name>' % p,
                '      <initialMarking><value>Default,%d</value><graphics><offset x="0.0" y="0.0"/></graphics></initialMarking>'
                % net.initial[p],
                '      <capacity><value>0</value></capacity>',
                '    </place>']
    for t in net.transitions:
        x, y = px(t["name"])
        out += ['    <transition id="%s">' % t["name"],
                '      <graphics><position x="%.1f" y="%.1f"/></graphics>' % (x, y),
                '      <name><value>%s</value><graphics><offset x="0.0" y="0.0"/></graphics></name>' % t["name"],
                '      <orientation><value>90</value></orientation>',
                '      <rate><value>1.0</value></rate>',
                '      <timed><value>false</value></timed>',
                '      <infiniteServer><value>false</value></infiniteServer>',
                '      <priority><value>1</value></priority>',
                '    </transition>']
    n = 0
    for t in net.transitions:
        arcs = [(p, t["name"], w, "normal") for p, w in t["pre"].items()]
        arcs += [(t["name"], p, w, "normal") for p, w in t["post"].items()]
        arcs += [(p, t["name"], w, "inhibitor") for p, w in t["inhib"].items()]
        for src, dst, w, kind in arcs:
            out += ['    <arc id="A%d" source="%s" target="%s">' % (n, escape(src), escape(dst)),
                    '      <graphics/>',
                    '      <inscription><value>Default,%d</value><graphics/></inscription>' % w,
                    '      <tagged><value>false</value></tagged>',
                    '      <type value="%s"/>' % kind,
                    '    </arc>']
            n += 1
    out += ["  </net>", "</pnml>"]
    return "\n".join(out) + "\n"
