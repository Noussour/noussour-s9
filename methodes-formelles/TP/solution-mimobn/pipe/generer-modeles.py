"""Genere les modeles PIPE 5 du dossier 2, au format et avec la mise en page du modele de Walid
(../solution-bechar-walid/3-petri/reservation.pnml) : grille reguliere, arcs orthogonaux avec points
de passage, identifiants d'arcs « source TO cible ».

  2/<style>/reservation-retour-2-utilisateurs.pnml   : un utilisateur refuse ou ayant annule peut revenir en attente
  2/<style>/reservation-priorite-3-utilisateurs.pnml : 3 utilisateurs, une seule place, priorite U1 > U2 > U3
                                                       (U1 deja confirme, U2 en attente, U3 vient reserver)
  <style> = walid  : refus garde par un arc inhibiteur depuis Libres (interpretation de Walid)
          | mimobn : refus garde par un arc de lecture sur Occupees (reseau P/T pur)

Usage : python generer-modeles.py [--png]   (--png dessine aussi un apercu de chaque reseau)
"""
import sys
from pathlib import Path

ici = Path(__file__).parent


class Reseau:
    def __init__(self, nom, commentaire, dx=0, dy=200):
        # decalage (dx, dy) : les couloirs d'arcs du haut et de gauche restent en coordonnees positives
        self.nom, self.commentaire, self.dx, self.dy = nom, commentaire, dx, dy
        self.places, self.trans, self.arcs = {}, {}, []

    def place(self, i, x, y, m=0, lab=(47.5, 47.0)):
        self.places[i] = (x + self.dx, y + self.dy, m, lab)

    def transition(self, i, x, y, lab=(-7.0, 19.0)):
        self.trans[i] = (x + self.dx, y + self.dy, lab)

    def centre(self, i):
        return self.places[i][:2] if i in self.places else self.trans[i][:2]

    def arc(self, s, d, via=(), kind="normal"):
        pts = [self.centre(s)] + [(x + self.dx, y + self.dy) for x, y in via] + [self.centre(d)]
        self.arcs.append((s, d, pts, kind))

    def ecrire(self, chemin):
        o = ['<?xml version="1.0" encoding="UTF-8"?>', "<!-- %s -->" % self.commentaire, "<pnml>", "<net>",
             '<token id="Default" red="0" green="0" blue="0"/>']
        for i, (x, y, m, (lx, ly)) in self.places.items():
            o.append('<place id="%s"><graphics><position x="%.1f" y="%.1f"/></graphics><name><value>%s</value>'
                     '<graphics><offset x="%.1f" y="%.1f"/></graphics></name><initialMarking><value>Default,%d</value>'
                     '<graphics><offset x="0.0" y="0.0"/></graphics></initialMarking><capacity><value>0</value>'
                     '</capacity></place>' % (i, x - 15, y - 15, i, lx, ly, m))
        for i, (x, y, (lx, ly)) in self.trans.items():
            o.append('<transition id="%s"><graphics><position x="%.1f" y="%.1f"/></graphics><name><value>%s</value>'
                     '<graphics><offset x="%.1f" y="%.1f"/></graphics></name><orientation><value>0</value></orientation>'
                     '<rate><value>1.0</value></rate><timed><value>false</value></timed><infiniteServer><value>false'
                     '</value></infiniteServer><priority><value>1</value></priority></transition>'
                     % (i, x - 5, y - 15, i, lx, ly))
        for s, d, pts, kind in self.arcs:
            path = "".join('<arcpath id="%03d" x="%.1f" y="%.1f" curvePoint="false"/>' % (k, x, y)
                           for k, (x, y) in enumerate(pts))
            o.append('<arc id="%s TO %s" source="%s" target="%s">%s<type value="%s"/><inscription>'
                     '<value>Default,1</value></inscription></arc>' % (s, d, s, d, path, kind))
        o += ["</net>", "</pnml>", ""]
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text("\n".join(o), encoding="utf-8")

    def apercu(self, chemin):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        xs = [p[0] for p in self.places.values()] + [t[0] for t in self.trans.values()]
        ys = [p[1] for p in self.places.values()] + [t[1] for t in self.trans.values()]
        for _, _, pts, _ in self.arcs:
            xs += [p[0] for p in pts]; ys += [p[1] for p in pts]
        w, h = max(xs) - min(xs) + 200, max(ys) - min(ys) + 160
        fig, ax = plt.subplots(figsize=(w / 90, h / 90))
        for s, d, pts, kind in self.arcs:
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color="#c0392b" if kind == "inhibitor" else "#333",
                    lw=1.1, zorder=1)
            (x0, y0), (x1, y1) = pts[-2], pts[-1]
            ax.annotate("", xy=(x1 - (x1 - x0) * 0.0, y1), xytext=(x0, y0), zorder=1,
                        arrowprops=dict(arrowstyle="-|>" if kind == "normal" else "-", lw=0, color="#333",
                                        shrinkA=0, shrinkB=16))
        for i, (x, y, m, _) in self.places.items():
            ax.add_patch(plt.Circle((x, y), 15, fc="white", ec="#111", lw=1.4, zorder=3))
            if m: ax.add_patch(plt.Circle((x, y), 4, color="#111", zorder=4))
            ax.text(x, y + 30, i, ha="center", va="top", fontsize=7, zorder=5)
        for i, (x, y, _) in self.trans.items():
            ax.add_patch(plt.Rectangle((x - 5, y - 15), 10, 30, color="#111", zorder=3))
            ax.text(x + 9, y - 18, i, ha="left", va="bottom", fontsize=6.5, color="#1f4e79", zorder=5)
        ax.set_xlim(min(xs) - 100, max(xs) + 100); ax.set_ylim(max(ys) + 80, min(ys) - 80)
        ax.set_aspect("equal"); ax.axis("off")
        fig.savefig(chemin, dpi=110, bbox_inches="tight"); plt.close(fig)


STYLES = {
    "walid": dict(L="Libres", O="Occupees", A="Attente_", C="Confirmee_", F="Refusee_", N="Annulee_",
                  res="reserver_", ref="refuser_", ab="abandonner_", an="annuler_", rr="retour_refus_",
                  ra="reessayer_", D="Demande_", rj="rejoindre_", lecture=False),
    "mimobn": dict(L="Libres", O="Occupees", A="Attente_", C="Confirmee_", F="Refusee_", N="Annulee_",
                   res="Confirmer_", ref="Refuser_", ab="Abandonner_", an="Annuler_", rr="RetourRefus_",
                   ra="RetourAnnulee_", D="Demande_", rj="Rejoindre_", lecture=True),
}


def bloc(r, st, u, X, s, etat, demande=False):
    """Bloc d'un utilisateur, disposition de Walid : colonne X = Attente / abandonner / Annulee,
    colonne X+140s = reserver / Confirmee / annuler (cote ressources), colonne X-140s = refuser / Refusee
    (cote exterieur), et a l'exterieur les deux transitions de retour.
    demande=True : les retours passent par un etat Demande (colonne X-270s) avant de rejoindre Attente."""
    A, C, F, N = (st[k] + u for k in "ACFN")
    res, ref, ab, an, rr, ra = (st[k] + u for k in ("res", "ref", "ab", "an", "rr", "ra"))
    ext = (-7.0, 19.0) if s > 0 else (82.0, 19.0)
    r.place(A, X, 240, 1 if etat == "attente" else 0, (47.5, -7.0))
    r.place(C, X + 140 * s, 360, 1 if etat == "confirme" else 0, (-5.0 if s > 0 else 113.0, 19.0))
    r.place(F, X - 140 * s, 360)
    r.place(N, X, 480)
    r.transition(res, X + 140 * s, 240, (-3.0 if s > 0 else 84.5, 37.0))
    r.transition(ref, X - 140 * s, 240, ext)
    r.transition(ab, X, 360, ext)
    r.transition(an, X + 140 * s, 480, (-3.0 if s > 0 else 78.0, 37.0))
    r.transition(rr, X - 210 * s, 360, (-3.0, 37.0))
    r.transition(ra, X - 270 * s, 480, (-3.0, 37.0))
    r.arc(A, ref); r.arc(A, res); r.arc(A, ab)
    r.arc(res, C); r.arc(ref, F); r.arc(ab, N); r.arc(C, an); r.arc(an, N)
    r.arc(F, rr)
    r.arc(N, ra)
    if demande:  # retours : Refusee / Annulee -> Demande -> rejoindre -> Attente
        D, rj = st["D"] + u, st["rj"] + u
        r.place(D, X - 270 * s, 240, 0, (47.5, -7.0))
        r.transition(rj, X - 270 * s, 150, (-3.0, -8.0))
        r.arc(rr, D, via=[(X - 210 * s, 240)])
        r.arc(ra, D)
        r.arc(D, rj)
        r.arc(rj, A, via=[(X, 150)])
    else:  # retours directs : Refusee -> retour_refus -> Attente, Annulee -> reessayer -> Attente
        r.arc(rr, A, via=[(X - 210 * s, 190), (X - 50 * s, 190)])
        r.arc(ra, A, via=[(X - 270 * s, 150), (X, 150)])


def ressources_paire(r, st, u, X, s, R):
    """Arcs vers Libres/Occupees (colonne R) exactement comme dans le modele de Walid."""
    L, O = st["L"], st["O"]
    res, ref, an = st["res"] + u, st["ref"] + u, st["an"] + u
    r.arc(L, res, via=[(X + 140 * s, 120)])
    r.arc(res, O)
    r.arc(O, an, via=[(R - 40 * s, 280), (R - 40 * s, 560), (X + 140 * s, 560)])
    r.arc(an, L, via=[(R - 100 * s, 480), (R - 100 * s, 160), (R - 40 * s, 160)])
    if st["lecture"]:  # refus seulement si la place est occupee : arc aller-retour avec Occupees
        r.arc(O, ref, via=[(R - 70 * s, 210), (R - 70 * s, 80), (X - 140 * s, 80)])
        r.arc(ref, O, via=[(X - 170 * s, 210), (X - 170 * s, 60), (R - 80 * s, 60), (R - 80 * s, 220)])
    else:  # refus seulement si aucune place libre : arc inhibiteur depuis Libres
        r.arc(L, ref, via=[(R - 40 * s, 80), (X - 140 * s, 80)], kind="inhibitor")


def modele_2(st, style):
    r = Reseau("Reservation_retour", "Reseau de Petri : 2 utilisateurs, 1 place, retour apres refus ou annulation "
               "(retour_refus, reessayer). Style %s. Invariant : Libres + Occupees = 1." % style)
    r.place(st["L"], 600, 120, 1, (34.5, 65.0)); r.place(st["O"], 600, 240, 0, (41.0, -5.0))
    bloc(r, st, "U1", 300, +1, "attente"); ressources_paire(r, st, "U1", 300, +1, 600)
    bloc(r, st, "U2", 900, -1, "attente"); ressources_paire(r, st, "U2", 900, -1, 600)
    return r


def modele_3(st, style, u3_confirme=False, demande=False):
    """u3_confirme=False : U1 confirme, U2 en attente, U3 vient reserver ; priorite U1 > U2 > U3.
    u3_confirme=True  : U3 confirme, U1 et U2 en attente ; U1 attend apres U2, donc priorite U2 > U1 > U3
                        (les deux arcs de priorite vers reserver_U3 sont conserves).
    demande=True (avec u3_confirme) : un utilisateur qui revient (apres refus, abandon ou annulation) passe par
                        Demande et ne peut rejoindre Attente tant qu'un utilisateur qu'il depasserait y attend."""
    if demande:
        r = Reseau("Reservation_priorite_3_U3_demande", "Reseau de Petri : 3 utilisateurs, 1 place. U3 confirme, U1 "
                   "et U2 en attente, priorite U2 > U1 > U3. Un utilisateur qui revient passe par Demande et ne "
                   "regagne pas sa priorite sur ceux qui attendent deja. Style %s." % style, dx=40, dy=260)
        etats = ("attente", "attente", "confirme")
    elif u3_confirme:
        r = Reseau("Reservation_priorite_3_U3", "Reseau de Petri : 3 utilisateurs, 1 place. U3 confirme, U1 et U2 en "
                   "attente, U1 attend apres U2. Priorite U2 > U1 > U3 (arcs inhibiteurs depuis Attente). Style %s."
                   % style)
        etats = ("attente", "attente", "confirme")
    else:
        r = Reseau("Reservation_priorite_3", "Reseau de Petri : 3 utilisateurs, 1 place. U1 confirme, U2 en attente, "
                   "U3 vient reserver. Priorite U1 > U2 > U3 (arcs inhibiteurs depuis Attente). Style %s." % style)
        etats = ("confirme", "attente", "attente")
    L, O, A, res, ref, an = st["L"], st["O"], st["A"], st["res"], st["ref"], st["an"]
    r.place(L, 600, 120, 0, (34.5, 65.0)); r.place(O, 600, 240, 1, (41.0, -5.0))
    bloc(r, st, "U1", 300, +1, etats[0], demande); ressources_paire(r, st, "U1", 300, +1, 600)
    bloc(r, st, "U2", 900, -1, etats[1], demande); ressources_paire(r, st, "U2", 900, -1, 600)
    X = 1560
    bloc(r, st, "U3", X, +1, etats[2], demande)
    rs, rf = X + 140, X - 140  # colonnes de reserver_U3 et refuser_U3
    # U3, a droite de U2 : couloirs au-dessus (vers Libres) et au-dessous (vers Occupees) de tout le reste ;
    # chaque arc rejoint Libres / Occupees par sa propre colonne verticale (x = 592, 600, 608)
    r.arc(L, res + "U3", via=[(600, 0), (rs, 0)])
    r.arc(res + "U3", O, via=[(rs + 60, 240), (rs + 60, 660), (592, 660), (592, 255)])
    r.arc(O, an + "U3", via=[(608, 255), (608, 620), (rs, 620)])
    r.arc(an + "U3", L, via=[(rs + 120, 480), (rs + 120, -40), (592, -40), (592, 105)])
    if st["lecture"]:
        r.arc(O, ref + "U3", via=[(584, 275), (584, 700), (rf - 30, 700), (rf - 30, 270)])
        r.arc(ref + "U3", O, via=[(rf + 30, 270), (rf + 30, 740), (576, 740), (576, 285)])
    else:
        r.arc(L, ref + "U3", via=[(608, 105), (608, 40), (rf, 40)], kind="inhibitor")
    # priorite : une transition de reservation est bloquee tant qu'un utilisateur prioritaire attend
    if u3_confirme:  # U1 attend apres U2 : reserver_U1 bloquee tant que U2 attend (couloir du bas)
        r.arc(A + "U2", res + "U1", via=[(860, 280), (830, 280), (830, 860), (480, 860), (480, 280)],
              kind="inhibitor")
    else:
        r.arc(A + "U1", res + "U2", via=[(340, 200), (340, -80), (720, -80), (720, 200)], kind="inhibitor")
    r.arc(A + "U1", res + "U3", via=[(340, 280), (370, 280), (370, 820), (rs - 40, 820), (rs - 40, 280)],
          kind="inhibitor")
    r.arc(A + "U2", res + "U3", via=[(860, 200), (860, -120), (rs + 40, -120), (rs + 40, 200)], kind="inhibitor")
    if demande:
        # un utilisateur qui revient ne repasse pas devant ceux qui attendent et qu'il depasserait :
        # U2 (prioritaire) attend que U1 et U3 ne soient plus en attente ; U1 attend que U3 ne le soit plus
        rj = st["rj"]
        r.arc(A + "U1", rj + "U2", via=[(340, 200), (340, -160), (1200, -160), (1200, 150)], kind="inhibitor")
        r.arc(A + "U3", rj + "U2", via=[(X + 40, 200), (X + 40, -200), (1170, -200)], kind="inhibitor")
        r.arc(A + "U3", rj + "U1", via=[(X + 40, 280), (X + 40, 900), (0, 900), (0, 150)], kind="inhibitor")
    return r


for style, st in STYLES.items():
    for nom, f in (("reservation-retour-2-utilisateurs", modele_2),
                   ("reservation-priorite-3-utilisateurs", modele_3),
                   ("reservation-priorite-3-utilisateurs-U3-confirme", lambda st, s: modele_3(st, s, True)),
                   ("reservation-priorite-3-utilisateurs-demande", lambda st, s: modele_3(st, s, True, True))):
        r = f(st, style)
        r.ecrire(ici / "2" / style / (nom + ".pnml"))
        if "--png" in sys.argv:
            r.apercu(ici / "2" / style / (nom + ".png"))
print("ok")
