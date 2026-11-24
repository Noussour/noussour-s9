"""Draw the explanatory figures used by the module summaries (RESUME/figures/).

Run from any directory: python scripts/figures-resumes.py
Requires matplotlib. Every figure is generated from code, so it can be edited and redrawn.
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

ROOT = Path(__file__).resolve().parent.parent
NAVY, TEAL, PALE, GREY, LIGHT = '#193650', '#087d85', '#eef4f8', '#536778', '#d5e1e9'
AMBER, RED, GREEN, WHITE = '#f59e0b', '#dc2626', '#16a34a', '#ffffff'
SOFT_TEAL, SOFT_AMBER, SOFT_RED, SOFT_GREEN = '#d7eef0', '#fdecc8', '#fde2e2', '#dcf3e4'


# ------------------------------------------------------------------ helpers
def canvas(w, h, xlim, ylim):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig, ax


def save(fig, module, name):
    out = ROOT / module / 'RESUME' / 'figures'
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, dpi=170, bbox_inches='tight', facecolor='white', pad_inches=0.12)
    plt.close(fig)
    print('  ', module, name)


def box(ax, x, y, w, h, text='', fc=PALE, ec=NAVY, fs=9, color=NAVY, weight='bold', r=0.12, lw=1.4, ls='-', z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=%s' % r,
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=fs, color=color,
                fontweight=weight, zorder=z + 1, linespacing=1.25)


def txt(ax, x, y, s, fs=9, color=NAVY, ha='center', va='center', weight='normal', style='normal', z=5, **kw):
    ax.text(x, y, s, ha=ha, va=va, fontsize=fs, color=color, fontweight=weight, fontstyle=style, zorder=z,
            linespacing=1.25, **kw)


def arrow(ax, a, b, color=NAVY, lw=1.5, style='-|>', rad=0.0, ls='-', ms=12, z=3):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, ls=ls,
                                 connectionstyle='arc3,rad=%s' % rad, zorder=z, shrinkA=0, shrinkB=0))


# ------------------------------------------------------------------ Petri drawing
PR, TW, TH = 0.36, 0.95, 0.3


def place(ax, x, y, label='', tokens=0, side='below'):
    ax.add_patch(Circle((x, y), PR, fc=WHITE, ec=NAVY, lw=1.6, zorder=3))
    if tokens == 1:
        ax.add_patch(Circle((x, y), 0.1, fc='black', zorder=5))
    elif tokens > 1:
        txt(ax, x, y, str(tokens), fs=11, weight='bold')
    if label:
        dy = {'below': (0, -0.62), 'above': (0, 0.62), 'left': (-0.5, 0), 'right': (0.5, 0)}[side]
        ha = {'left': 'right', 'right': 'left'}.get(side, 'center')
        txt(ax, x + dy[0], y + dy[1], label, fs=8.2, ha=ha)


def trans(ax, x, y, label='', state='idle', vertical=False, side='right', w=None, h=None):
    fc = {'idle': LIGHT, 'ok': '#34d399', 'fired': AMBER, 'blocked': '#e2e8f0'}[state]
    ww, hh = (TH, TW) if vertical else (TW, TH)
    ax.add_patch(Rectangle((x - ww / 2, y - hh / 2), ww, hh, fc=fc, ec=NAVY, lw=1.3, zorder=3))
    if label:
        dx = {'right': (ww / 2 + 0.12, 0), 'left': (-ww / 2 - 0.12, 0), 'above': (0, hh / 2 + 0.25), 'below': (0, -hh / 2 - 0.25)}[side]
        ha = {'right': 'left', 'left': 'right'}.get(side, 'center')
        txt(ax, x + dx[0], y + dx[1], label, fs=8.2, ha=ha, style='italic', color='#334155')


def edge_point(c, toward, is_place, vertical=False):
    dx, dy = toward[0] - c[0], toward[1] - c[1]
    d = math.hypot(dx, dy) or 1
    ux, uy = dx / d, dy / d
    if is_place:
        r = PR
    else:
        ww, hh = (TH, TW) if vertical else (TW, TH)
        r = min((ww / 2) / abs(ux) if ux else 1e9, (hh / 2) / abs(uy) if uy else 1e9)
    return (c[0] + ux * r, c[1] + uy * r)


def parc(ax, p, t, place_to_trans=True, vertical=False, rad=0.0, inhibitor=False, color=NAVY):
    """arc between place centre p and transition centre t"""
    if place_to_trans:
        a, b = edge_point(p, t, True), edge_point(t, p, False, vertical)
    else:
        a, b = edge_point(t, p, False, vertical), edge_point(p, t, True)
    if inhibitor:
        ux, uy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(ux, uy)
        end = (b[0] - ux / d * 0.16, b[1] - uy / d * 0.16)
        ax.add_patch(FancyArrowPatch(a, end, arrowstyle='-', color=RED, lw=1.6, connectionstyle='arc3,rad=%s' % rad, zorder=2))
        ax.add_patch(Circle((b[0] - ux / d * 0.08, b[1] - uy / d * 0.08), 0.085, fc=WHITE, ec=RED, lw=1.6, zorder=4))
    else:
        arrow(ax, a, b, color=color, lw=1.3, rad=rad, ms=10, z=2)


# =================================================================== METHODES FORMELLES
def fig_petri_franchissement():
    fig, ax = canvas(8.2, 3.2, (-1.8, 15.0), (-2.7, 2.4))
    for off, tok, lab in ((0.0, (1, 1, 0), 'M0 = (1, 1, 0)'), (9.0, (0, 0, 1), 'M1 = (0, 0, 1)')):
        a, b, t, c = (off, 1.05), (off, -1.05), (off + 2.8, 0), (off + 5.6, 0)
        place(ax, *a, 'PlacesDisponibles', tok[0], 'above')
        place(ax, *b, 'DemandesEnAttente', tok[1], 'below')
        place(ax, *c, 'ReservationsConfirmees', tok[2], 'below')
        trans(ax, *t, '', 'ok' if off == 0 else 'fired')
        txt(ax, off + 2.8, -0.95, 'Confirmer\nReservation', fs=8.2, style='italic', color='#334155')
        parc(ax, a, t, True)
        parc(ax, b, t, True)
        parc(ax, c, t, False)
        txt(ax, off + 2.8, -2.45, lab, fs=9.5, weight='bold', color=TEAL)
    arrow(ax, (6.9, 0), (8.2, 0), color=AMBER, lw=2.6, ms=18)
    txt(ax, 7.55, 0.42, 'franchir', fs=8.5, color=AMBER, weight='bold')
    save(fig, 'methodes-formelles', 'petri-franchissement.png')


def fig_petri_graphe():
    fig = plt.figure(figsize=(7.4, 6.1))
    ax = fig.add_axes([0, 0.34, 1, 0.66])
    ax.set_xlim(-1.6, 5.6); ax.set_ylim(-0.3, 5.9); ax.set_aspect('equal'); ax.axis('off')
    P = {'p1': (0, 5), 'p2': (0, 3), 'p3': (4, 3), 'p4': (2, 1.6)}
    T = {'t1': (0, 4), 't2': (0, 0.6), 't3': (2, 3)}
    mark = {'p1': 1, 'p2': 0, 'p3': 0, 'p4': 1}
    for k, c in P.items():
        place(ax, *c, '', mark[k])
    labs = {'p1': (-0.55, 0, 'right'), 'p2': (-0.55, 0, 'right'), 'p3': (0.55, 0, 'left'), 'p4': (0.55, 0, 'left')}
    for k, (dx, dy, ha) in labs.items():
        txt(ax, P[k][0] + dx, P[k][1] + dy, k, fs=10, ha=ha, weight='bold')
    for k, c in T.items():
        trans(ax, *c, '', 'ok' if k == 't1' else 'idle')
        txt(ax, c[0] + 0.7, c[1] + (0.0 if k != 't3' else 0.35), k, fs=10, ha='left', weight='bold', style='italic')
    parc(ax, P['p1'], T['t1'], True); parc(ax, P['p2'], T['t1'], False)
    parc(ax, P['p2'], T['t2'], True); parc(ax, P['p4'], T['t2'], True)
    parc(ax, P['p1'], T['t2'], False, rad=-0.55)
    parc(ax, P['p3'], T['t2'], False, rad=0.25)
    parc(ax, P['p2'], T['t3'], True, rad=0.3); parc(ax, P['p2'], T['t3'], False, rad=0.3)
    parc(ax, P['p3'], T['t3'], True); parc(ax, P['p4'], T['t3'], False)
    txt(ax, 2.6, 5.75, "Réseau d'exemple : 4 places, 3 transitions, M0 = (1, 0, 0, 1)", fs=9.5, weight='bold', color=TEAL)

    ax2 = fig.add_axes([0, 0.0, 1, 0.32])
    ax2.set_xlim(-0.4, 15.0); ax2.set_ylim(-2.3, 1.3); ax2.set_aspect('equal'); ax2.axis('off')
    xs = (0.0, 3.9, 7.8, 11.7)
    names = ('M0  (1, 0, 0, 1)', 'M1  (0, 1, 0, 1)', 'M2  (1, 0, 1, 0)', 'M3  (0, 1, 1, 0)')
    for i, (x, nm) in enumerate(zip(xs, names)):
        box(ax2, x, -0.35, 2.9, 0.7, nm, fc=SOFT_TEAL if i == 0 else WHITE, fs=7.8)
    for x1, x2, t in zip(xs, xs[1:], ('t1', 't2', 't1')):
        arrow(ax2, (x1 + 2.9, 0), (x2, 0), lw=1.4)
        txt(ax2, (x1 + 2.9 + x2) / 2, 0.38, t, fs=9, color='#b45309', weight='bold')
    arrow(ax2, (xs[3] + 1.45, -0.38), (xs[1] + 1.45, -0.38), rad=-0.32, lw=1.3, color=GREY)
    txt(ax2, (xs[1] + xs[3]) / 2 + 1.45, -1.55, 't3 : retour à M1', fs=8.5, color='#b45309', weight='bold',
        bbox=dict(fc='white', ec='none', pad=1.5))
    txt(ax2, 7.2, 1.0, 'Graphe de marquages : 4 états, aucun blocage, M0 jamais revisité', fs=9.5, weight='bold', color=TEAL)
    save(fig, 'methodes-formelles', 'petri-graphe-marquages.png')


def fig_petri_inhibiteur():
    fig, ax = canvas(8.4, 4.2, (-1.2, 20.4), (-5.6, 2.1))
    for off, nb, ok_c, ok_r, title in ((0.0, 1, 'ok', 'blocked', 'Situation 1 : une place est libre'),
                                        (10.4, 0, 'blocked', 'ok', 'Situation 2 : plus aucune place')):
        dem, pl = (off + 0.2, 0.0), (off + 0.2, -3.0)
        tc, tr = (off + 3.6, -0.4), (off + 3.6, -3.4)
        place(ax, *dem, 'DemandesEnAttente', 1, 'above')
        place(ax, *pl, 'PlacesDisponibles', nb, 'below')
        trans(ax, *tc, 'Confirmer', ok_c, side='right')
        trans(ax, *tr, 'Rejeter', ok_r, side='right')
        parc(ax, dem, tc, True); parc(ax, pl, tc, True)
        parc(ax, dem, tr, True, rad=0.35)
        parc(ax, pl, tr, True, inhibitor=True)
        txt(ax, off + 3.2, 1.45, title, fs=9.6, weight='bold', color=TEAL)
        txt(ax, off + 3.2, -4.75, 'Confirmer : franchissable' if nb else 'Rejeter : franchissable (place vide)',
            fs=8.8, color=GREEN if nb else RED, weight='bold')
    txt(ax, 9.8, -5.35, 'Arc rouge terminé par un cercle = arc inhibiteur : teste l\'absence de jetons, ne consomme rien.',
        fs=8.2, color=GREY, style='italic')
    save(fig, 'methodes-formelles', 'petri-arc-inhibiteur.png')


# =================================================================== DEV MOBILE
def fig_mobile_approches():
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    pts = [('Natif\n(Kotlin, Java, Swift)', 1.7, 8.7, NAVY, 1900), ('Natif généré\n(Flutter, React Native, Xamarin)', 7.0, 7.3, TEAL, 2200),
           ('Hybride\n(Cordova)', 7.6, 4.6, AMBER, 1700), ('Web mobile\n(HTML, CSS, JS)', 8.9, 2.5, GREY, 1500)]
    for lab, x, y, c, sz in pts:
        ax.scatter([x], [y], s=sz, color=c, alpha=0.88, zorder=3, edgecolor='white', linewidth=2)
        ax.text(x, y - 1.05, lab, ha='center', va='top', fontsize=8.6, color=NAVY, fontweight='bold', linespacing=1.2)
    ax.annotate('', xy=(9.8, 0.3), xytext=(0.3, 0.3), arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.6))
    ax.annotate('', xy=(0.3, 9.8), xytext=(0.3, 0.3), arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.6))
    ax.set_xlabel('Réutilisation du code entre systèmes (un seul code)  →', fontsize=9, color=NAVY, fontweight='bold')
    ax.set_ylabel('Performance et accès aux fonctions natives  →', fontsize=9, color=NAVY, fontweight='bold')
    ax.text(5, 9.9, 'Positions qualitatives', ha='center', fontsize=8.2, color=GREY, style='italic')
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    save(fig, 'dev-mobile', 'mobile-approches.png')


def fig_mobile_composants():
    fig, ax = canvas(9.2, 5.1, (0, 18.2), (0, 8.4))
    box(ax, 4.7, 3.15, 4.6, 2.1, 'AndroidManifest.xml\nDéclare les composants,\nles permissions et l\'activité\nde lancement', fc=SOFT_AMBER, ec=AMBER, fs=8.6)
    comps = [(0.3, 5.9, 'Activity', 'Écran et interface\nAppCompatActivity  <activity>', NAVY),
             (9.0, 5.9, 'Service', 'Traitement de fond\nsans interface\nService  <service>', TEAL),
             (0.3, 0.5, 'ContentProvider', 'Partage de données\nvia URI  <provider>', GREEN),
             (9.0, 0.5, 'BroadcastReceiver', 'Événements système\nBroadcastReceiver  <receiver>', RED)]
    for x, y, title, sub, c in comps:
        box(ax, x, y, 4.7, 1.9, '', fc=WHITE, ec=c, lw=2)
        txt(ax, x + 2.35, y + 1.38, title, fs=11, weight='bold', color=c)
        txt(ax, x + 2.35, y + 0.65, sub, fs=8.2)
    arrow(ax, (3.0, 5.9), (5.4, 5.1), color=AMBER, ls='--'); arrow(ax, (11.0, 5.9), (8.6, 5.1), color=AMBER, ls='--')
    arrow(ax, (3.0, 2.4), (5.4, 3.3), color=AMBER, ls='--'); arrow(ax, (11.0, 2.4), (8.6, 3.3), color=AMBER, ls='--')
    arrow(ax, (5.0, 6.85), (9.0, 6.85), color=NAVY)
    txt(ax, 7.0, 7.55, 'Intent\n(startService, bindService)', fs=8.2)
    arrow(ax, (1.9, 5.9), (1.9, 2.4), color=NAVY)
    txt(ax, 2.1, 4.15, 'ContentResolver\n+ URI', fs=8, ha='left')
    box(ax, 14.6, 0.8, 3.4, 1.3, 'Système Android\nou autre application', fc=LIGHT, fs=8.2)
    arrow(ax, (14.6, 1.45), (13.7, 1.45), color=RED, lw=1.8)
    txt(ax, 16.3, 2.55, 'diffuse un Intent\n(batterie, SMS, réseau)', fs=8, color=RED)
    save(fig, 'dev-mobile', 'mobile-composants.png')


def fig_mobile_cycle():
    fig, ax = canvas(7.6, 5.6, (0, 12), (0, 9.2))
    nodes = {'onCreate': (6, 8.5), 'onStart': (6, 7.0), 'onResume': (6, 5.5), 'onPause': (6, 3.4), 'onStop': (6, 1.9), 'onDestroy': (6, 0.45),
             'onRestart': (10.2, 4.7)}
    cols = {'onCreate': SOFT_TEAL, 'onStart': SOFT_TEAL, 'onResume': SOFT_GREEN, 'onPause': SOFT_AMBER, 'onStop': SOFT_AMBER,
            'onDestroy': SOFT_RED, 'onRestart': LIGHT}
    for n, (x, y) in nodes.items():
        box(ax, x - 1.15, y - 0.3, 2.3, 0.6, n + '()', fc=cols[n], fs=9.2)
    for a, b in (('onCreate', 'onStart'), ('onStart', 'onResume'), ('onPause', 'onStop'), ('onStop', 'onDestroy')):
        arrow(ax, (6, nodes[a][1] - 0.3), (6, nodes[b][1] + 0.3))
    arrow(ax, (6, 5.2), (6, 3.7))
    txt(ax, 6.2, 4.45, 'Active', fs=8.5, weight='bold', color=GREEN, ha='left')
    arrow(ax, (7.15, 1.9), (10.2, 4.4), rad=0.0)                         # onStop -> onRestart
    arrow(ax, (10.2, 5.0), (7.15, 6.9))                                  # onRestart -> onStart
    arrow(ax, (4.85, 3.4), (4.85, 5.5), rad=-0.5, color=TEAL)            # onPause -> onResume (focus retrouvé)
    txt(ax, 2.9, 4.45, 'retour au\npremier plan', fs=8.2, color=TEAL, ha='center')
    txt(ax, 10.2, 3.95, 'l\'utilisateur\nrevient', fs=8, color=GREY)
    for lab, y0, y1, c in (('visible', 2.3, 7.4, TEAL), ('premier plan, focus', 3.8, 5.9, GREEN)):
        pass
    txt(ax, 0.25, 6.7, 'Visible : de onStart\nà onStop', fs=8.2, ha='left', color=TEAL)
    txt(ax, 0.25, 5.4, 'Premier plan : de\nonResume à onPause', fs=8.2, ha='left', color=GREEN)
    txt(ax, 0.25, 2.5, 'Pause : partiellement\nvisible, sans focus', fs=8.2, ha='left', color='#b45309')
    txt(ax, 0.25, 1.2, 'Arrêt : invisible,\nétat conservé', fs=8.2, ha='left', color='#b45309')
    txt(ax, 8.1, 0.45, 'Destruction :\nlibère base, threads, fichiers', fs=8.2, ha='left', color=RED)
    save(fig, 'dev-mobile', 'mobile-cycle-vie.png')


def fig_mobile_intent():
    fig, ax = canvas(9.4, 4.4, (0, 19.6), (0, 8.8))
    txt(ax, 4.2, 8.35, 'Intent explicite : la cible est nommée', fs=10, weight='bold', color=TEAL)
    box(ax, 0.2, 4.4, 3.2, 1.3, 'MainActivity', fc=SOFT_TEAL)
    box(ax, 5.2, 4.4, 3.2, 1.3, 'ProfileActivity', fc=SOFT_TEAL)
    arrow(ax, (3.4, 5.05), (5.2, 5.05), lw=2)
    txt(ax, 4.3, 5.55, 'Intent', fs=8.5, weight='bold')
    box(ax, 1.5, 2.2, 6.0, 1.45, 'putExtra("EXTRA_NOM", "Sana")\ngetStringExtra("EXTRA_NOM")', fc=WHITE, fs=8.2, weight='normal', ec=GREY, ls='--')
    arrow(ax, (4.3, 4.4), (4.5, 3.7), color=GREY, ls='--')
    txt(ax, 4.5, 1.4, 'même clé, type compatible', fs=8.2, color=GREY, style='italic')
    ax.plot([9.3, 9.3], [0.6, 8.2], color=LIGHT, lw=1.5)
    txt(ax, 14.5, 8.35, "Intent implicite : l'action est décrite", fs=10, weight='bold', color=AMBER)
    box(ax, 9.8, 4.4, 2.4, 1.3, 'Activity', fc=SOFT_AMBER, ec=AMBER)
    box(ax, 14.0, 4.4, 2.3, 1.3, 'Système\nAndroid', fc=WHITE, ec=NAVY, fs=8.8)
    arrow(ax, (12.2, 5.05), (14.0, 5.05), lw=2)
    txt(ax, 13.1, 5.75, 'ACTION_VIEW + Uri', fs=7.6, weight='bold')
    for i, lab in enumerate(('Navigateur', 'Cartes', 'Autre appli')):
        y = 7.0 - i * 1.95
        box(ax, 17.1, y - 0.35, 2.3, 0.7, lab, fc=WHITE, ec=GREEN, fs=8, weight='normal')
        arrow(ax, (16.3, 5.05), (17.1, y), color=GREEN, lw=1.1, ms=8)
    box(ax, 9.8, 1.4, 6.5, 1.4, 'resolveActivity() != null ?\nsinon ActivityNotFoundException', fc=WHITE, ec=RED, fs=8.2, weight='normal')
    save(fig, 'dev-mobile', 'mobile-intent.png')


def fig_mobile_layouts():
    fig, axes = plt.subplots(2, 3, figsize=(8.2, 5.2))
    names = ['LinearLayout', 'GridLayout', 'TableLayout', 'RelativeLayout', 'FrameLayout', 'ConstraintLayout']
    for ax, name in zip(axes.flat, names):
        ax.set_xlim(0, 10); ax.set_ylim(0, 12); ax.set_aspect('equal'); ax.axis('off')
        ax.set_title(name, fontsize=9.5, color=NAVY, fontweight='bold', pad=4)
        ax.add_patch(FancyBboxPatch((0.3, 0.3), 9.4, 11.2, boxstyle='round,pad=0,rounding_size=0.5', fc=WHITE, ec=NAVY, lw=1.6))
        item = dict(fc=SOFT_TEAL, ec=TEAL, lw=1.2)
        def r(x, y, w, h, t='', fc=SOFT_TEAL, ec=TEAL, fs=7):
            ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.25', fc=fc, ec=ec, lw=1.2))
            if t: ax.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=fs, color=NAVY)
        if name == 'LinearLayout':
            for i, t in enumerate(('TextView', 'EditText', 'Button')):
                r(1, 8.6 - i * 3.1, 8, 2.4, t)
            ax.text(5, 0.9, 'vertical', ha='center', fontsize=7.5, color=GREY, style='italic')
        elif name == 'GridLayout':
            for i in range(3):
                for j in range(2):
                    if i == 2:
                        continue
                    r(1 + j * 4.1, 8.4 - i * 3.0, 3.9, 2.5, '%d,%d' % (i, j))
            r(1, 2.4, 8, 2.5, 'columnSpan = 2', fc=SOFT_AMBER, ec=AMBER)
        elif name == 'TableLayout':
            for i, (a, b) in enumerate((('Nom', 'champ'), ('Prénom', 'champ'), ('Email', 'champ'))):
                r(1, 8.8 - i * 3.0, 2.6, 2.3, a)
                r(3.9, 8.8 - i * 3.0, 5.1, 2.3, b)
            ax.text(5, 0.95, 'TableRow, stretchColumns', ha='center', fontsize=7.2, color=GREY, style='italic')
        elif name == 'RelativeLayout':
            r(3.1, 9.2, 3.8, 1.8, 'Titre')
            r(1, 6.4, 8, 1.9, 'Login  (below Titre)')
            r(1, 3.9, 8, 1.9, 'Password  (below Login)')
            r(3.1, 0.8, 3.8, 1.9, 'alignParentBottom', fc=SOFT_AMBER, ec=AMBER, fs=6.2)
        elif name == 'FrameLayout':
            r(1, 1.5, 8, 9, 'ImageView', fc=LIGHT, ec=GREY, fs=8)
            r(2.2, 2.2, 5.6, 1.8, 'TextView au-dessus', fc=SOFT_AMBER, ec=AMBER, fs=6.8)
            r(5.8, 8.0, 3.2, 1.8, 'badge', fc=SOFT_RED, ec=RED, fs=7)
        else:
            r(3.2, 4.6, 3.6, 2.6, 'Button', fc=SOFT_TEAL)
            for p, q in (((5, 7.2), (5, 11.5)), ((5, 4.6), (5, 0.3)), ((3.2, 5.9), (0.3, 5.9)), ((6.8, 5.9), (9.7, 5.9))):
                ax.annotate('', xy=q, xytext=p, arrowprops=dict(arrowstyle='<->', color=AMBER, lw=1.3))
            ax.text(5, 10.2, 'Top_toTopOf', ha='center', fontsize=6.3, color='#b45309', bbox=dict(fc='white', ec='none', pad=0.5))
    fig.tight_layout(pad=0.8)
    save(fig, 'dev-mobile', 'mobile-layouts.png')


# =================================================================== IOT
def fig_iot_couches():
    fig, ax = canvas(8.6, 5.0, (0, 17.6), (0, 10.2))
    txt(ax, 2.4, 9.85, '3 couches', fs=10.5, weight='bold', color=TEAL)
    txt(ax, 9.6, 9.85, '5 couches', fs=10.5, weight='bold', color=TEAL)
    three = [('Application', 5.6, 4.0, SOFT_AMBER), ('Réseau', 3.0, 2.2, SOFT_TEAL), ('Perception', 0.4, 2.2, SOFT_GREEN)]
    for t, y, h, c in three:
        box(ax, 0.3, y, 4.2, h if h != 4.0 else 4.0, t, fc=c, fs=9.5)
    five = [('Métier  (décision, valeur)', 8.2, SOFT_RED), ('Application  (service, tableau de bord)', 6.4, SOFT_AMBER), ('Traitement  (stockage, analyse)', 4.6, SOFT_AMBER),
            ('Transport  (réseau, passerelle)', 2.8, SOFT_TEAL), ('Perception  (capteurs, actionneurs)', 1.0, SOFT_GREEN)]
    for t, y, c in five:
        box(ax, 5.8, y, 7.3, 1.45, t, fc=c, fs=8.6)
    for y0, y1 in ((5.6, 9.6),):
        pass
    arrow(ax, (14.0, 1.2), (14.0, 9.4), color=TEAL, lw=2.2, ms=16)
    arrow(ax, (14.9, 9.4), (14.9, 1.2), color=AMBER, lw=2.2, ms=16)
    txt(ax, 14.45, 0.45, 'données montantes', fs=7.8, color=TEAL, weight='bold')
    txt(ax, 16.3, 5.3, 'commandes\ndescendantes', fs=7.8, color='#b45309', weight='bold', rotation=90)
    txt(ax, 2.4, 0.05, 'Perception → Réseau → Application', fs=7.6, color=GREY, style='italic')
    save(fig, 'iot', 'iot-couches.png')


def fig_iot_edge_fog_cloud():
    fig, ax = canvas(8.4, 4.3, (0, 17), (0, 8.6))
    tiers = [('Edge', 'objets, capteurs,\nmicrocontrôleur', 'Caméra qui détecte,\narrêt d\'urgence', 0.3, SOFT_GREEN, GREEN),
             ('Fog', 'passerelle,\nserveur local', 'Agrégation d\'un bâtiment,\nrègles, tampon hors ligne', 5.9, SOFT_TEAL, TEAL),
             ('Cloud', 'centre de données\ndistant', 'Historique, entraînement\nd\'un modèle d\'IA', 11.5, SOFT_AMBER, AMBER)]
    for name, what, ex, x, fc, ec in tiers:
        box(ax, x, 1.8, 5.2, 4.7, '', fc=fc, ec=ec, lw=2)
        txt(ax, x + 2.6, 5.7, name, fs=13, weight='bold', color=ec)
        txt(ax, x + 2.6, 4.4, what, fs=8.8)
        txt(ax, x + 2.6, 2.75, ex, fs=8, style='italic', color=GREY)
    arrow(ax, (5.5, 4.1), (5.9, 4.1), lw=1.8); arrow(ax, (11.1, 4.1), (11.5, 4.1), lw=1.8)
    arrow(ax, (0.6, 0.9), (16.4, 0.9), color=NAVY, lw=1.6)
    txt(ax, 8.5, 0.3, 'plus on monte : plus de puissance, vue globale, latence plus élevée', fs=8.6, color=NAVY, weight='bold')
    arrow(ax, (16.4, 7.5), (0.6, 7.5), color=GREEN, lw=1.6)
    txt(ax, 8.5, 8.1, 'plus on descend : réponse rapide, données locales, peu de bande passante', fs=8.6, color=GREEN, weight='bold')
    save(fig, 'iot', 'iot-edge-fog-cloud.png')


def fig_iot_connectivite():
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    fam = [('Filaire\n(Ethernet)', 1.0, 4.7, GREY, 380), ('Courte portée\n(Wi-Fi, BLE, Zigbee)', 2.0, 3.3, TEAL, 560), ('LPWAN\n(LoRaWAN, Sigfox)', 4.6, 0.9, GREEN, 520),
           ('Cellulaire\n(NB-IoT, 4G, 5G)', 4.0, 3.9, AMBER, 700), ('Satellite', 5.3, 2.6, RED, 560)]
    for lab, x, y, c, s in fam:
        ax.scatter([x], [y], s=s, color=c, alpha=0.88, edgecolor='white', linewidth=2, zorder=3)
        ax.text(x, y - 0.55, lab, ha='center', va='top', fontsize=8, color=NAVY, fontweight='bold', linespacing=1.15)
    ax.set_xlim(0.2, 6.2); ax.set_ylim(-0.6, 5.7)
    ax.set_xlabel('Portée  →', fontsize=9, color=NAVY, fontweight='bold')
    ax.set_ylabel('Débit  →', fontsize=9, color=NAVY, fontweight='bold')
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.3, 5.45, 'Taille du cercle = consommation d\'énergie (qualitatif)', fontsize=8, color=GREY, style='italic')
    ax.text(5.9, -0.45, 'LPWAN : grande portée et faible énergie, mais faible débit', fontsize=8, color=GREEN, fontweight='bold', ha='right')
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(GREY)
    save(fig, 'iot', 'iot-connectivite.png')


def fig_iot_noeud():
    fig, ax = canvas(8.8, 2.9, (0, 18), (0, 5.9))
    blocks = [('Capteur', SOFT_GREEN), ('ADC', SOFT_TEAL), ('Microcontrôleur\n(ESP32)', SOFT_AMBER), ('Connectivité\n(Wi-Fi, BLE,\nLoRa)', SOFT_TEAL),
              ('Passerelle', LIGHT), ('Cloud', SOFT_AMBER)]
    x = 0.2
    for i, (t, c) in enumerate(blocks):
        box(ax, x, 2.5, 2.6, 1.8, t, fc=c, fs=7.2)
        if i < len(blocks) - 1:
            arrow(ax, (x + 2.6, 3.4), (x + 3.0, 3.4), lw=1.6)
        x += 3.0
    box(ax, 6.2, 0.2, 5.6, 1.1, 'Alimentation : batterie, secteur ou énergie récupérée', fc=WHITE, ec=GREY, fs=8.2, weight='normal')
    arrow(ax, (9.0, 1.3), (9.0, 2.5), color=GREY, ls='--')
    box(ax, 6.2, 4.7, 5.6, 1.0, 'Actionneur (relais, moteur, LED) commandé par le MCU', fc=WHITE, ec=GREY, fs=8.2, weight='normal')
    arrow(ax, (9.0, 4.7), (9.0, 4.3), color=GREY, ls='--')
    save(fig, 'iot', 'iot-noeud.png')


# =================================================================== EMBEDDED
def fig_embedded_tp3():
    fig, ax = canvas(10.6, 4.9, (0, 22.8), (0, 9.5))
    BW, BH, GAP = 3.3, 1.7, 0.5
    def row(y, label, items):
        txt(ax, 0.1, y + BH + 0.35, label, fs=9, weight='bold', color=TEAL, ha='left')
        for k, (t, c) in enumerate(items):
            x = 0.2 + k * (BW + GAP)
            box(ax, x, y, BW, BH, t, fc=c, fs=7.3)
            if k < len(items) - 1:
                arrow(ax, (x + BW, y + BH / 2), (x + BW + GAP, y + BH / 2), lw=1.5, ms=10)
    row(6.9, 'Réception USB (port COM virtuel)', [('PC\nterminal série', LIGHT), ('CDC_Receive_FS\n(pilote USB)', SOFT_AMBER),
         ('USB_CDC_\nRxCallback\nrange les octets', SOFT_AMBER), ('Tampon circulaire\n128 octets\nhead, tail', SOFT_GREEN),
         ('Boucle principale\nassemble une ligne', SOFT_TEAL), ('usb_println\n« Received: … »', SOFT_TEAL)])
    row(3.6, 'Bouton PA0 (EXTI0, front descendant)', [('Appui\nPA0 vers GND', LIGHT), ('HAL_GPIO_EXTI_\nCallback\nanti-rebond 200 ms', SOFT_AMBER),
         ('button_event\n(volatile bool)', SOFT_GREEN), ('Boucle principale\nbascule la LED', SOFT_TEAL), ('usb_println\n« Button pressed »', SOFT_TEAL)])
    row(0.3, 'Timer TIM4 (1 Hz)', [('TIM4\ndébordement', LIGHT), ('HAL_TIM_Period\nElapsedCallback', SOFT_AMBER), ('LED PC13\nbascule\n(active à LOW)', WHITE)])
    for (t, c, x, y) in (('ISR : courte', SOFT_AMBER, 12.6, 1.55), ('données partagées', SOFT_GREEN, 12.6, 0.95), ('boucle principale', SOFT_TEAL, 12.6, 0.35)):
        box(ax, x, y, 0.5, 0.4, '', fc=c, lw=1.0)
        txt(ax, x + 0.7, y + 0.2, t, fs=7.8, ha='left')
    save(fig, 'embedded', 'embedded-tp3-chaine.png')


def fig_embedded_pull():
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.7))
    for ax, kind in zip(axes, ('up', 'down')):
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.set_aspect('equal'); ax.axis('off')
        top, bot = ('VCC', 'GND') if kind == 'up' else ('GND', 'VCC')
        topc = RED if kind == 'up' else NAVY
        ax.text(5, 9.6, 'Pull-up (INPUT_PULLUP)' if kind == 'up' else 'Pull-down (INPUT_PULLDOWN)', ha='center', fontsize=9.4, color=TEAL, fontweight='bold')
        ax.text(1.5, 8.4, 'VCC' if kind == 'up' else 'GND', fontsize=9, color=NAVY, fontweight='bold', ha='center')
        ax.plot([1.5, 1.5], [8.0, 6.7], color=NAVY, lw=1.6)
        ax.add_patch(Rectangle((1.0, 4.9), 1.0, 1.8, fc=WHITE, ec=NAVY, lw=1.6))
        ax.text(2.35, 5.8, 'R', fontsize=9, color=NAVY, va='center')
        ax.plot([1.5, 1.5], [4.9, 3.7], color=NAVY, lw=1.6)
        ax.plot([1.5, 6.0], [3.7, 3.7], color=NAVY, lw=1.6)
        ax.add_patch(Rectangle((6.0, 3.1), 2.4, 1.2, fc=SOFT_TEAL, ec=NAVY, lw=1.6))
        ax.text(7.2, 3.7, 'GPIO', ha='center', va='center', fontsize=9, color=NAVY, fontweight='bold')
        ax.plot([1.5, 1.5], [3.7, 1.9], color=NAVY, lw=1.6)
        ax.plot([0.9, 1.5], [1.9, 1.3], color=NAVY, lw=2.0)
        ax.plot([1.5, 1.5], [1.3, 0.7], color=NAVY, lw=1.6)
        ax.text(2.35, 1.5, 'bouton', fontsize=8, color=GREY)
        ax.text(1.5, 0.15, 'GND' if kind == 'up' else 'VCC', fontsize=9, color=NAVY, fontweight='bold', ha='center')
        lvl_open, lvl_press = ('HIGH', 'LOW') if kind == 'up' else ('LOW', 'HIGH')
        ax.text(5.0, 7.2, 'relâché : %s' % lvl_open, fontsize=9, color=GREEN, fontweight='bold')
        ax.text(5.0, 6.0, 'appuyé : %s' % lvl_press, fontsize=9, color=RED, fontweight='bold')
        ax.text(5.0, 8.4, 'état actif : %s' % lvl_press, fontsize=8.6, color=NAVY, style='italic')
    fig.tight_layout(pad=0.6)
    save(fig, 'embedded', 'embedded-pull.png')


def fig_embedded_pwm():
    import numpy as np
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 4.6), sharex=True)
    for ax, duty in zip(axes, (0.25, 0.5, 0.75)):
        t = np.linspace(0, 4, 800)
        y = ((t % 1) < duty).astype(float)
        ax.plot(t, y, color=TEAL, lw=2.2, drawstyle='steps-post')
        ax.axhline(duty, color=AMBER, lw=1.4, ls='--')
        ax.text(4.03, duty, 'moyenne = %d %% de Vcc' % (duty * 100), va='center', fontsize=8, color='#b45309', fontweight='bold')
        ax.set_ylim(-0.15, 1.2); ax.set_yticks([0, 1]); ax.set_yticklabels(['0', 'Vcc'], fontsize=8)
        ax.set_ylabel('rapport\ncyclique %d %%' % (duty * 100), fontsize=8.4, color=NAVY, fontweight='bold', rotation=0, labelpad=38, va='center')
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
    axes[-1].set_xticks([0, 1, 2, 3, 4]); axes[-1].set_xticklabels(['0', 'T', '2T', '3T', '4T'], fontsize=8)
    axes[0].set_title('PWM : la fréquence est constante, le rapport cyclique règle la puissance moyenne', fontsize=9.2, color=TEAL, fontweight='bold')
    fig.subplots_adjust(left=0.2, right=0.78, hspace=0.35)
    save(fig, 'embedded', 'embedded-pwm.png')


# =================================================================== GAME DEV
def fig_game_boucle():
    fig, ax = canvas(7.6, 3.3, (0, 15.5), (0, 6.6))
    steps = [('1. Lire les entrées', 'keydown, keyup,\nsouris', SOFT_TEAL), ('2. Mettre à jour', 'positions, vitesses,\ncollisions, score', SOFT_AMBER),
             ('3. Effacer', 'clearRect', SOFT_RED), ('4. Dessiner', 'tuiles, sprites,\ninterface', SOFT_GREEN)]
    x = 0.2
    for i, (t, sub, c) in enumerate(steps):
        box(ax, x, 3.0, 3.4, 2.2, '', fc=c, fs=9)
        txt(ax, x + 1.7, 4.55, t, fs=9, weight='bold')
        txt(ax, x + 1.7, 3.65, sub, fs=8)
        if i < 3:
            arrow(ax, (x + 3.4, 4.1), (x + 3.85, 4.1), lw=1.8)
        x += 3.85
    arrow(ax, (14.8, 3.0), (1.9, 3.0), rad=-0.0, color=GREY, ls='--')
    ax.plot([14.8, 14.8], [3.0, 2.2], color=GREY, lw=1.5, ls='--'); ax.plot([1.9, 1.9], [3.0, 2.2], color=GREY, lw=1.5, ls='--')
    ax.plot([1.9, 14.8], [2.2, 2.2], color=GREY, lw=1.5, ls='--')
    txt(ax, 8.4, 1.5, 'requestAnimationFrame(boucle)  :  prochaine image, environ 60 fois par seconde', fs=8.8, color=NAVY, weight='bold')
    txt(ax, 8.4, 0.6, 'Un simple « for » qui dessine toutes les images d\'un coup ne donne pas une animation', fs=8, color=GREY, style='italic')
    save(fig, 'game-dev', 'game-boucle.png')


def fig_game_spritesheet():
    fig, ax = canvas(8.0, 3.6, (-0.6, 17.4), (-0.6, 7.8))
    FW, FH = 3.0, 3.0
    for r_ in range(2):
        for c_ in range(4):
            sel = (r_ == 1 and c_ == 2)
            ax.add_patch(Rectangle((c_ * FW, 3.6 - r_ * FH + 0.0), FW, FH, fc=SOFT_AMBER if sel else WHITE, ec=NAVY, lw=1.4))
            txt(ax, c_ * FW + FW / 2, 3.6 - r_ * FH + FH / 2, '(%d, %d)' % (c_, r_), fs=8.5, color=NAVY if not sel else '#b45309', weight='bold' if sel else 'normal')
    txt(ax, 6.0, 7.1, 'Feuille de sprites : colonne = image, ligne = direction', fs=9.2, weight='bold', color=TEAL)
    arrow(ax, (7.5, 2.2), (13.4, 3.4), color=AMBER, lw=1.8)
    ax.add_patch(Rectangle((13.2, 2.2), 3.0, 3.0, fc=SOFT_AMBER, ec=AMBER, lw=2))
    txt(ax, 14.7, 3.7, 'canvas\n(x, y)', fs=8.5, color='#b45309', weight='bold')
    txt(ax, 6.0, -0.35, 'ctx.drawImage(img, col × FW, ligne × FH, FW, FH, x, y, FW, FH)    et    col = (col + 1) % nbImages', fs=8, color=NAVY)
    save(fig, 'game-dev', 'game-spritesheet.png')


def fig_game_iso():
    fig, ax = canvas(8.8, 4.4, (-6.5, 19.0), (-1.2, 8.4))
    w, h = 2.2, 1.1
    def tile(i, j, c):
        cx = (i - j) * w / 2 + 3.2
        cy = 6.0 - (i + j) * h / 2
        pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
        ax.add_patch(Polygon(pts, closed=True, fc=c, ec=NAVY, lw=1.3))
        txt(ax, cx, cy, '%d,%d' % (i, j), fs=7.8, weight='bold')
    for i in range(4):
        for j in range(4):
            tile(i, j, SOFT_AMBER if (i, j) == (2, 1) else (SOFT_TEAL if (i + j) % 2 == 0 else WHITE))
    txt(ax, 3.2, 7.6, 'Grille (i, j) : i = ligne, j = colonne', fs=9, weight='bold', color=TEAL)
    box(ax, 9.2, 1.2, 9.4, 5.5, '', fc=PALE, ec=NAVY)
    txt(ax, 13.9, 6.1, 'Projection isométrique', fs=9.4, weight='bold', color=TEAL)
    txt(ax, 9.7, 5.0, 'x = (i − j) × w / 2 + offsetX', fs=9, ha='left', weight='bold')
    txt(ax, 9.7, 4.1, 'y = (i + j) × h / 2', fs=9, ha='left', weight='bold')
    txt(ax, 9.7, 3.2, 'TP : w = 32 px, h = 16 px (moitié de 32)', fs=8.2, ha='left', color=GREY)
    txt(ax, 9.7, 2.1, 'Exemple i=2, j=1, w=64, h=32 :\n(32, 48) avant les décalages', fs=8.2, ha='left', color=NAVY)
    txt(ax, -3.2, 3.3, "on dessine\nde l'arrière\nvers l'avant :\ni puis j", fs=8.5, color=GREY, style='italic')
    save(fig, 'game-dev', 'game-isometrique.png')


def fig_game_box2d():
    fig, ax = canvas(8.8, 4.7, (0, 18.4), (-0.9, 9.6))
    levels = [('World', 'gravité, simulation, collisions', 6.7, SOFT_AMBER), ('Body', 'position, angle, vitesse ; static, dynamic, kinematic', 4.5, SOFT_TEAL),
              ('Fixture', 'densité, friction, restitution', 2.3, SOFT_GREEN), ('Shape', 'cercle, polygone ; SetAsBox(demi-largeur, demi-hauteur)', 0.2, LIGHT)]
    for n, d, y, c in levels:
        box(ax, 0.2, y, 9.4, 1.7, '', fc=c)
        txt(ax, 0.6, y + 1.15, n, fs=11, weight='bold', ha='left')
        txt(ax, 0.6, y + 0.5, d, fs=7.8, ha='left')
    for y in (6.7, 4.5, 2.3):
        arrow(ax, (4.9, y), (4.9, y - 0.5), lw=1.6)
    txt(ax, 14.0, 9.0, 'Une étape de simulation', fs=10, weight='bold', color=TEAL)
    steps = ['1. appliquer les forces', '2. détecter les collisions', '3. résoudre les collisions', '4. mettre à jour position,\nvitesse et rotation']
    for i, st in enumerate(steps):
        box(ax, 10.8, 6.4 - i * 1.9, 6.4, 1.3, st, fc=WHITE, ec=TEAL, fs=8.6, weight='normal')
        if i < 3:
            arrow(ax, (14.0, 6.4 - i * 1.9), (14.0, 6.4 - i * 1.9 - 0.6), lw=1.5)
    txt(ax, 14.0, -0.35, 'world.Step(1/60, 10, 10)    scale = 20 ou 30 px par mètre', fs=8, color=GREY, style='italic')
    save(fig, 'game-dev', 'game-box2d.png')


# =================================================================== DEVOPS
def fig_devops_hyperviseurs():
    fig, ax = canvas(8.8, 4.7, (0, 18), (0, 9.4))
    cols = [('Hyperviseur de type 1\n(bare metal)', 0.2, [('Matériel', LIGHT), ('Hyperviseur', SOFT_AMBER), ('VM  |  VM  |  VM', SOFT_TEAL)]),
            ('Hyperviseur de type 2\n(hébergé)', 6.1, [('Matériel', LIGHT), ('Système hôte', LIGHT), ('Hyperviseur', SOFT_AMBER), ('VM  |  VM', SOFT_TEAL)]),
            ('Conteneurs', 12.0, [('Matériel', LIGHT), ('Système hôte (noyau partagé)', LIGHT), ('Moteur de conteneurs', SOFT_AMBER), ('App  |  App  |  App', SOFT_GREEN)])]
    for title, x, layers in cols:
        txt(ax, x + 2.8, 8.7, title, fs=9.2, weight='bold', color=TEAL)
        for k, (t, c) in enumerate(layers):
            box(ax, x, 0.4 + k * 1.75, 5.6, 1.5, t, fc=c, fs=8.4)
    txt(ax, 3.0, 0.0, 'accès direct au matériel', fs=7.8, color=GREY, style='italic')
    txt(ax, 8.9, 0.0, 'plus de couches', fs=7.8, color=GREY, style='italic')
    txt(ax, 14.8, 0.0, 'plus léger : pas de système invité', fs=7.8, color=GREY, style='italic')
    save(fig, 'devops', 'devops-hyperviseurs.png')


def fig_devops_services():
    fig, ax = canvas(8.8, 4.8, (0, 18.4), (0, 9.9))
    layers = ['Applications', 'Données', 'Runtime', 'Middleware', 'Système d\'exploitation', 'Virtualisation', 'Serveurs', 'Stockage', 'Réseau']
    models = [('Sur site', 0.4, 9), ('IaaS', 4.9, 5), ('PaaS', 9.4, 2), ('SaaS', 13.9, 0)]
    for name, x, client_layers in models:
        txt(ax, x + 1.9, 9.45, name, fs=10.5, weight='bold', color=TEAL)
        for k, l in enumerate(layers):
            y = 8.3 - k * 0.92
            client = k < client_layers
            box(ax, x, y - 0.38, 3.8, 0.8, l, fc=SOFT_AMBER if client else SOFT_TEAL, ec=AMBER if client else TEAL, fs=7.3, weight='normal', lw=1.1)
    box(ax, 0.4, 0.05, 1.0, 0.45, '', fc=SOFT_AMBER, ec=AMBER, lw=1.1)
    txt(ax, 1.55, 0.28, 'géré par le client', fs=8, ha='left')
    box(ax, 7.2, 0.05, 1.0, 0.45, '', fc=SOFT_TEAL, ec=TEAL, lw=1.1)
    txt(ax, 8.35, 0.28, 'géré par le fournisseur', fs=8, ha='left')
    save(fig, 'devops', 'devops-modeles-service.png')


def main():
    print('Drawing figures...')
    for f in (fig_petri_franchissement, fig_petri_graphe, fig_petri_inhibiteur,
              fig_mobile_approches, fig_mobile_composants, fig_mobile_cycle, fig_mobile_intent, fig_mobile_layouts,
              fig_iot_couches, fig_iot_edge_fog_cloud, fig_iot_connectivite, fig_iot_noeud,
              fig_embedded_tp3, fig_embedded_pull, fig_embedded_pwm,
              fig_game_boucle, fig_game_spritesheet, fig_game_iso, fig_game_box2d,
              fig_devops_hyperviseurs, fig_devops_services):
        f()
    print('done')


if __name__ == '__main__':
    main()
