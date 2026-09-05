# Backlog of "good first issues"

Ten issues to open against the `wangtiankai/ng911-extract` repo over the next six months. Each one is tied to a real, narrow gap in the current codebase. Open them one at a time, work them, close them. JOSS reviewers will see the steady activity.

Each issue is ready to copy into a GitHub issue. Suggested labels: `good first issue`, `documentation`, `tests`, or `enhancement` as marked.

---

## Issue 1 — Add function-level docstrings to `code/ng911_stack_panel.py`

**Labels:** `good first issue`, `documentation`

**Body:**

The module has a top-level docstring but the inline logic — particularly the `event_year` derivation loop — has no inline comments explaining what each branch does. A new reader cannot follow why `n_operational_esinets >= 1` is OR-ed with `routing_location >= 2` rather than treated as equivalent.

Please add:
1. A docstring to any helper functions or inline-commented blocks.
2. A short comment explaining the priority order: the loop scans years ascending and triggers on the first year any of the three signals fires.
3. Update the module docstring's "Schema" section if anything is now stale.

Acceptance: a reader unfamiliar with NG911 terminology can read `ng911_stack_panel.py` top-to-bottom without opening any other file.

---

## Issue 2 — Add type hints to `code/ng911_extract_321_v2.py`

**Labels:** `good first issue`, `enhancement`

**Body:**

The module currently has zero function signatures with type annotations. Three public functions would benefit: `find_data_page(r, sec_pat, head_pat)`, `parse_grid(text, value_format)`, and `normalize(val, fmt)`.

Please add `from __future__ import annotations` at the top of the file and annotate:
- `find_data_page`: `(r: pypdf.PdfReader, sec_pat: str, head_pat: str) -> tuple[str | None, int | None]`
- `parse_grid`: `(text: str, value_format: str) -> dict[str, str]`
- `normalize`: `(val: str | None, fmt: str) -> str | float | int | None`

Run the existing extraction afterwards and confirm the per-year CSVs are byte-identical to the current ones (diff against `git HEAD`).

---

## Issue 3 — Add type hints to `code/ng911_extract_maturity.py`

**Labels:** `good first issue`, `enhancement`

**Body:**

Same as Issue 2 but for the Maturity Model extractor. Two public items to annotate:
- the `NAME_RE` regex (already typed as `re.Pattern[str]` via the constructor)
- any top-level helper that gets introduced if you refactor the value-page loop into a function

The current loop inlines the `(one_based, cat)` zip-and-iterate; pulling it into a function with a typed signature will make the per-page extraction testable in isolation (see Issue 5).

---

## Issue 4 — Write a unit test for `parse_grid` in `tests/`

**Labels:** `good first issue`, `tests`

**Body:**

`tests/test_panel.py` currently only tests the assembled master panel. The extractors in `code/` have no test coverage, so any regression in `parse_grid` or `find_data_page` would only surface as a silent diff in the per-year CSV.

Add `tests/test_extract.py` with at least:
1. A fixture that holds a representative text snippet from page 125 of the 2013 Progress Report (the 4-column grid for `3.2.1.1 Statewide NG911 Plan Adopted`).
2. `test_parse_grid_4col` asserting that `'AK', 'No', 'GU', 'Yes', 'ME', 'Yes', 'OK', 'No'` parses to `{'AK': 'No', 'GU': 'Yes', 'ME': 'Yes', 'OK': 'No'}`.
3. `test_parse_grid_summary_block` asserting the `"100% of Geographic Area Served: AL, CA, ..."` summary block contributes states with value `'100'`.
4. `test_parse_grid_2col` for the 2014+ reports using a representative two-column snippet from page 74 of `2015_911_Profile_Database_RPT.pdf`.

Run with `pytest tests/ -v` and confirm all new tests pass.

---

## Issue 5 — Parameterize the Maturity Model page indices

**Labels:** `good first issue`, `enhancement`

**Body:**

In `code/ng911_extract_maturity.py`, the per-PDF list of state-value pages is hard-coded:

```python
('2019_911_Profile_Database_RPT.pdf', 2018, [74, 76, 78, 80, 82, 84, 86, 88]),
('National_911_Annual_Report_2020_Data.pdf', 2020, [69, 71, 73, 75, 77, 79, 81, 83]),
```

Add a function `find_maturity_value_pages(r: pypdf.PdfReader) -> list[int]` that scans every page, identifies the ones containing both the maturity-level legend (`Jurisdictional End State`) and a state-name list (`Alabama`, `Alaska`, ...), and returns their 1-based page numbers. The hard-coded lists should become a sanity-check in `if __name__ == "__main__":` rather than the source of truth.

This makes the extractor robust to 2021, 2022, ... reports without manual maintenance.

---

## Issue 6 — Add `CITATION.cff` ORCID validation in CI

**Labels:** `good first issue`, `tests`

**Body:**

The repo's CI runs pytest on three Python versions but does not lint the metadata files. JOSS reviewers sometimes flag invalid ORCID or repository URLs.

Add a step to `.github/workflows/test.yml` after the pytest step:

```yaml
      - name: Validate CITATION.cff
        run: |
          pip install cffconvert
          cffconvert --validate
```

This requires `cffconvert` to be installed. If it complains, fix the underlying YAML — common fixes are unquoted URLs or missing version keys.

---

## Issue 7 — Document the `fetch_ng911_pdfs.py` workaround in a TROUBLESHOOTING.md

**Labels:** `good first issue`, `documentation`

**Body:**

`code/fetch_ng911_pdfs.py` is a reference implementation, but anyone who runs it as-is will hit HTTP 403 from `911.gov`'s Akamai edge. The README mentions this in one paragraph; a new user will not know what to do next.

Add `TROUBLESHOOTING.md` at the repo root with:
1. **Why the script fails for you.** Akamai inspects the TLS ClientHello; raw `curl` and Tor SOCKS5 are both blocked.
2. **What works.** Playwright driving Chromium through an established session on `911.gov`. Show the minimal in-page `fetch()` snippet.
3. **Where the PDFs are mirrored.** Note the JEMS archive at `https://www.jems.com/wp-content/uploads/2019/12/National-911-Program-Profile-Database-Progress-Report-2019.pdf` for the 2018-data report specifically.
4. **A pre-bundled fallback.** Note that the repo already includes all 8 PDFs in `data/ng911/raw_pdfs/` so first-time users do not need to download anything.

---

## Issue 8 — Add a `make` target or `tox.ini` for end-to-end pipeline run

**Labels:** `good first issue`, `enhancement`

**Body:**

The pipeline currently requires four commands in sequence. New users will not know the order.

Add a `Makefile` at the repo root:

```make
.PHONY: extract stack test

extract:
	python code/ng911_extract_321_v2.py
	python code/ng911_extract_maturity.py

stack:
	python code/ng911_stack_panel.py

test:
	pytest tests/ -v

all: extract stack test
```

A Windows user without `make` should be able to fall back to running the four commands directly; mention `make` is for Unix shells in the README.

---

## Issue 9 — Surface the `event_year` distribution on `ng911_extract.load_panel`

**Labels:** `good first issue`, `enhancement`

**Body:**

`ng911_extract/pipeline.py` already has `event_year_distribution(panel)`. It currently returns a dict but does not print. Add a small helper `summarize_panel(path: str | Path) -> dict` that loads the panel and returns a summary dict with: row count, distinct state_fips, distinct years, and the event_year distribution. Then add `__main__` so `python -m ng911_extract.pipeline /path/to/state_ng911_panel.csv` prints the summary.

Acceptance: running `python -m ng911_extract.pipeline data/ng911/state_ng911_panel.csv` prints a one-screen summary that a non-author can read to understand the panel shape.

---

## Issue 10 — Add a CONTRIBUTING.md

**Labels:** `good first issue`, `documentation`

**Body:**

JOSS reviewers look for a CONTRIBUTING file. The repo does not have one.

Add `CONTRIBUTING.md` at the repo root with:
1. **Setup.** `git clone`, `pip install -e .[dev]` (or `pip install pypdf pandas numpy statsmodels pytest`), `pytest tests/`.
2. **Branch and PR conventions.** Branch from `main`, name like `fix/parse-grid-empty-summary` or `feat/type-hints-extract`, open a PR that runs CI green.
3. **Coding style.** PEP 8, type hints on new code, docstrings on new public functions.
4. **Adding a new data year.** Document the steps to extend coverage: download the PDF, identify the schema (3.2.x vs Maturity Model), run the appropriate extractor, add the year to the stacker, update `tests/test_panel.py` to expect the new year.
5. **Reporting issues.** What to include: PDF filename, page number, expected vs actual behavior, raw text snippet.

---

# How to use this backlog

Suggested cadence: open one issue every 2–3 weeks, work it for 1–2 hours, push, close. Over six months that yields ten issue-open events and ten issue-close events. Each PR also creates a commit and a code-review event. Combined, this looks like steady maintenance rather than a single burst.

The earliest issue to open is **Issue 4** (unit test for `parse_grid`), because it can be done in one sitting and immediately increases the test count, which JOSS reviewers see in the CI badge. Issues 2, 3, 6, 9 are mechanical and good for low-energy days. Issues 1, 7, 10 are documentation and good for when you want to think but not code. Issues 5, 8 are slightly larger and should be saved for when you have a chunk of time.

If you want me to pre-fill Issue 4 with the actual page-125 text snippet, say so — it's tedious to copy by hand.
