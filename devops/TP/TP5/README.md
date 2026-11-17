# TP5 — Git and GitHub

Executed on 17 November 2026 against the six-page [assignment](../TP5_Git.pdf).

- [Report PDF](rapport.pdf), [editable report](rapport.md) and [all question answers](ANSWERS.md).
- [GitHub repository](https://github.com/mimobn/StudentManagement), with 21 commits and four merged PRs.
- [Release v1.0.0](https://github.com/mimobn/StudentManagement/releases/tag/v1.0.0).
- [Submission ZIP](TP5-submission.zip), including original screenshots and evidence.
- [Source snapshot](StudentManagement/) and [offline Git bundle](StudentManagement.bundle).

One account only, as requested: Exercise 7 has a real inline COMMENT review, a fix and a merge. No independent approval or REQUEST_CHANGES review is claimed. The initial one-approval rule is recorded; the final main protection requires a PR with zero approvals and applies to administrators.

The optional hello Actions workflow succeeded. The registration three-way merge, all undo operations and a real heading conflict are recorded in [evidence](evidence/).

## Open the project

Open `StudentManagement/index.html` in Edge. This static teaching form does not store student registrations; the support address is a demonstration address.

## Inspect history offline

```sh
git clone StudentManagement.bundle StudentManagement-restored
cd StudentManagement-restored
git log --oneline --graph --all
git show v1.0.0 --no-patch
```

## Rebuild the report

From the course repository, with Python, reportlab, pillow and pymupdf installed:

```sh
python devops/TP/TP5/build_report.py
```

The builder uses `scripts/generer-resumes.py` for shared formatting. It reads saved evidence, checks the recorded final results, and rebuilds Markdown, PDF, hashes and ZIP without modifying GitHub or the exercise history. The self-contained ZIP includes the finished report; rebuilding requires the course repository's formatting helper.
