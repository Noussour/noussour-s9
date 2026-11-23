// Dessin des reseaux de Petri du rapport (cetz).
#import "@preview/cetz:0.4.2"

#let R = 0.38          // rayon d'une place
#let TW = 0.42         // demi-largeur d'une transition
#let TH = 0.11         // demi-hauteur d'une transition

#let c-en = rgb("#2e9e44")
#let c-fired = rgb("#e07b00")
#let c-inh = rgb("#c62828")

// Position et type de chaque noeud. side : cote de l'etiquette.
#let nodes = (
  Idle_U1: (pos: (0, 0), kind: "p", side: "w"),
  Idle_U2: (pos: (8, 0), kind: "p", side: "e"),
  demander_U1: (pos: (0, -1.4), kind: "t", side: "w"),
  demander_U2: (pos: (8, -1.4), kind: "t", side: "e"),
  Attente_U1: (pos: (0, -2.8), kind: "p", side: "w"),
  Attente_U2: (pos: (8, -2.8), kind: "p", side: "e"),
  Libres: (pos: (4, -2.8), kind: "p", side: "n"),
  attribuer_U1: (pos: (2, -4.2), kind: "t", side: "w"),
  attribuer_U2: (pos: (6, -4.2), kind: "t", side: "e"),
  Confirmee_U1: (pos: (2, -5.6), kind: "p", side: "w"),
  Confirmee_U2: (pos: (6, -5.6), kind: "p", side: "e"),
  annuler_U1: (pos: (2, -7.0), kind: "t", side: "w"),
  annuler_U2: (pos: (6, -7.0), kind: "t", side: "e"),
  Annulee_U1: (pos: (2, -8.4), kind: "p", side: "w"),
  Annulee_U2: (pos: (6, -8.4), kind: "p", side: "e"),
)

// Arcs : (source, cible, type, points intermediaires)
#let arcs-base = (
  ("Idle_U1", "demander_U1", "n", ()),
  ("demander_U1", "Attente_U1", "n", ()),
  ("Idle_U2", "demander_U2", "n", ()),
  ("demander_U2", "Attente_U2", "n", ()),
  ("Attente_U1", "attribuer_U1", "n", ()),
  ("Libres", "attribuer_U1", "n", ()),
  ("Attente_U2", "attribuer_U2", "n", ()),
  ("Libres", "attribuer_U2", "n", ()),
  ("attribuer_U1", "Confirmee_U1", "n", ()),
  ("attribuer_U2", "Confirmee_U2", "n", ()),
)
#let arcs-inh = (
  ("Attente_U2", "demander_U1", "i", ()),
  ("Attente_U1", "demander_U2", "i", ()),
)
#let arcs-cancel = (
  ("Confirmee_U1", "annuler_U1", "n", ()),
  ("annuler_U1", "Annulee_U1", "n", ()),
  ("annuler_U1", "Libres", "n", ((3.68, -7.0),)),
  ("Confirmee_U2", "annuler_U2", "n", ()),
  ("annuler_U2", "Annulee_U2", "n", ()),
  ("annuler_U2", "Libres", "n", ((4.32, -7.0),)),
)

#let net-def(kind) = {
  let names = ("Idle_U1", "Idle_U2", "demander_U1", "demander_U2", "Attente_U1",
    "Attente_U2", "Libres", "attribuer_U1", "attribuer_U2", "Confirmee_U1", "Confirmee_U2")
  let arcs = arcs-base
  if kind == "r1" { arcs += arcs-inh }
  if kind in ("r3", "r3bad") {
    names += ("annuler_U1", "annuler_U2", "Annulee_U1", "Annulee_U2")
    arcs += if kind == "r3" { arcs-cancel } else { arcs-cancel.filter(a => a.at(1) != "Libres") }
  }
  (names: names, arcs: arcs)
}

// Point du bord d'un noeud dans la direction de (tx, ty).
#let border(name, tx, ty) = {
  let n = nodes.at(name)
  let (x, y) = n.pos
  let dx = tx - x
  let dy = ty - y
  let d = calc.sqrt(dx * dx + dy * dy)
  if n.kind == "p" {
    (x + dx / d * R, y + dy / d * R)
  } else {
    let k = calc.min(
      if dx == 0 { 1e9 } else { TW / calc.abs(dx) },
      if dy == 0 { 1e9 } else { TH / calc.abs(dy) },
    )
    (x + dx * k, y + dy * k)
  }
}

// Transitions franchissables pour un marquage donne.
#let pre = (
  demander_U1: ("Idle_U1",), demander_U2: ("Idle_U2",),
  attribuer_U1: ("Attente_U1", "Libres"), attribuer_U2: ("Attente_U2", "Libres"),
  annuler_U1: ("Confirmee_U1",), annuler_U2: ("Confirmee_U2",),
)
#let inh = (demander_U1: ("Attente_U2",), demander_U2: ("Attente_U1",))

#let enabled(kind, m, t) = {
  let ok = pre.at(t).all(p => m.at(p, default: 0) >= 1)
  if kind == "r1" and t in inh {
    ok = ok and inh.at(t).all(p => m.at(p, default: 0) == 0)
  }
  ok
}

#let tokens(x, y, n) = {
  import cetz.draw: *
  if n == 1 {
    circle((x, y), radius: 0.09, fill: black, stroke: none)
  } else if n == 2 {
    circle((x - 0.13, y), radius: 0.09, fill: black, stroke: none)
    circle((x + 0.13, y), radius: 0.09, fill: black, stroke: none)
  } else if n > 2 {
    content((x, y), text(weight: "bold", str(n)))
  }
}

// kind : "r1" | "r2" | "r3"; m : marquage; fired : transition franchie juste avant.
#let net(kind, m, fired: none, length: 0.62cm, size: 7pt) = {
  let def = net-def(kind)
  set text(size: size)
  cetz.canvas(length: length, {
    import cetz.draw: *
    // arcs
    for (s, t, ty, via) in def.arcs {
      let pts = (nodes.at(s).pos,) + via + (nodes.at(t).pos,)
      let a = border(s, ..pts.at(1))
      let b = border(t, ..pts.at(-2))
      let path = (a,) + via + (b,)
      if ty == "i" {
        let blocking = m.at(s, default: 0) > 0
        line(..path, stroke: (paint: c-inh, thickness: if blocking { 1.4pt } else { 0.7pt },
            dash: if blocking { none } else { "dashed" }),
          mark: (end: "circle", fill: white, stroke: c-inh, scale: 0.9))
      } else {
        line(..path, stroke: 0.6pt, mark: (end: "stealth", fill: black, scale: 0.55))
      }
    }
    // noeuds
    for name in def.names {
      let n = nodes.at(name)
      let (x, y) = n.pos
      let label = text(font: "DejaVu Sans Mono", size: size - 0.5pt, name.replace("_", "\u{200B}_"))
      if n.kind == "p" {
        circle((x, y), radius: R, fill: white, stroke: 0.8pt)
        tokens(x, y, m.at(name, default: 0))
        if n.side == "w" { content((x - R - 0.12, y), label, anchor: "east") }
        else if n.side == "e" { content((x + R + 0.12, y), label, anchor: "west") }
        else if kind == "r1" { content((x, y - R - 0.08), label, anchor: "north") }
        else { content((x, y + R + 0.1), label, anchor: "south") }
      } else {
        let col = if name == fired { c-fired } else if enabled(kind, m, name) { c-en } else { white }
        rect((x - TW, y - TH), (x + TW, y + TH), fill: col, stroke: 0.8pt)
        if n.side == "w" { content((x - TW - 0.12, y), label, anchor: "east") }
        else { content((x + TW + 0.12, y), label, anchor: "west") }
      }
    }
  })
}

#let legend = {
  set text(size: 8pt)
  let box-t(c) = box(width: 14pt, height: 5pt, fill: c, stroke: 0.6pt, baseline: -1pt)
  grid(columns: 5, column-gutter: 14pt, align: horizon,
    [#box-t(c-en) franchissable],
    [#box-t(c-fired) vient d'être franchie],
    [#box-t(white) non franchissable],
    [#box(width: 18pt, height: 6pt, baseline: -1pt, cetz.canvas(length: 1pt, {
      import cetz.draw: *
      line((0, 3), (18, 3), stroke: (paint: c-inh, thickness: 1.2pt), mark: (end: "circle", fill: white, stroke: c-inh))
    })) arc inhibiteur],
    [#box(width: 8pt, height: 8pt, baseline: 0pt, cetz.canvas(length: 1pt, {
      import cetz.draw: *
      circle((4, 4), radius: 2.2, fill: black, stroke: none)
    })) jeton],
  )
}

// Graphe d'accessibilite (2 utilisateurs, 1 place).
#let reach-graph(with-both: false) = {
  set text(size: 7pt, font: "DejaVu Sans Mono")
  cetz.canvas(length: 0.62cm, {
    import cetz.draw: *
    let st = (
      S0: ((4.5, 0), "I1 I2 L"),
      S1: ((0, -1.8), "A1 I2 L"),
      S2: ((9, -1.8), "I1 A2 L"),
      S3: ((0, -3.6), "C1 I2"),
      S4: ((9, -3.6), "I1 C2"),
      S5: ((0, -5.4), "C1 A2"),
      S6: ((9, -5.4), "A1 C2"),
    )
    if with-both { st.insert("S7", ((4.5, -3.6), "A1 A2 L")) }
    let ed = (
      ("S0", "S1", "d1"), ("S0", "S2", "d2"), ("S1", "S3", "a1"), ("S2", "S4", "a2"),
      ("S3", "S5", "d2"), ("S4", "S6", "d1"),
    )
    if with-both {
      ed += (("S1", "S7", "d2"), ("S2", "S7", "d1"), ("S7", "S5", "a1"), ("S7", "S6", "a2"))
    }
    for (a, b, l) in ed {
      let (pa, _) = st.at(a)
      let (pb, _) = st.at(b)
      let dx = pb.at(0) - pa.at(0)
      let dy = pb.at(1) - pa.at(1)
      let k = calc.min(if dx == 0 { 1e9 } else { 1.45 / calc.abs(dx) }, if dy == 0 { 1e9 } else { 0.38 / calc.abs(dy) })
      let a = (pa.at(0) + dx * k, pa.at(1) + dy * k)
      let b = (pb.at(0) - dx * k, pb.at(1) - dy * k)
      line(a, b, stroke: 0.6pt, mark: (end: "stealth", fill: black, scale: 0.5), name: "e")
      content("e.mid", box(fill: white, inset: 1.2pt, text(fill: rgb("#555"), l)))
    }
    for (k, v) in st {
      let (p, l) = v
      let dead = k in ("S5", "S6")
      let conflict = k == "S7"
      rect((p.at(0) - 1.4, p.at(1) - 0.32), (p.at(0) + 1.4, p.at(1) + 0.32), radius: 0.12,
        fill: if dead { rgb("#fde2e2") } else if conflict { rgb("#fff1d6") } else { white },
        stroke: if dead { c-inh } else if conflict { c-fired } else { 0.6pt })
      content(p, [*#k* #l])
    }
  })
}
