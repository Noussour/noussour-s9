"""Build the TP5 report and submission archive from recorded execution evidence.

Run from any directory with reportlab, pillow and pymupdf installed.
This script does not mutate Git history or publish anything.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import zipfile

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, Spacer
from reportlab.platypus.tableofcontents import TableOfContents

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
EV=BASE/'evidence'
spec=importlib.util.spec_from_file_location('report_format',ROOT/'scripts/generer-resumes.py')
fmt=importlib.util.module_from_spec(spec)
spec.loader.exec_module(fmt)


class LabReport(fmt.ResumeDoc):
    def decorate(self,canvas,doc):
        canvas.saveState()
        canvas.setFillColor(fmt.NAVY)
        canvas.rect(0,A4[1]-8,A4[0],8,fill=1,stroke=0)
        canvas.setFont('ResumeSans',7)
        canvas.setFillColor(fmt.GREY)
        canvas.drawString(self.leftMargin,A4[1]-29,'USTHB · DEVOPS AND CLOUD COMPUTING · TP5')
        canvas.drawRightString(A4[0]-self.rightMargin,A4[1]-29,'EXECUTION REPORT · 17 NOVEMBER 2026')
        canvas.setStrokeColor(colors.HexColor('#d5e1e9'))
        canvas.line(self.leftMargin,36,A4[0]-self.rightMargin,36)
        canvas.drawString(self.leftMargin,23,'Git and GitHub · StudentManagement · mimobn')
        canvas.drawRightString(A4[0]-self.rightMargin,23,str(doc.page))
        canvas.restoreState()


def main():
    verify=json.loads((EV/'verification.json').read_text(encoding='utf-8'))
    prs=json.loads((EV/'pull-requests.json').read_text(encoding='utf-8'))
    screenshots=json.loads((EV/'screenshots.json').read_text(encoding='utf-8'))
    assert verify['worktree_clean'] and verify['main_ci_run']['conclusion']=='success'
    assert all(p['state']=='MERGED' for p in prs)
    assert len(screenshots)==8 and all((EV/s['file']).exists() for s in screenshots)
    answers=(BASE/'ANSWERS.md').read_text(encoding='utf-8')
    questions=answers[answers.index('## Exercise 1'):].replace('## Exercise','### Exercise').replace('## Bonus','### Bonus').replace('## References','### References')
    pr_rows='\n'.join(f'| #{p["number"]} | {p["title"]} | {p["state"]} | {p["mergeCommit"]["oid"][:7]} |' for p in sorted(prs,key=lambda p:p['number']))
    report=f'''# TP5 — Git and GitHub

USTHB · 5th Year Software Engineering · 2026/2027

Module: DevOps and Cloud Computing · Instructor: Ameur Imane

GitHub account: mimobn · Execution date: 17 November 2026

Repository: [mimobn/StudentManagement](https://github.com/mimobn/StudentManagement)

Executed solution with real Git history, GitHub pull requests, a resolved conflict, an annotated tag and a published release. This report includes all worksheet answers and genuine Microsoft Edge captures.

## 1. Scope, environment and results

The six-page assignment TP5_Git.pdf was carried out in an isolated StudentManagement repository, separate from the course repository. Git 2.45.1.windows.1 ran on Windows through PowerShell/Python subprocesses; GitHub CLI used the existing mimobn login. Repository-local identity settings preserved the machine's existing global configuration.

**Single-account adaptation:** the user requested that no second account be used. Exercise 7 therefore has a real inline COMMENT review, a follow-up fix and a merged PR, but no independent approval or REQUEST_CHANGES review. The initial one-approval branch rule is preserved as evidence; the final rule requires a PR with zero approvals and applies to administrators. The two-person approval requirement is not claimed as completed. A second local clone, under the same account, demonstrates synchronization.

| Item | Verified outcome |
| --- | --- |
| Exercises 1–3 | Repository, ignore rules, staging/diffs and meaningful commits executed |
| Exercise 4 | Registration three-way merge ed39fcf, plus a separate fast-forward demonstration |
| Exercise 5 | restore, unstage, shared revert, mixed reset and stash executed |
| Exercise 6 | Public GitHub repository published over authenticated HTTPS |
| Exercise 7 | PR #1: inline comment, correction and merge; independent review omitted for solo use |
| Exercise 8 | PR #2 merged first; actual heading conflict resolved in merge 51cb7c6 and merged through PR #3 |
| Exercise 9 | Annotated tag v1.0.0 and GitHub Release published |
| Optional bonus | hello Actions workflow completed successfully on main |
| Final state | {verify['commit_count']} reachable commits; clean worktree; tag, local main and remote main agree |

## 2. Recorded execution and evidence

The complete command transcript is in evidence/commands.txt. It includes the original staged and unstaged diffs, the three-way merge graph, the five undo operations and their before/after outputs, pushes and actual conflict output. API responses are preserved alongside the transcript. No passwords or access tokens were written to the repository or report.

The first two commits created the requested index.html, README.md and .gitignore, then improved the welcome paragraph. On feature/registration, the form was committed separately; an independent README commit on main forced the required three-way merge:

```text
*   ed39fcf Merge the student registration feature
|\\
| * b1ef5d0 Add a student registration form
* | b36cd5d Document the registration feature
|/
* 498c44f Clarify the student management welcome message
* fdec0f7 Create initial student management structure
```

Scenario C was demonstrated with a truly shared change: commit 96ebb16 hid the heading and was pushed; revert f32a634 restored it and was then pushed. Neither published commit was removed. Scenario D's reset affected only an unpublished temporary commit. The stash scenario included a real branch switch and restoration before committing.

| Pull request | Purpose | Final state | Merge commit |
| --- | --- | --- | --- |
{pr_rows}

PR #1's inline comment asked for a clickable mailto link and a visible demonstration-address note. Commit f4425aa added both. The contact address uses example.invalid and is illustrative; the form is static and does not store registrations.

Both title branches started from the same main commit. After PR #2 integrated Student Information System, merging main into feature/title-b produced this actual conflict, saved before resolution:

```text
<<<<<<< HEAD
  <h1>University Student Portal</h1>
=======
  <h1>Student Information System</h1>
>>>>>>> main
```

The resolution selected University Student Portal, removed the conflict markers and retained the merged contact section. It was staged and committed as 51cb7c6, which has two parents, then pushed and merged through PR #3. Both local clones synchronized using git pull --ff-only origin main. The complete final graph is preserved in evidence/history-graph.txt.

The annotated tag resolves to {verify['tag_target']}. The [v1.0.0 release](https://github.com/mimobn/StudentManagement/releases/tag/v1.0.0) includes release notes. The [main Actions run]({verify['main_ci_run']['url']}) completed successfully after a push event; its saved log includes Hello from CI. This hello workflow demonstrates CI execution and does not validate application behavior.

## 3. Answers to all worksheet questions

{questions}

## 4. Screenshots and capture provenance

Eight screenshots were captured using Microsoft Edge controlled by Playwright. The GitHub captures show real public pages and need no browser login to view. The history and conflict captures show clearly labeled local evidence viewers containing actual recorded output; they are not terminal-screen simulations. Capture URLs and UTC timestamps are listed in evidence/screenshots.json. Original full-resolution PNGs are supplied with the submission.

![GitHub repository showing the published project files](evidence/01-github-repository.png)

![PR #1: actual solo inline comment, correction and merged discussion](evidence/02-contact-pull-request.png)

![PR #3: competing heading changes and resolution in the merge history](evidence/03-conflict-pull-request.png)

![Annotated version tag and published GitHub Release v1.0.0](evidence/04-release.png)

![GitHub Actions: actual hello workflow runs](evidence/05-actions.png)

![Evidence viewer: actual final git log --oneline --graph --all output](evidence/06-history.png)

![Evidence viewer: original conflict markers before resolution](evidence/07-conflict-record.png)

![Final static application opened in Microsoft Edge](evidence/08-application.png)

## 5. Deliverables and final checks

The submission includes rapport.pdf and rapport.md, ANSWERS.md, the StudentManagement source snapshot, the complete StudentManagement.bundle Git archive, original screenshots and execution evidence. The bundle preserves the branches, annotated tag and history without embedding a nested .git directory in the course repository.

To inspect the repository online:

```sh
git clone https://github.com/mimobn/StudentManagement.git
cd StudentManagement
git log --oneline --graph --all
git show v1.0.0 --no-patch
```

To recover the submitted history offline, run git clone StudentManagement.bundle StudentManagement-restored from the submission directory. Use git bundle verify StudentManagement.bundle inside a Git repository to inspect the bundle's integrity and references.

Verification checked the two-parent registration and conflict merge commits, all four merged PRs, the annotated tag object, agreement between tag/local main/remote main, a clean worktree, the successful main CI run and the absence of conflict markers in the final HTML. git fsck and git bundle verify completed successfully. evidence/manifest-sha256.json records file hashes at report generation; it is an integrity manifest, not an original capture timestamp.

The only worksheet limitation is the independent two-person review/approval in Exercise 7, explicitly replaced by the requested single-account demonstration. All nine exercises have answers in both this report and the repository's ANSWERS.md.
'''
    (BASE/'rapport.md').write_text(report,encoding='utf-8')
    fmt.fonts()
    doc=LabReport(BASE/'rapport.pdf','TP5 — Git and GitHub')
    doc.title='TP5 — Git and GitHub: StudentManagement'
    first=report.index('## 1.')
    intro=report[:first].splitlines()[1:]
    story=[Spacer(1,55),Paragraph('TP5',fmt.STYLES['title']),Paragraph('Git and GitHub',fmt.STYLES['subtitle']),Paragraph('StudentManagement · Execution report',fmt.STYLES['section']),Spacer(1,16)]
    story.extend(fmt.paragraphs(intro,doc))
    toc=TableOfContents();toc.levelStyles=[fmt.STYLES['toc']];toc.dotsMinLevel=0
    story.extend([PageBreak(),Paragraph('Contents',fmt.STYLES['section']),toc,PageBreak()])
    image_count=0
    for part in re.split(r'(^!\[[^\]]*\]\([^)]+\)\s*$)',report[first:],flags=re.M):
        match=re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)\s*',part)
        if not match:
            story.extend(fmt.paragraphs(part.splitlines(),doc));continue
        if image_count%2==0: story.append(PageBreak())
        with PILImage.open(BASE/match[2]) as im: w,h=im.size
        scale=min(doc.width/w,285/h)
        story.append(KeepTogether([Image(str(BASE/match[2]),width=w*scale,height=h*scale),Spacer(1,6),Paragraph(fmt.inline(match[1]),fmt.STYLES['body']),Spacer(1,14)]))
        image_count+=1
    doc.multiBuild(story)
    files=[p for p in BASE.rglob('*') if p.is_file() and p.name not in ['manifest-sha256.json','TP5-submission.zip'] and '__pycache__' not in p.parts]
    manifest={'algorithm':'SHA-256','purpose':'Integrity at report finalization; capture timestamps are in screenshots.json','files':[{'path':p.relative_to(BASE).as_posix(),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]}
    (EV/'manifest-sha256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    with zipfile.ZipFile(BASE/'TP5-submission.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
        for p in [*files,EV/'manifest-sha256.json']: archive.write(p,Path('TP5')/p.relative_to(BASE))
    print('Built rapport.md, rapport.pdf, evidence manifest and TP5-submission.zip')


if __name__=='__main__': main()
