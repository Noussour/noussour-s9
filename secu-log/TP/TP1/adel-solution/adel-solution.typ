#set document(title: "Practical Lab 1: Classical Ciphers", author: "Adel HADJ ARAB")
#set page(paper: "a4", margin: (x: 2cm, y: 1.8cm), numbering: "1 / 1",
  header: context if counter(page).get().first() > 1 [
    #set text(8pt, fill: luma(120))
    Adel HADJ ARAB #h(1fr) Practical Lab 1: Classical Ciphers
  ])
#set text(font: "New Computer Modern", size: 10.5pt)
#set par(justify: true, leading: 0.62em, spacing: 0.9em)
#let accent = rgb("#1f4e79")
#show heading.where(level: 1): it => block(above: 1.6em, below: 0.8em, width: 100%)[
  #text(13pt, weight: "bold", fill: accent, it.body)
  #v(-0.5em)
  #line(length: 100%, stroke: 0.6pt + accent)
]
#show heading.where(level: 2): it => block(above: 1.1em, below: 0.6em, text(11pt, weight: "bold", it.body))
#show raw.where(block: true): it => block(fill: luma(245), stroke: (left: 2pt + accent), inset: (x: 8pt, y: 6pt), width: 100%, text(size: 9pt, it))
#show figure: set block(above: 0.8em, below: 1em)
#show figure.caption: set text(size: 8.5pt, fill: luma(70))
#set table(stroke: 0.4pt + luma(170), inset: 5pt)

#let shot(file, caption, px: 1036) = figure(
  image("screenshots/" + file, width: px / 1036 * 85%),
  caption: caption,
)
#let q(body) = text(weight: "bold", fill: accent, body)
#let grid5(rows, hl: ()) = table(
  columns: (1.6em,) * 5, align: center,
  ..rows.flatten().map(c => if c in hl { table.cell(fill: rgb("#dbe8f5"))[*#c*] } else { [#c] })
)

#align(center)[
  #block(text(15pt, weight: "bold", fill: accent)[Practical Lab 1: Classical Ciphers])
  #block(above: 0.5em, text(11pt)[Adel HADJ ARAB · ID 222231482117])
  #block(above: 0.4em, text(9.5pt, fill: luma(90))[Sécurité de Logiciel · USTHB · 2026/2027])
]
#v(0.4em)

#block(fill: luma(245), inset: 9pt, radius: 3pt, width: 100%)[
  *Tool.* The ciphers were run with *RusCrypt 0.3.0* (`ruscrypt`, a Rust command-line cryptography toolkit) instead of CrypTool 1. Each operation is one command (`ruscrypt encrypt|decrypt --caesar|--playfair|--vigenere`) that asks for the text and the key. The figures are captures of these terminal sessions.

  *Conventions.* Only the 26 letters are transformed; spaces and digits are kept unchanged. Playfair works on letters only, in capitals, with J merged into I. Vigenère advances the key only on letters.
]

= 1. Caesar cipher

Each letter is shifted by the key in the alphabet: $C = (P + k) mod 26$ to encrypt, $P = (C - k) mod 26$ to decrypt. Here $k = 3$.

== b. Encrypt "Adel HADJ ARAB 222231482117" with key 3

#shot(px: 876, "1b.png", [`ruscrypt encrypt --caesar`, shift 3.])

#q[Output:] `Dgho KDGM DUDE 222231482117`

#q[Manual check] (each letter + 3):

#table(columns: 12, align: center,
  [A], [d], [e], [l], [H], [A], [D], [J], [A], [R], [A], [B],
  [D], [g], [h], [o], [K], [D], [G], [M], [D], [U], [D], [E],
)
The digits are not letters, so they stay `222231482117`. Result: `Dgho KDGM DUDE 222231482117`, same as the tool.

== c. Decrypt "dojhuld irrwedoo whdp lv qrw jrrg qrz" with key 3

#shot(px: 1036, "1c.png", [`ruscrypt decrypt --caesar`, shift 3.])

#q[Output:] `algeria football team is not good now`

#q[Manual check] (each letter − 3): d→a, o→l, j→g, h→e, u→r, l→i, d→a gives *algeria*; i→f, r→o, r→o, w→t, e→b, d→a, o→l, o→l gives *football*; w→t, h→e, d→a, p→m gives *team*; l→i, v→s gives *is*; q→n, r→o, w→t gives *not*; j→g, r→o, r→o, g→d gives *good*; q→n, r→o, z→w gives *now*. Same as the tool.

= 2. Playfair cipher

The key fills a 5×5 grid (J = I), then the rest of the alphabet. The message is split into pairs. Rules: same row → take the letter to the right (left to decrypt); same column → the letter below (above to decrypt); otherwise → the two other corners of the rectangle, each letter keeping its own row.

== a. Encrypt "Adel HADJ ARAB" with key "king"

#shot(px: 652, "2a.png", [`ruscrypt encrypt --playfair`, key `king`.])

#q[Output:] `NFCOPKCNIUKF`

#q[Manual check.] Grid for KING and pairs of `ADELHADIARAB` (J → I):

#block(breakable: false, grid(columns: (auto, 1fr), gutter: 16pt,
  grid5((("K","I","N","G","A"), ("B","C","D","E","F"), ("H","L","M","O","P"), ("Q","R","S","T","U"), ("V","W","X","Y","Z")), hl: ("A","D","N","F")),
  table(columns: 3, align: (center, left, center),
    table.header([*Pair*], [*Rule*], [*Result*]),
    [AD], [rectangle: A(r0,c4) D(r1,c2)], [NF],
    [EL], [rectangle: E(r1,c3) L(r2,c1)], [CO],
    [HA], [rectangle: H(r2,c0) A(r0,c4)], [PK],
    [DI], [rectangle: D(r1,c2) I(r0,c1)], [CN],
    [AR], [rectangle: A(r0,c4) R(r3,c1)], [IU],
    [AB], [rectangle: A(r0,c4) B(r1,c0)], [KF],
  ),
))
Result `NF CO PK CN IU KF` = `NFCOPKCNIUKF`, same as the tool (highlighted: the first pair AD → NF).

== b. Decrypt "OMDXFNOMFQHUDLEK" with key "sun"

#shot(px: 700, "2b.png", [`ruscrypt decrypt --playfair`, key `sun`.])

#q[Output:] `THEWEATHERISFINE` (THE WEATHER IS FINE)

#q[Manual check.] Grid for SUN and the pairs:

#block(breakable: false, grid(columns: (auto, 1fr), gutter: 16pt,
  grid5((("S","U","N","A","B"), ("C","D","E","F","G"), ("H","I","K","L","M"), ("O","P","Q","R","T"), ("V","W","X","Y","Z")), hl: ("E","K")),
  table(columns: 3, align: (center, left, center),
    table.header([*Pair*], [*Rule*], [*Result*]),
    [OM], [rectangle], [TH],
    [DX], [rectangle], [EW],
    [FN], [rectangle], [EA],
    [OM], [rectangle], [TH],
    [FQ], [rectangle], [ER],
    [HU], [rectangle], [IS],
    [DL], [rectangle], [FI],
    [EK], [same column (c2): letter above], [NE],
  ),
))
Result `THEWEATHERISFINE`, same as the tool.

= 3. Vigenère cipher

Letter $i$ is shifted by the value of key letter $i$ (A = 0, …, Z = 25), the key being repeated: $C_i = (P_i + K_i) mod 26$, $P_i = (C_i - K_i) mod 26$.

== a. Encrypt "Adel HADJ ARAB 222231482117" with key "usthb"

#shot(px: 876, "3a.png", [`ruscrypt encrypt --vigenere`, key `usthb`.])

#q[Output:] `Uvxs IUVC HSUT 222231482117`

#q[Manual check] (U=20, S=18, T=19, H=7, B=1):

#table(columns: 13, align: center,
  [*P*], [A], [D], [E], [L], [H], [A], [D], [J], [A], [R], [A], [B],
  [*K*], [U], [S], [T], [H], [B], [U], [S], [T], [H], [B], [U], [S],
  [*C*], [U], [V], [X], [S], [I], [U], [V], [C], [H], [S], [U], [T],
)
For example D(3) + S(18) = 21 = V and J(9) + T(19) = 28 mod 26 = 2 = C. Digits unchanged. Result `Uvxs IUVC HSUT 222231482117`, same as the tool.

== c. Decrypt "br eyrlcay cf uuauyydyq" with key "sun"

#shot(px: 812, "3c.png", [`ruscrypt decrypt --vigenere`, ciphertext exactly as given.])

#q[Output as given:] `jx rgxykgl kl hcghgeqgw`, which is not readable.

The ciphertext in the statement is missing its first letter. Decrypting it with the key shifted by one position (starting at U instead of S) gives "he meeting is cancelled", so the original ciphertext is `lbr eyrlcay cf uuauyydyq`. Encrypting "the meeting is cancelled" with SUN gives exactly that text.

#shot(px: 828, "3d.png", [`ruscrypt decrypt --vigenere` with the missing first letter `l` restored.])

#q[Output:] `the meeting is cancelled`

#block(breakable: false)[
#q[Manual check] (S=18, U=20, N=13):

#let vrow(c, k, p) = table(columns: 8, align: center, inset: 4pt,
  [*C*], ..c.map(x => [#x]), [*K*], ..k.map(x => [#x]), [*P*], ..p.map(x => [#x]))
#grid(columns: 3, gutter: 8pt, vrow(("l","b","r","e","y","r","l"), ("s","u","n","s","u","n","s"), ("t","h","e","m","e","e","t")), vrow(("c","a","y","c","f","u","u"), ("u","n","s","u","n","s","u"), ("i","n","g","i","s","c","a")), vrow(("a","u","y","y","d","y","q"), ("n","s","u","n","s","u","n"), ("n","c","e","l","l","e","d")))
]
For example l(11) − s(18) = −7 mod 26 = 19 = t, and q(16) − n(13) = 3 = d. Result *the meeting is cancelled*, same as the tool.

= Summary

#table(columns: (auto, auto, 1fr, 1fr), align: left,
  table.header([*Cipher*], [*Key*], [*Input*], [*Output*]),
  [Caesar enc.], [3], [Adel HADJ ARAB 222231482117], [Dgho KDGM DUDE 222231482117],
  [Caesar dec.], [3], [dojhuld irrwedoo whdp lv qrw jrrg qrz], [algeria football team is not good now],
  [Playfair enc.], [king], [Adel HADJ ARAB], [NFCOPKCNIUKF],
  [Playfair dec.], [sun], [OMDXFNOMFQHUDLEK], [THEWEATHERISFINE],
  [Vigenère enc.], [usthb], [Adel HADJ ARAB 222231482117], [Uvxs IUVC HSUT 222231482117],
  [Vigenère dec.], [sun], [(l)br eyrlcay cf uuauyydyq], [the meeting is cancelled],
)
