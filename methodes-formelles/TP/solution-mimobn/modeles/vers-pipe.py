"""Convertit les modeles ISO PNML (reservation*.pnml) en fichiers que PIPE 5 sait ouvrir.

Usage : python vers-pipe.py   ->  ecrit pipe/reservation.pnml et pipe/reservation-incorrecte.pnml
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

NS = "{http://www.pnml.org/version-2009/grammar/pnml}"
ici = Path(__file__).parent


def convertir(src: Path, dst: Path) -> None:
    net = ET.parse(src).getroot().find(NS + "net")
    page = net.find(NS + "page")
    pos, out = {}, ['<?xml version="1.0" encoding="UTF-8"?>', "<pnml>",
                    '  <net id="%s" type="P/T net">' % escape(net.get("id")),
                    '    <token id="Default" enabled="true" red="0" green="0" blue="0"/>']
    for el in page:
        g = el.find(NS + "graphics/" + NS + "position")
        if g is not None:
            pos[el.get("id")] = (float(g.get("x")), float(g.get("y")))
    for p in page.findall(NS + "place"):
        x, y = pos[p.get("id")]
        n = p.findtext(NS + "initialMarking/" + NS + "text") or "0"
        out += ['    <place id="%s">' % escape(p.get("id")),
                '      <graphics><position x="%s" y="%s"/></graphics>' % (x, y),
                '      <name><value>%s</value></name>' % escape(p.get("id")),
                '      <initialMarking><value>Default,%s</value></initialMarking>' % n,
                '      <capacity><value>0</value></capacity>', '    </place>']
    for t in page.findall(NS + "transition"):
        x, y = pos[t.get("id")]
        out += ['    <transition id="%s">' % escape(t.get("id")),
                '      <graphics><position x="%s" y="%s"/></graphics>' % (x, y),
                '      <name><value>%s</value></name>' % escape(t.get("id")),
                '      <orientation><value>0</value></orientation>', '      <rate><value>1.0</value></rate>',
                '      <timed><value>false</value></timed>',
                '      <infiniteServer><value>false</value></infiniteServer>',
                '      <priority><value>1</value></priority>', '    </transition>']
    for i, a in enumerate(page.findall(NS + "arc")):
        s, d = a.get("source"), a.get("target")
        w = a.findtext(NS + "inscription/" + NS + "text") or "1"
        out += ['    <arc id="arc%d" source="%s" target="%s">' % (i, escape(s), escape(d)),
                '      <inscription><value>Default,%s</value></inscription>' % w,
                '      <arcpath id="000" x="%s" y="%s" curvePoint="false"/>' % pos[s],
                '      <arcpath id="001" x="%s" y="%s" curvePoint="false"/>' % pos[d],
                '      <type value="normal"/>', '    </arc>']
    out += ["  </net>", "</pnml>", ""]
    dst.parent.mkdir(exist_ok=True)
    dst.write_text("\n".join(out), encoding="utf-8")


for nom in ("reservation", "reservation-incorrecte"):
    convertir(ici / (nom + ".pnml"), ici / "pipe" / (nom + ".pnml"))
    print("ecrit pipe/%s.pnml" % nom)
