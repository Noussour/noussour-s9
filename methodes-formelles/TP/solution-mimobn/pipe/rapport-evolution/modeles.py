"""Rassemble dans modeles/ les reseaux de chaque etape de l'evolution (format PIPE, mise en page de Walid).

E0 modele naif         : reseau de Walid ou reserver_Ui remet le jeton dans Libres (on teste sans prendre)
E1 reseau de Walid     : ../../../solution-bechar-walid/3-petri/reservation.pnml (tel quel)
E2 retour              : ../2/walid/reservation-retour-2-utilisateurs.pnml
E2b 3 utilisateurs     : E3 sans ses arcs de priorite (pour montrer le conflit non arbitre)
E3 priorite U1>U2>U3   : ../2/walid/reservation-priorite-3-utilisateurs.pnml
E4 U3 confirme         : ../2/walid/reservation-priorite-3-utilisateurs-U3-confirme.pnml
E5 etat Demande        : ../2/walid/reservation-priorite-3-utilisateurs-demande.pnml
"""
import re
import shutil
from pathlib import Path

ICI = Path(__file__).resolve().parent
PIPE = ICI.parent
WALID = PIPE.parents[1] / "solution-bechar-walid" / "3-petri" / "reservation.pnml"
SORTIE = ICI / "modeles"

FICHIERS = {
    "E1": WALID,
    "E2": PIPE / "2" / "walid" / "reservation-retour-2-utilisateurs.pnml",
    "E3": PIPE / "2" / "walid" / "reservation-priorite-3-utilisateurs.pnml",
    "E4": PIPE / "2" / "walid" / "reservation-priorite-3-utilisateurs-U3-confirme.pnml",
    "E5": PIPE / "2" / "walid" / "reservation-priorite-3-utilisateurs-demande.pnml",
}
NOMS = {"E0": "E0-modele-naif", "E1": "E1-reseau-walid", "E2": "E2-retour", "E2b": "E2b-trois-sans-priorite",
        "E3": "E3-priorite-U1-U2-U3", "E4": "E4-U3-confirme-U2-U1-U3", "E5": "E5-etat-demande"}


def arc(s, d, pts, typ="normal"):
    p = "".join('<arcpath id="%03d" x="%.1f" y="%.1f" curvePoint="false"/>' % (i, x, y) for i, (x, y) in enumerate(pts))
    return ('<arc id="%s TO %s" source="%s" target="%s">%s<type value="%s"/><inscription><value>Default,1</value>'
            '</inscription></arc>' % (s, d, s, d, p, typ))


def construire():
    SORTIE.mkdir(exist_ok=True)
    chemins = {}
    for k, src in FICHIERS.items():
        chemins[k] = SORTIE / (NOMS[k] + ".pnml")
        shutil.copyfile(src, chemins[k])
    # E0 : la reservation teste la place libre mais la rend aussitot (verification puis action non atomiques)
    texte = WALID.read_text(encoding="utf-8")
    texte = texte.replace("refuser_Ui est garde par un arc inhibiteur depuis Libres : refus seulement si aucune place libre.",
                          "MODELE NAIF : reserver_Ui teste Libres sans consommer le jeton (arc retour vers Libres).")
    ajout = "\n".join([
        arc("reserver_U1", "Libres", [(440, 240), (470, 210), (470, 150), (585, 135), (600, 120)]),
        arc("reserver_U2", "Libres", [(760, 240), (730, 210), (730, 150), (615, 135), (600, 120)]),
    ])
    chemins["E0"] = SORTIE / (NOMS["E0"] + ".pnml")
    chemins["E0"].write_text(texte.replace("</net>", ajout + "\n</net>"), encoding="utf-8")
    # E2b : E3 sans les arcs inhibiteurs de priorite (Attente_X -> reserver_Y), U1 confirme, U2 et U3 en attente
    texte = FICHIERS["E3"].read_text(encoding="utf-8")
    texte = re.sub(r'<arc id="Attente_U\d TO reserver_U\d"[^\n]*<type value="inhibitor"/>[^\n]*</arc>\n', "", texte)
    texte = texte.replace("Priorite U1 > U2 > U3 (arcs inhibiteurs depuis Attente)", "Aucune regle de priorite")
    chemins["E2b"] = SORTIE / (NOMS["E2b"] + ".pnml")
    chemins["E2b"].write_text(texte, encoding="utf-8")
    return {k: chemins[k] for k in NOMS}


if __name__ == "__main__":
    for k, c in construire().items():
        print(k, c.name)
