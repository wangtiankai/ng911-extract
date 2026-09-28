# Monthly maintenance

This repository is maintained on a **monthly cadence**: one small, reviewable change per month (tests, docs, or a narrow enhancement), with a matching GitHub issue opened and closed when the work lands. That keeps the public history easy to follow and CI green.

## When to run

- **Target:** first week of each calendar month (or within seven days of the 1st).
- **Time budget:** about 1–2 hours per month.

## Monthly checklist

1. **Pull** latest `main`: `git pull origin main`
2. **Pick** the next item from [BACKLOG.md](BACKLOG.md) (or the oldest open issue on GitHub).
3. **Branch** (optional but tidy): `git checkout -b maint/YYYY-MM-short-topic`
4. **Implement** only that item; run `pytest tests/ -v` from the repo root.
5. **Commit** with a clear message (what changed and why).
6. **Push** and merge to `main` (direct push or PR).
7. **Close** the GitHub issue with a one-line summary and link to the commit.
8. **Open** the next backlog issue for the following month (copy title/body from BACKLOG.md).

Confirm **Actions** passed on https://github.com/wangtiankai/ng911-extract/actions after each push.

## Suggested six-month schedule

| Month (example) | Backlog item | Theme |
|-----------------|--------------|--------|
| 1 | Issue 4 | `tests/test_extract.py` for `parse_grid` |
| 2 | Issue 1 | Docstrings on `ng911_stack_panel.py` |
| 3 | Issue 6 | `cffconvert --validate` in CI |
| 4 | Issue 7 | `TROUBLESHOOTING.md` for PDF fetch |
| 5 | Issue 2 | Type hints on `ng911_extract_321_v2.py` |
| 6 | Issue 10 | `CONTRIBUTING.md` |

After month 6, continue with Issues 3, 5, 8, 9 or small fixes (typos, dependency pins, new report year).

## Cursor / agent prompt (copy each month)

Paste into Cursor with the repo open at `ng911-extract`:

```text
Monthly maintenance for wangtiankai/ng911-extract.

1. Read MAINTENANCE.md and BACKLOG.md.
2. Find the oldest open GitHub issue (gh issue list) or the next unchecked row in the schedule above.
3. Implement only that issue; run pytest tests/ -v.
4. Commit, push to origin main (or open a PR), close the issue, and open the next backlog issue for next month.
5. Summarize what shipped and the next issue number.
```

## What not to do

- Do not commit large binary PDFs, mock panels, or local-only notes (`PUSH_INSTRUCTIONS.md` is gitignored).
- Avoid multi-issue “mega” PRs; one issue per month is enough.
- Do not force-push `main`.

## Contacts

- **Source data:** U.S. National 911 Program, https://www.911.gov/
- **Profile Database access:** see README and NHTSA 911 Program (research requests).
