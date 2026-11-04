"""Construit RAPPORT.pdf a partir des resultats reels des outils.

Usage (depuis la racine du projet) :
    python3 rapport/build.py

Lit les sorties NuSMV et PRISM, relance les tests Java, insere les figures SVG
et les sources en annexe, puis imprime le tout en PDF avec Chrome.
"""
import html
import textwrap
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "rapport" / "figures"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def svg(name):
    s = (FIG / name).read_text(encoding="utf-8")
    s = re.sub(r"<\?xml[^>]*\?>", "", s)
    # Taille pilotee par le CSS : on retire la taille fixe de la racine <svg>
    root = re.search(r"<svg[^>]*>", s).group(0)
    return s.replace(root, re.sub(r'\s(width|height|style|preserveAspectRatio)="[^"]*"', "", root), 1)


def code(text, lang):
    """Bloc de code avec commentaires attenues."""
    out = []
    comment = {"java": "//", "smv": "--", "prism": "//"}[lang]
    for line in text.rstrip("\n").split("\n"):
        e = html.escape(line)
        i = e.find(comment)
        if lang == "java" and e.lstrip().startswith(("/**", "*", "*/")):
            out.append(f'<span class="c">{e}</span>')
        elif i >= 0:
            out.append(e[:i] + f'<span class="c">{e[i:]}</span>')
        else:
            out.append(e)
    return f'<pre class="code"><code>' + "\n".join(out) + "</code></pre>"


# ---------- Resultats reels ----------
def java_results():
    out_dir = tempfile.mkdtemp()
    subprocess.run(["javac", "-d", out_dir, *map(str, (ROOT / "1-java/src").glob("*.java"))], check=True)
    out = subprocess.run(["java", "-cp", out_dir, "Main"], capture_output=True, text=True, check=True).stdout
    tests = re.findall(r"\[(OK|ECHEC)\]\s+(.*)", out)
    summary = re.search(r"(\d+)/(\d+) tests reussis", out).group(0)
    return tests, summary


def nusmv_results(rel):
    return [(m.group(1).strip(), m.group(2) == "true")
            for m in re.finditer(r"^-- specification (.*?)\s+is (true|false)", read(rel), re.M)]


def prism_results():
    lines = read("5-prism/resultats.txt").splitlines()
    i = lines.index("T\tResult") + 1
    rows = []
    while i < len(lines) and lines[i][:1].isdigit():
        t, v = lines[i].split("\t"); rows.append((int(t), float(v))); i += 1
    after = "\n".join(lines[i:])
    conf = float(re.search(r'F "confirmee" \]:\nResult\n([\d.]+)', after).group(1))
    ref = float(re.search(r'F "refusee" \]:\nResult\n([\d.]+)', after).group(1))
    return rows, conf, ref


def fr(x, n=3):
    return f"{x:.{n}f}".replace(".", ",")


tests, java_summary = java_results()
smv_ok = nusmv_results("4-nusmv/resultat_correcte.txt")
smv_bug = nusmv_results("4-nusmv/resultat_bug.txt")
prism_rows, p_conf, p_ref = prism_results()
p3 = dict(prism_rows)[3]

# Identifiants des proprietes, dans l'ordre d'affichage de NuSMV (LTL en dernier)
OK_IDS = ["S1", "S2", "S3", "S4", "S4", "S5", "V1", "V1", "V2", "V2", "V4", "V3"]
BUG_IDS = ["S1", "S2", "S3", "V1", "V3"]

tick = '<span class="ok">vraie</span>'
cross = '<span class="ko">fausse</span>'

bug_verdict = dict(smv_bug)
rows_smv = "".join(
    f"<tr><td class='id'>{pid}</td><td><code>{html.escape(f)}</code></td><td>{tick if v else cross}</td>"
    f"<td>{(tick if bug_verdict[f] else cross) if f in bug_verdict else '<span class=sub>non vérifiée</span>'}</td></tr>"
    for pid, (f, v) in zip(OK_IDS, smv_ok))
rows_ok = "".join(f"<tr><td class='id'>{pid}</td><td><code>{html.escape(f)}</code></td><td>{tick if v else cross}</td></tr>"
                  for pid, (f, v) in zip(OK_IDS, smv_ok))
rows_bug = "".join(f"<tr><td class='id'>{pid}</td><td><code>{html.escape(f)}</code></td><td>{tick if v else cross}</td></tr>"
                   for pid, (f, v) in zip(BUG_IDS, smv_bug))
ACCENTS = {"confirmees": "confirmées", "confirmee": "confirmée", "refusee": "refusée", "liberee": "libérée",
           "annulee": "annulée", "deja": "déjà", "rejete": "rejeté", "etre": "être", "capacite": "capacité",
           "reserver": "réserver", "pre :": "pré :"}


def accents(t):
    for a, b in ACCENTS.items():
        t = re.sub(rf"\b{re.escape(a)}", b, t)
    return t


def test_label(n):
    n = html.escape(accents(n))
    if " -&gt; " in n:
        nom, res = n.split(" -&gt; ", 1)
        return f"{nom}<br><span class='sub'>{res}</span>"
    return n


rows_java = "".join(f"<tr><td>{test_label(n)}</td><td>{'<span class=ok>réussi</span>' if s == 'OK' else '<span class=ko>échec</span>'}</td></tr>"
                    for s, n in tests)
prism_head = "".join(f"<th>{t}</th>" for t, _ in prism_rows)
prism_vals = "".join(f"<td>{fr(v)}</td>" for _, v in prism_rows)
n_true = sum(v for _, v in smv_ok)

reserver_src = read("1-java/src/SystemeReservation.java")
m = re.search(r"    /\*\*\n     \* Pre  : d != null et d est EN_ATTENTE.*?\n    }\n", reserver_src, re.S)
reserver_excerpt = textwrap.dedent(m.group(0))

# ---------- Document ----------
HTML = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<title>Rapport TD/TP MFGL : réservation de places</title>
<style>
@page {{
  size: A4; margin: 22mm 20mm 24mm 20mm;
  @bottom-left {{ content: "MFGL · Réservation de places"; font: 8.5pt "Helvetica Neue", Helvetica, sans-serif; color: #87867f; }}
  @bottom-right {{ content: counter(page); font: 8.5pt "Helvetica Neue", Helvetica, sans-serif; color: #87867f; }}
}}
@page :first {{ margin: 0; @bottom-left {{ content: none; }} @bottom-right {{ content: none; }} }}
:root {{
  --ink: #141413; --ink2: #3d3d3a; --muted: #87867f; --line: #e8e6dc;
  --paper: #faf9f5; --panel: #f0eee6; --clay: #c96442; --clay-soft: #f5e4dc;
  --green: #4f7a3a; --green-soft: #e3ebd9; --red: #b5452b;
  --serif: "Charter", "Iowan Old Style", Georgia, serif;
  --sans: "Helvetica Neue", Helvetica, Arial, sans-serif;
  --mono: "SF Mono", Menlo, Consolas, monospace;
}}
* {{ box-sizing: border-box; }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ margin: 0; font: 10.6pt/1.58 var(--serif); color: var(--ink2); background: #fff; }}
h1, h2, h3 {{ font-family: var(--serif); color: var(--ink); font-weight: 600; line-height: 1.2; }}
h2 {{ font-size: 19pt; margin: 0 0 4mm; padding-top: 1mm; break-after: avoid; }}
h3 {{ font-size: 12.5pt; margin: 6mm 0 2mm; break-after: avoid; }}
p {{ margin: 0 0 3mm; orphans: 3; widows: 3; }}
li {{ orphans: 2; widows: 2; }}
code {{ font: 8.8pt var(--mono); color: var(--ink); }}
p code, li code, td code {{ background: var(--panel); padding: 0.3mm 1.2mm; border-radius: 1mm; }}
.kicker {{ font: 600 8pt var(--sans); letter-spacing: 0.14em; text-transform: uppercase; color: var(--clay); margin-bottom: 2mm; }}
section {{ margin-top: 13mm; }}
section.page {{ break-before: page; margin-top: 0; }}
.kicker {{ break-after: avoid; }}
table.keep, .two, .keepblock {{ break-inside: avoid; }}

/* Couverture */
.cover {{ height: 297mm; background: var(--paper); padding: 26mm 24mm; display: flex; flex-direction: column; position: relative; overflow: hidden; }}
.cover .inst {{ font: 9pt/1.5 var(--sans); color: var(--muted); display: flex; justify-content: space-between; }}
.cover .mark {{ width: 18mm; height: 18mm; margin-top: 46mm; }}
.cover .course {{ font: 600 9pt var(--sans); letter-spacing: 0.16em; text-transform: uppercase; color: var(--clay); margin-top: 8mm; }}
.cover h1 {{ font-size: 34pt; margin: 4mm 0 6mm; letter-spacing: -0.01em; max-width: 150mm; }}
.cover .lede {{ font-size: 13pt; line-height: 1.5; color: var(--ink2); max-width: 140mm; margin: 0; }}
.cover .meta {{ margin-top: auto; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6mm; border-top: 0.3mm solid var(--ink); padding-top: 5mm; }}
.cover .meta div {{ font: 10.5pt/1.45 var(--serif); color: var(--ink); }}
.cover .meta span {{ display: block; font: 600 7.5pt var(--sans); letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted); margin-bottom: 1mm; }}

/* En bref */
.tiles {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 4mm; margin: 6mm 0 8mm; }}
.tile {{ background: var(--paper); border: 0.25mm solid var(--line); border-radius: 2.5mm; padding: 4mm 4mm 3.5mm; }}
.tile b {{ display: block; font: 600 21pt/1.1 var(--serif); color: var(--ink); }}
.tile span {{ font: 8.5pt/1.35 var(--sans); color: var(--muted); }}
.toc {{ list-style: none; padding: 0; margin: 0; columns: 3; column-gap: 8mm; }}
.toc li {{ font: 10pt/1.8 var(--serif); color: var(--ink); break-inside: avoid; }}
.toc li span {{ font: 600 8pt var(--sans); color: var(--clay); display: inline-block; width: 9mm; }}

/* Tableaux */
table {{ width: 100%; border-collapse: collapse; margin: 2mm 0 5mm; font: 9pt/1.45 var(--sans); }}\ntr {{ break-inside: avoid; }}\n.sub {{ color: var(--muted); font-size: 8pt; font-weight: 400; }}\ntable.smv th:nth-child(3), table.smv th:nth-child(4), table.smv td:nth-child(3), table.smv td:nth-child(4) {{ width: 18%; }}
th {{ text-align: left; font: 600 7.5pt var(--sans); letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); border-bottom: 0.3mm solid var(--ink); padding: 1.6mm 2mm; }}
td {{ border-bottom: 0.2mm solid var(--line); padding: 1.6mm 2mm; vertical-align: top; color: var(--ink2); }}
td.id {{ font-weight: 600; color: var(--clay); white-space: nowrap; }}
table.num th, table.num td {{ text-align: center; }}
.ok {{ color: var(--green); font-weight: 600; }}
.ko {{ color: var(--red); font-weight: 600; }}
tr.hl td {{ background: var(--clay-soft); }}

/* Encadres */
.contract {{ background: var(--paper); border: 0.25mm solid var(--line); border-radius: 2.5mm; padding: 4mm 5mm; margin: 3mm 0 5mm; break-inside: avoid; }}
.contract dt {{ font: 600 7.5pt var(--sans); letter-spacing: 0.12em; text-transform: uppercase; color: var(--clay); margin-top: 3mm; }}
.contract dt:first-child {{ margin-top: 0; }}
.contract dd {{ margin: 1mm 0 0; font: 9.6pt/1.6 var(--mono); color: var(--ink); white-space: pre; }}
.note {{ border-left: 0.8mm solid var(--clay); background: var(--clay-soft); padding: 3mm 4.5mm; border-radius: 0 2mm 2mm 0; margin: 4mm 0; break-inside: avoid; }}
.note b {{ color: var(--ink); }}
.good {{ border-left-color: var(--green); background: var(--green-soft); }}
ul {{ margin: 0 0 3mm; padding-left: 5mm; }}
li {{ margin-bottom: 1mm; }}

/* Figures */
figure {{ margin: 3mm 0 6mm; break-inside: avoid; }}
figure .frame {{ background: var(--paper); border: 0.25mm solid var(--line); border-radius: 2.5mm; padding: 5mm; display: flex; justify-content: center; }}
figure svg {{ max-width: 100%; height: auto; }}
figcaption {{ font: 8.5pt/1.4 var(--sans); color: var(--muted); margin-top: 2mm; }}
figcaption b {{ color: var(--ink); }}
.w-etats svg {{ width: 72mm; }} .w-seq svg {{ width: 94mm; }} .w-petri svg {{ width: 160mm; }}
.w-auto svg {{ width: 100%; }} .w-chart svg {{ width: 150mm; }}

/* Code */
pre.code {{ background: var(--panel); border-radius: 2.5mm; padding: 4mm 5mm; margin: 2mm 0 5mm; font: 7.9pt/1.5 var(--mono); color: var(--ink); white-space: pre-wrap; overflow-wrap: anywhere; }}
pre.code code {{ font: inherit; color: inherit; }}
pre.code .c {{ color: #8a7f72; font-style: italic; }}
.cmd {{ font: 8.6pt var(--mono); background: var(--ink); color: #f0eee6; border-radius: 2mm; padding: 2.5mm 4mm; margin: 2mm 0 4mm; white-space: pre-wrap; }}
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; }}
.annex h3 {{ margin-top: 2mm; }}
.annex pre.code {{ font-size: 6.9pt; }}
section.annex + section.annex {{ margin-top: 6mm; }}
</style></head>
<body>

<!-- ===================== Couverture ===================== -->
<div class="cover">
  <div class="inst"><div>USTHB<br>Faculté d'Informatique<br>Laboratoire MOVEP</div><div style="text-align:right">TD / TP MFGL<br>Ing 5 Soft.Eng<br>Année 2026-2027</div></div>
  <svg class="mark" viewBox="0 0 40 40"><rect width="40" height="40" rx="9" fill="#c96442"/><circle cx="14" cy="20" r="5.5" fill="none" stroke="#faf9f5" stroke-width="2.4"/><rect x="23" y="12" width="4" height="16" fill="#faf9f5"/></svg>
  <div class="course">Méthodes formelles pour le génie logiciel</div>
  <h1>Réservation de places&#8239;: spécifier, vérifier, valider</h1>
  <p class="lede">Spécification formelle, modélisation et vérification d'un système de réservation de places pour un événement de capacité limitée, du contrat Java jusqu'au model checking probabiliste.</p>
  <div class="meta">
    <div><span>Réalisé par</span>Bechar Walid<br>Groupe 2</div>
    <div><span>Encadré par</span>Dr Mekahlia Fatma Zohra</div>
    <div><span>Date</span>Novembre 2026</div>
  </div>
</div>

<!-- ===================== En bref ===================== -->
<section class="page">
  <div class="kicker">Synthèse</div>
  <h2>En bref</h2>
  <p>Le système doit garantir qu'une place n'est jamais attribuée deux fois, même lorsque deux utilisateurs demandent la dernière place au même moment. Nous avons spécifié l'opération de réservation, l'avons implémentée avec des contrats vérifiés, puis modélisée avec cinq outils formels. Le résultat central&#8239;: une réservation <b>non atomique</b> permet la double réservation (NuSMV en donne le contre-exemple), alors que la version <b>atomique</b> satisfait toutes les propriétés.</p>
  <div class="tiles">
    <div class="tile"><b>{java_summary.split()[0]}</b><span>tests Java réussis, contrats respectés</span></div>
    <div class="tile"><b>{n_true}/{len(smv_ok)}</b><span>propriétés CTL/LTL vraies sur le modèle correct</span></div>
    <div class="tile"><b>5 états</b><span>contre-exemple de double réservation (modèle incorrect)</span></div>
    <div class="tile"><b>{fr(p_conf*100, 1)}&#8239;%</b><span>probabilité de confirmation (PRISM)</span></div>
  </div>

  <h3>Correspondance avec le travail demandé</h3>
  <table>
    <tr><th style="width:52%">Travail demandé</th><th>Livrable</th><th>Outil</th><th>Section</th></tr>
    <tr><td>Préconditions, postconditions, invariants</td><td>Contrat de <code>reserver</code></td><td>Notation formelle</td><td>1</td></tr>
    <tr><td>Réservation séquentielle en Java, vérification des conditions</td><td><code>1-java/</code></td><td>Java</td><td>2</td></tr>
    <tr><td>États d'une réservation, transitions autorisées</td><td><code>etats.puml</code>, <code>etats.jff</code></td><td>PlantUML, JFLAP</td><td>3</td></tr>
    <tr><td>Deux utilisateurs demandent la dernière place</td><td><code>concurrence.puml</code></td><td>PlantUML</td><td>4</td></tr>
    <tr><td>Disponibilité, transitions et conflits</td><td><code>reservation.pnml</code></td><td>PIPE</td><td>5</td></tr>
    <tr><td>Propriétés de sûreté et de vivacité, formalisation temporelle</td><td>Formules CTL/LTL</td><td>NuSMV</td><td>6</td></tr>
    <tr><td>Scénario incorrect, vérification, contre-exemples</td><td><code>4-nusmv/</code></td><td>NuSMV</td><td>7</td></tr>
    <tr><td>Probabilités de défaillance ou de retard, confirmation avant échéance</td><td><code>5-prism/</code></td><td>PRISM</td><td>8</td></tr>
  </table>

  <h3>Sommaire</h3>
  <ol class="toc">
    <li><span>0</span>Contexte et hypothèses</li><li><span>1</span>Spécification</li>
    <li><span>2</span>Implémentation Java</li><li><span>3</span>États et transitions</li>
    <li><span>4</span>Scénario concurrent</li><li><span>5</span>Réseau de Petri</li>
    <li><span>6</span>Propriétés temporelles</li><li><span>7</span>Vérification NuSMV</li>
    <li><span>8</span>Modèle probabiliste</li><li><span>9</span>Conclusion</li>
    <li><span>A</span>Annexes&#8239;: sources</li>
  </ol>
</section>

<!-- ===================== 0. Contexte ===================== -->
<section class="page">
  <div class="kicker">Section 0</div>
  <h2>Contexte et hypothèses</h2>
  <p>Un événement dispose d'une capacité <code>N</code> fixée à l'avance. Les utilisateurs soumettent des demandes de réservation&#8239;: si une place est libre, la demande est confirmée, sinon elle est refusée. Deux contraintes doivent toujours tenir&#8239;: le nombre de places disponibles reste cohérent, et aucune place n'est attribuée deux fois. La difficulté apparaît en concurrence, quand deux demandes simultanées visent la dernière place.</p>
  <h3>Hypothèses de modélisation</h3>
  <ul>
    <li><b>Capacité et utilisateurs.</b> Les modèles formels (Petri, NuSMV) utilisent <code>N = 1</code> et deux utilisateurs&#8239;: c'est exactement la situation critique de la dernière place. L'implémentation Java est générale (capacité quelconque).</li>
    <li><b>Annulation.</b> Une demande peut être annulée depuis <i>En attente</i> (l'utilisateur renonce) ou depuis <i>Confirmée</i> (la place est alors libérée). <i>Refusée</i> et <i>Annulée</i> sont des états finaux.</li>
    <li><b>Concurrence.</b> NuSMV modélise un entrelacement&#8239;: à chaque pas, un ordonnanceur choisit l'utilisateur qui agit. Les propriétés de vivacité supposent un ordonnanceur équitable.</li>
    <li><b>Temps.</b> Le modèle PRISM est une chaîne de Markov à temps discret&#8239;: un pas représente une unité de temps.</li>
  </ul>
  <h3>Outils utilisés</h3>
  <table class="keep">
    <tr><th>Outil</th><th>Version</th><th>Usage</th></tr>
    <tr><td>Java (OpenJDK)</td><td>25</td><td>Implémentation séquentielle et tests</td></tr>
    <tr><td>PlantUML</td><td>1.2024.7</td><td>Diagramme d'états, diagramme de séquence</td></tr>
    <tr><td>JFLAP</td><td>7.1</td><td>Automate des états, simulation de séquences</td></tr>
    <tr><td>PIPE</td><td>5.0.2</td><td>Réseau de Petri, graphe d'accessibilité</td></tr>
    <tr><td>NuSMV</td><td>2.7.1</td><td>Vérification CTL/LTL, contre-exemples</td></tr>
    <tr><td>PRISM</td><td>4.11</td><td>Vérification probabiliste (PCTL)</td></tr>
  </table>
</section>

<!-- ===================== 1. Specification ===================== -->
<section>
  <div class="kicker">Section 1</div>
  <h2>Spécification de l'opération de réservation</h2>
  <p>L'état du système est décrit par trois variables&#8239;: la capacité <code>N</code>, le nombre de places libres <code>placesLibres</code> et le nombre de réservations confirmées <code>nbConfirmees</code>. Chaque demande <code>d</code> possède un état parmi <i>EN_ATTENTE</i>, <i>CONFIRMEE</i>, <i>REFUSEE</i> et <i>ANNULEE</i>.</p>
  <div class="contract"><dl>
    <dt>Invariant</dt><dd>0 ≤ placesLibres ≤ N
placesLibres + nbConfirmees = N</dd>
    <dt>Préconditions de reserver(d)</dt><dd>d ≠ null  ∧  d.etat = EN_ATTENTE  ∧  Invariant</dd>
    <dt>Postconditions de reserver(d)</dt><dd>placesLibres₀ &gt; 0  ⇒  d.etat = CONFIRMEE  ∧  placesLibres = placesLibres₀ − 1
placesLibres₀ = 0  ⇒  d.etat = REFUSEE    ∧  placesLibres = placesLibres₀
Invariant</dd>
  </dl></div>
  <p>L'indice <code>₀</code> désigne la valeur avant l'appel. La première ligne de l'invariant interdit la sur-réservation (jamais moins de zéro place libre). La seconde garantit qu'aucune place n'est perdue ni comptée deux fois.</p>
  <div class="contract"><dl>
    <dt>Préconditions de annuler(d)</dt><dd>d.etat ∈ {{EN_ATTENTE, CONFIRMEE}}  ∧  Invariant</dd>
    <dt>Postconditions de annuler(d)</dt><dd>d.etat = ANNULEE
d.etat₀ = CONFIRMEE  ⇒  placesLibres = placesLibres₀ + 1
d.etat₀ = EN_ATTENTE ⇒  placesLibres = placesLibres₀
Invariant</dd>
  </dl></div>
</section>

<!-- ===================== 2. Java ===================== -->
<section>
  <div class="kicker">Section 2</div>
  <h2>Implémentation Java séquentielle</h2>
  <p>La classe <code>SystemeReservation</code> traduit directement le contrat&#8239;: chaque méthode vérifie ses préconditions et l'invariant à l'entrée, puis ses postconditions et l'invariant à la sortie. Une violation lève une <code>IllegalStateException</code>. Les vérifications sont explicites (et non des <code>assert</code>) pour rester actives sans option de la JVM.</p>
  {code(reserver_excerpt, "java")}
  <div class="cmd">cd 1-java &amp;&amp; javac -d out src/*.java &amp;&amp; java -cp out Main</div>
  <h3>Résultats des tests ({java_summary.replace("reussis", "réussis")})</h3>
  <p>Scénario avec une capacité de 2&#8239;: A et B sont confirmées, C est refusée, A annule, puis D obtient la place libérée. Les appels qui violent une précondition doivent être rejetés.</p>
  <table><tr><th>Test</th><th style="width:16%">Résultat</th></tr>{rows_java}</table>
</section>

<!-- ===================== 3. Etats ===================== -->
<section>
  <div class="kicker">Section 3</div>
  <h2>États et transitions d'une réservation</h2>
  <p>Une demande naît <i>En attente</i>. La réservation la conduit vers <i>Confirmée</i> ou <i>Refusée</i> selon les places disponibles&#8239;; l'annulation la conduit vers <i>Annulée</i>. Les gardes et les effets sur <code>placesLibres</code> reprennent le contrat de la section 1.</p>
  <figure class="w-etats"><div class="frame">{svg("etats.svg")}</div>
    <figcaption><b>Figure 1.</b> Diagramme d'états (PlantUML, <code>2-etats/etats.puml</code>).</figcaption></figure>
  <h3>Automate JFLAP et simulation</h3>
  <p>L'automate fini <code>2-etats/etats.jff</code> encode les mêmes transitions avec l'alphabet <code>c</code> (réserver avec place libre), <code>r</code> (réserver sans place libre) et <code>a</code> (annuler). Une séquence est acceptée si elle respecte les transitions autorisées. Le fichier a été chargé et simulé avec le moteur de JFLAP 7.1 (équivalent de <i>Input › Multiple Run</i>).</p>
  <div class="two" style="align-items:start">
    <figure class="w-auto" style="margin-top:0"><div class="frame">{svg("automate_jflap.svg")}</div>
      <figcaption><b>Figure 2.</b> Automate JFLAP. États finaux en double cercle.</figcaption></figure>
    <table class="keep" style="margin-top:0">
      <tr><th>Séquences</th><th>Résultat</th><th>Sens</th></tr>
      <tr><td><code>c</code> <code>r</code> <code>a</code></td><td class="ok">acceptées</td><td>confirmation, refus, abandon</td></tr>
      <tr><td><code>ca</code></td><td class="ok">acceptée</td><td>confirmer puis annuler</td></tr>
      <tr><td><code>cc</code> <code>rc</code> <code>ac</code></td><td class="ko">rejetées</td><td>double confirmation, confirmer après un refus ou une annulation</td></tr>
      <tr><td><code>rr</code> <code>aa</code> <code>cac</code></td><td class="ko">rejetées</td><td>sortir d'un état final</td></tr>
    </table>
  </div>
</section>

<!-- ===================== 4. Concurrence ===================== -->
<section>
  <div class="kicker">Section 4</div>
  <h2>Deux utilisateurs, une dernière place</h2>
  <p>Le diagramme de séquence compare deux exécutions lorsque <code>placesLibres = 1</code>. Dans la version incorrecte, la vérification de la place et la décrémentation sont deux étapes séparées&#8239;: les deux utilisateurs voient la place libre avant que l'un d'eux ne la prenne. Dans la version correcte, les deux opérations forment une seule action atomique protégée par un verrou.</p>
  <figure class="w-seq"><div class="frame">{svg("concurrence.svg")}</div>
    <figcaption><b>Figure 3.</b> Scénario concurrent (PlantUML, <code>2-etats/concurrence.puml</code>). L'ordre des étapes de la version incorrecte reprend le contre-exemple produit par NuSMV (section 7).</figcaption></figure>
</section>

<!-- ===================== 5. Petri ===================== -->
<section class="page">
  <div class="kicker">Section 5</div>
  <h2>Réseau de Petri&#8239;: disponibilité et conflits</h2>
  <p>Le réseau <code>3-petri/reservation.pnml</code> (format PIPE) modélise deux utilisateurs et une place. La place <code>Libres</code> contient un jeton par place disponible, <code>Occupees</code> un jeton par place attribuée. Chaque utilisateur possède un jeton qui circule entre ses quatre états.</p>
  <figure class="w-petri"><div class="frame">{svg("petri.svg")}</div>
    <figcaption><b>Figure 4.</b> Réseau de Petri, marquage initial (<code>N = 1</code>). Les transitions sont en noir, leurs noms en orange.</figcaption></figure>
  <ul>
    <li><code>reserver_Ui</code> consomme le jeton de <code>Libres</code> et le place dans <code>Occupees</code>.</li>
    <li><code>refuser_Ui</code> n'est franchissable que si <code>Occupees</code> contient <code>N</code> jetons (arcs de poids <code>N</code> dans les deux sens). C'est un test à zéro de <code>Libres</code> sans arc inhibiteur.</li>
    <li><code>annuler_Ui</code> rend le jeton à <code>Libres</code>&#8239;; <code>abandonner_Ui</code> annule une demande encore en attente.</li>
  </ul>
  <div class="note"><b>Conflit sur la dernière place.</b> Dans le marquage initial, <code>reserver_U1</code> et <code>reserver_U2</code> sont toutes deux franchissables mais se disputent l'unique jeton de <code>Libres</code>&#8239;: le franchissement de l'une désactive l'autre. Le réseau rend ainsi la réservation atomique par construction.</div>
  <div class="keepblock">
  <h3>Analyse du graphe d'accessibilité</h3>
  <p>Le graphe a été exploré avec le moteur d'animation de PIPE 5.0.2.</p>
  <table class="keep">
    <tr><th>Propriété</th><th>Résultat</th></tr>
    <tr><td>Marquages accessibles</td><td>12</td></tr>
    <tr><td>Transitions franchissables au départ</td><td><code>reserver_U1</code>, <code>reserver_U2</code>, <code>abandonner_U1</code>, <code>abandonner_U2</code></td></tr>
    <tr><td>Borné</td><td><span class="ok">oui</span>, 1-borné (réseau sauf)</td></tr>
    <tr><td>Invariant de places <code>Libres + Occupees = N</code></td><td><span class="ok">vérifié</span> dans les 12 marquages</td></tr>
    <tr><td>Double réservation <code>Confirmee_U1 + Confirmee_U2 &gt; N</code></td><td><span class="ok">jamais atteinte</span></td></tr>
    <tr><td>Blocages</td><td>aucun&#8239;: les 3 marquages morts sont des états finaux (refus ou annulation)</td></tr>
  </table>
  </div>
</section>

<!-- ===================== 6. Proprietes ===================== -->
<section>
  <div class="kicker">Section 6</div>
  <h2>Propriétés de sûreté et de vivacité</h2>
  <p>Une propriété de <b>sûreté</b> affirme que rien de mauvais n'arrive jamais (forme <code>AG ¬mauvais</code>). Une propriété de <b>vivacité</b> affirme que quelque chose de bon finit par arriver (forme <code>AF bon</code> ou <code>EF bon</code>). Les formules portent sur le modèle NuSMV, où <code>u1</code> et <code>u2</code> sont les états des deux demandes et <code>libres</code> le nombre de places disponibles.</p>
  <table>
    <tr><th></th><th style="width:34%">Propriété</th><th>Formule</th></tr>
    <tr><td class="id">S1</td><td>Places libres dans <code>[0, N]</code></td><td><code>AG (libres &gt;= 0 &amp; libres &lt;= N)</code></td></tr>
    <tr><td class="id">S2</td><td>Cohérence du nombre de places</td><td><code>AG (libres + nb_confirmees = N)</code></td></tr>
    <tr><td class="id">S3</td><td>Pas de double réservation</td><td><code>AG !(u1 = confirmee &amp; u2 = confirmee)</code></td></tr>
    <tr><td class="id">S4</td><td>Refus et annulation définitifs</td><td><code>AG (u1 = refusee -&gt; AG u1 = refusee)</code></td></tr>
    <tr><td class="id">S5</td><td>Refus seulement si complet</td><td><code>AG ((u1 = attente &amp; libres &gt; 0) -&gt; AX u1 != refusee)</code></td></tr>
    <tr><td class="id">V1</td><td>Toute demande reçoit une réponse</td><td><code>AG (u1 = attente -&gt; AF u1 != attente)</code></td></tr>
    <tr><td class="id">V2</td><td>Chacun peut obtenir la place</td><td><code>EF (u1 = confirmee)</code></td></tr>
    <tr><td class="id">V3</td><td>Les deux demandes sont traitées (LTL)</td><td><code>F (u1 != attente &amp; u2 != attente)</code></td></tr>
    <tr><td class="id">V4</td><td>Une place libérée peut être reprise</td><td><code>AG ((u1 = annulee &amp; u2 = attente) -&gt; EF u2 = confirmee)</code></td></tr>
  </table>
  <p>S4, V1 et V2 sont vérifiées pour les deux utilisateurs. Les propriétés de vivacité supposent un ordonnanceur équitable, déclaré par <code>FAIRNESS qui = 1</code> et <code>FAIRNESS qui = 2</code>&#8239;: sans cette hypothèse, un utilisateur pourrait ne jamais être servi.</p>
</section>

<!-- ===================== 7. NuSMV ===================== -->
<section>
  <div class="kicker">Section 7</div>
  <h2>Vérification avec NuSMV</h2>
  <p>Deux modèles partagent les mêmes variables et les mêmes propriétés. Seul le protocole de réservation change&#8239;:</p>
  <ul>
    <li><code>reservation_correcte.smv</code>&#8239;: la vérification et la décrémentation se font en un seul pas.</li>
    <li><code>reservation_bug.smv</code>&#8239;: l'utilisateur passe d'abord par un état interne <code>verifiee</code> (il a vu une place libre), puis confirme et décrémente plus tard <b>sans revérifier</b>.</li>
  </ul>
  <div class="cmd">NuSMV 4-nusmv/reservation_correcte.smv
NuSMV 4-nusmv/reservation_bug.smv</div>
  <table class="smv">
    <tr><th></th><th>Spécification NuSMV</th><th>Modèle correct<br>24 états</th><th>Modèle incorrect<br>40 états</th></tr>
    {rows_smv}
  </table>
  <div class="note good"><b>Toutes les propriétés sont vraies sur le modèle correct</b> ({n_true}/{len(smv_ok)}). Le modèle incorrect viole S1 (borne des places) et S3 (double réservation).</div>
  <div class="keepblock">
  <h3>Analyse du contre-exemple</h3>
  <p>Pour S1 comme pour S3, NuSMV produit la même trace de cinq états (sortie complète&#8239;: <code>4-nusmv/resultat_bug.txt</code>)&#8239;:</p>
  <table class="keep">
    <tr><th>État</th><th>u1</th><th>u2</th><th>libres</th><th style="width:46%">Ce qui se passe</th></tr>
    <tr><td class="id">1.1</td><td>attente</td><td>attente</td><td>1</td><td>État initial, une place libre</td></tr>
    <tr><td class="id">1.2</td><td>verifiee</td><td>attente</td><td>1</td><td>U1 constate qu'une place est libre</td></tr>
    <tr><td class="id">1.3</td><td>verifiee</td><td>verifiee</td><td>1</td><td>U2 constate aussi la place libre&#8239;: personne n'a encore décrémenté</td></tr>
    <tr><td class="id">1.4</td><td>verifiee</td><td>confirmee</td><td>0</td><td>U2 prend la place</td></tr>
    <tr class="hl"><td class="id">1.5</td><td>confirmee</td><td>confirmee</td><td><b>−1</b></td><td>U1 confirme sur la foi d'une vérification périmée&#8239;: <b>double réservation</b></td></tr>
  </table>
  </div>
  <div class="note"><b>Pourquoi S2 reste vraie.</b> L'égalité <code>libres + nb_confirmees = N</code> tient même dans le modèle incorrect, car chaque confirmation décrémente le compteur&#8239;: à l'état 1.5, <code>−1 + 2 = 1</code>. Un invariant de comptage seul ne détecte donc pas la sur-réservation&#8239;; il faut aussi la borne <code>libres ≥ 0</code> (S1) ou l'exclusion directe (S3).</div>
  <p><b>Correction.</b> Le défaut vient de l'intervalle entre la lecture de <code>libres</code> et sa modification. Rendre ces deux opérations atomiques (verrou, section critique ou opération <i>compare-and-set</i>) supprime l'entrelacement fautif&#8239;: c'est exactement le modèle <code>reservation_correcte.smv</code>, sur lequel toutes les propriétés sont vraies.</p>
</section>

<!-- ===================== 8. PRISM ===================== -->
<section>
  <div class="kicker">Section 8</div>
  <h2>Modèle probabiliste avec PRISM</h2>
  <p>Le modèle <code>5-prism/reservation.pm</code> est une chaîne de Markov à temps discret. À chaque pas, la demande en attente est soit traitée, soit retardée, soit perdue à cause d'une panne&#8239;; une demande perdue doit être renvoyée, ce qui coûte un pas. Pendant ce temps, d'autres clients peuvent prendre les places restantes. Si plus aucune place n'est libre, la demande est refusée.</p>
  <table class="keep num" style="width:auto">
    <tr><th>Paramètre</th><th>Valeur</th><th style="text-align:left">Signification</th></tr>
    <tr><td><code>N</code></td><td>2</td><td style="text-align:left">places libres au départ</td></tr>
    <tr><td><code>p_retard</code></td><td>0,2</td><td style="text-align:left">la demande est retardée d'un pas</td></tr>
    <tr><td><code>p_echec</code></td><td>0,1</td><td style="text-align:left">panne&#8239;: la demande est perdue et renvoyée</td></tr>
    <tr><td><code>p_autre</code></td><td>0,3</td><td style="text-align:left">un autre client prend une place pendant le pas</td></tr>
  </table>
  <div class="cmd">prism 5-prism/reservation.pm 5-prism/proprietes.pctl -const T=1:10</div>
  <figure class="w-chart"><div class="frame">{svg("prism_courbe.svg")}</div>
    <figcaption><b>Figure 5.</b> Probabilité que la réservation soit confirmée avant l'échéance <code>T</code>, <code>P=? [ F&lt;=T "confirmee" ]</code> (PRISM 4.11).</figcaption></figure>
  <table class="keep num"><tr><th>T</th>{prism_head}</tr><tr><td><b>P</b></td>{prism_vals}</tr></table>
  <table class="keep">
    <tr><th style="width:44%">Propriété PCTL</th><th>Résultat</th></tr>
    <tr><td><code>P=? [ F "confirmee" ]</code></td><td>{fr(p_conf, 4)}</td></tr>
    <tr><td><code>P=? [ F "refusee" ]</code></td><td>{fr(p_ref, 4)}</td></tr>
    <tr><td><code>P&gt;=1 [ F ("confirmee" | "refusee") ]</code></td><td><span class="ok">vraie</span>&#8239;: toute demande est traitée</td></tr>
  </table>
  <p><b>Interprétation.</b> Sans panne ni retard, la demande serait confirmée au premier pas. Les défaillances la retardent&#8239;: 70&#8239;% de confirmations au premier pas, {fr(p3*100, 1)}&#8239;% avant trois pas. La courbe se stabilise vers {fr(p_conf, 4)} à partir de <code>T = 6</code>. Les pannes et les retards ne provoquent un refus ({fr(p_ref*100, 1)}&#8239;%) que si les autres clients prennent toutes les places pendant l'attente.</p>
</section>

<!-- ===================== 9. Conclusion ===================== -->
<section class="page">
  <div class="kicker">Section 9</div>
  <h2>Conclusion</h2>
  <ul>
    <li>Le contrat de <code>reserver</code> (préconditions, postconditions, invariant) est respecté par l'implémentation séquentielle&#8239;: {java_summary.replace("reussis", "réussis")}.</li>
    <li>En concurrence, une réservation non atomique permet la double réservation de la dernière place. NuSMV le démontre par un contre-exemple de cinq états.</li>
    <li>La version atomique vérifie toutes les propriétés de sûreté et, sous équité, de vivacité. Le réseau de Petri confirme ce résultat&#8239;: 1-borné, invariant de places respecté, aucune double réservation.</li>
    <li>PRISM quantifie l'effet des pannes et des retards&#8239;: {fr(p_conf*100, 1)}&#8239;% des demandes sont confirmées, dont {fr(p3*100, 1)}&#8239;% avant trois unités de temps.</li>
  </ul>
  <p>La vérification formelle a trouvé un défaut que des tests séquentiels ne pouvaient pas révéler, et elle a prouvé l'absence de ce défaut dans la version corrigée sur l'ensemble des exécutions possibles.</p>
  <h3>Fichiers livrés</h3>
  <table class="keep">
    <tr><th style="width:42%">Fichier</th><th>Contenu</th></tr>
    <tr><td><code>1-java/src/*.java</code></td><td>Implémentation séquentielle avec contrats, scénarios de test (<code>Main</code>)</td></tr>
    <tr><td><code>2-etats/etats.puml</code>, <code>etats.jff</code></td><td>Diagramme d'états PlantUML, automate JFLAP</td></tr>
    <tr><td><code>2-etats/concurrence.puml</code></td><td>Scénario des deux utilisateurs (versions incorrecte et correcte)</td></tr>
    <tr><td><code>3-petri/reservation.pnml</code></td><td>Réseau de Petri (PIPE)</td></tr>
    <tr><td><code>4-nusmv/reservation_correcte.smv</code>, <code>reservation_bug.smv</code></td><td>Modèles NuSMV et propriétés CTL/LTL</td></tr>
    <tr><td><code>4-nusmv/resultat_*.txt</code></td><td>Sorties NuSMV, dont le contre-exemple</td></tr>
    <tr><td><code>5-prism/reservation.pm</code>, <code>proprietes.pctl</code></td><td>Modèle PRISM et propriétés PCTL</td></tr>
    <tr><td><code>5-prism/resultats.txt</code></td><td>Résultats PRISM pour <code>T = 1..10</code></td></tr>
  </table>
</section>

<!-- ===================== Annexes ===================== -->
<section class="annex page">
  <div class="kicker">Annexe A</div>
  <h2>Sources</h2>
  <h3>A.1 · <code>1-java/src/SystemeReservation.java</code></h3>
  {code(reserver_src, "java")}
</section>
<section class="annex">
  <h3>A.2 · <code>4-nusmv/reservation_correcte.smv</code></h3>
  {code(read("4-nusmv/reservation_correcte.smv"), "smv")}
</section>
<section class="annex">
  <h3>A.3 · <code>4-nusmv/reservation_bug.smv</code></h3>
  {code(read("4-nusmv/reservation_bug.smv"), "smv")}
</section>
<section class="annex">
  <h3>A.4 · <code>5-prism/reservation.pm</code></h3>
  {code(read("5-prism/reservation.pm"), "prism")}
  <h3>A.5 · <code>5-prism/proprietes.pctl</code></h3>
  {code(read("5-prism/proprietes.pctl"), "prism")}
</section>
</body></html>
"""

out_html = ROOT / "rapport" / "rapport.html"
out_html.write_text(HTML, encoding="utf-8")
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={ROOT / 'RAPPORT.pdf'}", out_html.as_uri()],
               check=True, capture_output=True)
print("RAPPORT.pdf genere")
