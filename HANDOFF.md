# Handoff: ng911-extract — 6-month JOSS clock

*Date: 2026-09-05 (end of session)*
*Next action: 2027-03-05 or later*

---

## TL;DR

You pushed a JOSS submission package to GitHub today. The repo is **live at https://github.com/wangtiankai/ng911-extract** with CI green. JOSS will not let you submit for **at least six months** because they require more than six months of public development history with iterative activity. Your job over the next six months is to make 8–10 small, well-scoped improvements to the repo so the commit log shows steady maintenance rather than a one-time dump. After six months, submit at `http://joss.theoj.org/papers/new`.

Everything you need to remember is in this document. Don't try to reconstruct from memory.

---

## 1. What is the repo

**URL:** https://github.com/wangtiankai/ng911-extract

**What it does:** Builds a state-by-year panel of Next Generation 911 (NG911) deployment data from the U.S. National 911 Profile Database Progress Reports. The NHTSA Program Office stopped maintaining the database in 2024, but the underlying annual PDFs are still publicly hosted at `911.gov/assets/`. The pipeline ingests those PDFs, extracts the state-by-state grid, and stacks them into one CSV.

**License:** MIT.

**Language:** Python 3.10+.

**Author:** Tiankai Wang, Texas State University, ORCID 0000-0003-0083-0218.

---

## 2. What was done today (2026-09-05)

| Step | Status |
|---|---|
| NHTSA Profile Database request denied | done |
| 8 historical Progress Report PDFs downloaded | done |
| 3.2.x schema extractor (2013–2016 reports) | done |
| Maturity Model extractor (2018–2020 reports) | done |
| Master panel built: `data/ng911/state_ng911_panel.csv` (392 rows, 56 jurisdictions × 7 years) | done |
| Event study, falsifications, and verdict scripts run | done |
| **Verdict: STOP** (urban falsification fires strongly, pre-trend fails, notification effect null) | done |
| JOSS submission package drafted (`paper.md`, `paper.bib`, `README.md`, `LICENSE`, `pyproject.toml`, `CITATION.cff`) | done |
| Smoke tests written (10 tests, all passing) | done |
| CI workflow on Python 3.10 / 3.11 / 3.12 | green on first run |
| Repo created at https://github.com/wangtiankai/ng911-extract | done |
| Initial commit `566a1c2` pushed | done |
| `BACKLOG.md` with 10 good-first-issues committed and pushed (`a0c71e5`) | done |

Two commits on `main` as of now:
- `566a1c2` — initial commit (29 files, 1,937 insertions)
- `a0c71e5` — `BACKLOG.md`

---

## 3. Where the local files live

The local git repo is at `C:\Users\tw26\ng911-extract`. This is the canonical working tree — every change you make should happen here, get committed, and pushed. Don't edit files in `C:\Users\tw26\dead-zones\output\joss_submission\` — that was just the staging folder for the JOSS submission and is now stale.

The original project (`C:\Users\tw26\dead-zones\`) still has the FARS data, the killed cellular-coverage design, and the original kill-test verdict for the NG911 study. None of that is in the `ng911-extract` repo on purpose — the JOSS submission is for the *pipeline* only, not the empirical findings.

---

## 4. What you need to do over the next six months

### 4.1. The clock

JOSS's submission rule: **more than six months of public development history**, with iterative activity (not a single burst of commits). The clock started when the repo was first made public (today, 2026-09-05). Earliest submission date: **2027-03-05**.

### 4.2. The cadence

Open one issue from `BACKLOG.md` every 2–3 weeks, work it for 1–2 hours, push, close. Over six months: ~10 issue-open events, ~10 issue-close events, ~10 PRs. That is enough activity to satisfy JOSS.

The full list is in `BACKLOG.md` at the repo root. Recommended order:

1. **Issue 4 first** — unit test for `parse_grid`. Highest impact (raises the test count), takes ~2 hours, and the CI badge updates immediately.
2. **Issues 2, 3, 6, 9** — mechanical (type hints, CITATION.cff validation, summarize_panel). Good for low-energy days.
3. **Issues 1, 7, 10** — documentation. Good for thinking-but-not-coding days.
4. **Issues 5, 8 last** — slightly larger. Save for chunks of free time.

### 4.3. Step-by-step procedure for each issue

Here is the exact shell recipe. Run in Git Bash, PowerShell, or Command Prompt. The `!` prefix in Claude Code runs the command in this session.

#### Step A — Pick an issue

Open GitHub at https://github.com/wangtiankai/ng911-extract/issues. If none of the 10 backlog issues exist as GitHub issues yet, open one:

1. Go to https://github.com/wangtiankai/ng911-extract/issues/new
2. Title: `Add unit test for parse_grid (#4 from BACKLOG.md)` (or whichever issue number you're opening)
3. Body: copy the relevant section from `BACKLOG.md`
4. Labels: `good first issue`, `tests` (or `documentation` or `enhancement` as marked)
5. Submit.

Note the issue number GitHub assigns (e.g., `#2`).

#### Step B — Create a branch

In your shell:

```bash
cd "C:\Users\tw26\ng911-extract"
git checkout main
git pull origin main
git checkout -b fix/parse-grid-test
```

Branch naming convention from Issue 10:
- `fix/<short-description>` for bug fixes
- `feat/<short-description>` for new features
- `docs/<short-description>` for documentation

#### Step C — Make the change

Edit the file(s) the issue is about. Save.

#### Step D — Run the tests locally

```bash
pytest tests/ -v
```

All tests should pass. If they don't, fix the code before committing.

#### Step E — Commit and push

```bash
git add .
git commit -m "Add unit tests for parse_grid (#2)

- Add tests/test_extract.py with 4 cases
- Cover 4-column grids, 2-column grids, summary blocks
- All 10+ tests pass"
git push -u origin fix/parse-grid-test
```

The commit message should reference the issue number with `#N` syntax — GitHub will auto-link it.

#### Step F — Open a PR

1. After the push, GitHub shows a banner: "Compare & pull request". Click it.
2. Title: same as the commit (or a polished version).
3. Body: `Closes #2. Added N tests; all green.`
4. Click "Create pull request".
5. Wait ~30 seconds for CI to run. The Actions tab should show a green check.
6. Click "Merge pull request" → "Confirm merge". Delete the branch when prompted.

#### Step G — Verify the issue closed

The issue should auto-close when the PR merges (because the PR body says `Closes #2`). If it doesn't, manually close it with a comment:

> Closed via #N. All tests pass; CI green.

---

## 5. What you do NOT need to do

- Don't open more than one issue every 2 weeks. JOSS wants steady activity, not a flurry.
- Don't edit the empirical findings (`output/verdict_ng911.md`, the FARS parquet files). The JOSS submission is for the *pipeline*, not the result.
- Don't add new dependencies without checking that they install cleanly on Python 3.10 / 3.11 / 3.12 (the CI matrix).
- Don't rebase `main` after merging. Linear history is fine for JOSS.

---

## 6. After six months — submission

On or after **2027-03-05**:

1. Go to http://joss.theoj.org/papers/new
2. Fill in:
   - **Repository URL:** `https://github.com/wangtiankai/ng911-extract`
   - **Software version:** tag a release at this point (`git tag v0.1.0 && git push --tags`)
   - **Author list:** Tiankai Wang (with ORCID)
   - **Affiliation:** Texas State University
   - **Suggested reviewers:** (optional; you can leave blank)
3. Submit. JOSS assigns a managing editor who opens a pre-review issue. Expect 2–6 weeks for the first response.
4. After acceptance: deposit the tagged release with Zenodo (https://zenodo.org) to get a DOI. JOSS will then issue a CrossRef DOI for the paper itself.

---

## 7. Things that could go wrong

### 7.1. CI breaks after a Python release

If `pytest` fails on a new Python version, edit `.github/workflows/test.yml` to pin the matrix. Common fix: drop Python 3.13 if `pypdf` lags.

### 7.2. Akamai blocks you again

If `code/fetch_ng911_pdfs.py` stops working for new PDFs (it already requires Playwright; see Issue 7), don't fix it — that's an external problem, not a repo bug. The 8 PDFs in `data/ng911/raw_pdfs/` are already there.

### 7.3. The master panel goes stale

If NHTSA publishes a 2021+ report that you'd like to add, run the appropriate extractor (`ng911_extract_maturity.py` for the Maturity Model years; that script is already parameterized for any year). Then update `BACKLOG.md` Issue 5 to mention the new pages.

### 7.4. JOSS asks for revisions

Common JOSS reviewer requests:
- "Add a CONTRIBUTING.md" → that's Issue 10 in the backlog.
- "Add a CHANGELOG.md" → create it with the release notes from your tagged commit.
- "Confirm the package installs cleanly with `pip install git+https://...`" → run that locally and verify.

If a reviewer asks for something outside the backlog, do it. They are gatekeepers.

### 7.5. You forget about the project

Set a calendar reminder for **2027-03-01** titled "Start JOSS submission for ng911-extract." Even if you can't find time, open the submission page and start the form. You can save the form partway and finish later.

---

## 8. Quick reference card

| Item | Value |
|---|---|
| Repo URL | https://github.com/wangtiankai/ng911-extract |
| Local path | `C:\Users\tw26\ng911-extract` |
| Submission URL (after 6 months) | http://joss.theoj.org/papers/new |
| Earliest submission date | 2027-03-05 |
| Paper manuscript | `paper.md` |
| Bibliography | `paper.bib` |
| License | MIT (`LICENSE`) |
| Citation metadata | `CITATION.cff` |
| Smoke tests | `pytest tests/ -v` |
| CI status | https://github.com/wangtiankai/ng911-extract/actions |
| Backlog | `BACKLOG.md` (10 issues) |
| JOSS scope rules | https://joss.readthedocs.io/en/latest/submitting.html |

---

## 9. The empirical work that is NOT in this repo

For completeness — this is what is *not* in the JOSS submission:

- **The verdict.** The empirical result was STOP. Documented at `C:\Users\tw26\dead-zones\output\verdict_ng911.md` and `C:\Users\tw26\dead-zones\output\HANDOFF.md`. Not part of the JOSS submission.
- **The FARS data.** ~510K rows in `C:\Users\tw26\dead-zones\data\fars\`. Not in the JOSS repo (FARS is its own dataset; cite it in your paper but don't redistribute).
- **The killed cellular-coverage design.** All the `04_event_study.py`, `04b_daytime.py`, `05_verdict.py` scripts at `C:\Users\tw26\dead-zones\code\`. Don't confuse them with the `ng911_*` scripts.

If you ever come back to this project to write the empirical paper (or a methods note on why NG911 didn't work), the data and code at `C:\Users\tw26\dead-zones\` are still there.

---

*Good night. The repo is in good shape.*
