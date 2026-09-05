---
title: '`ng911-extract`: A reproducible pipeline for state-year Next Generation 911 deployment data from public Profile Database reports'
tags:
  - Python
  - public-safety
  - emergency-services
  - 911
  - data-extraction
  - panel-data
authors:
  - name: Tiankai Wang
    orcid: 0000-0003-0083-0218
    affiliation: 'Texas State University'
affiliations:
  - name: Texas State University
    index: 1
date: 2026-09-04
bibliography: paper.bib
---

# Summary

`ng911-extract` builds a state-by-year panel of Next Generation 911 (NG911) deployment milestones from the publicly distributed National 911 Profile Database Progress Reports. The U.S. National Highway Traffic Safety Administration stopped maintaining the Profile Database in 2024, but the underlying annual reports remain hosted at `911.gov` and on `data.transportation.gov` (Socrata ID `i5x2-a58r`). The pipeline ingests those PDFs, extracts the state-by-state NG911 Maturity Model grid (8 categories on a 0–6 ordinal scale) and the earlier 3.2.x Profile Database fields (statewide NG911 plan adoption, RFP release, percent population and geography served by NG911-capable services, operational ESInet count), and stacks them into a single tidy CSV at `data/ng911/state_ng911_panel.csv` with derived event-year columns. The pipeline is reproducible from publicly available source PDFs.

# Statement of need

Researchers studying the impact of NG911 modernization on emergency response times, road crash outcomes, or pre-hospital mortality need a multi-year state-level treatment variable. The Profile Database is the only systematic source, but its discontinuation left the data scattered across per-year PDF reports with two distinct schema generations (3.2.x for 2013–2016 data and the Maturity Model for 2018–2020 data). Re-extracting it requires manual PDF parsing with layout-specific code for both schemas. `ng911-extract` packages those routines and produces a single CSV that joins cleanly to FARS, FCC Form 477, FCC BDC, and USDA RUCC county-year panels for downstream event-study designs.

# Functionality

The pipeline comprises four scripts in `code/`:

1. `ng911_extract_321_v2.py` — parses the 4-column and 2-column "State Response" grids in the 2013–2016 Profile Database Progress Reports, plus the "100% of Field Served: AL, CA, ..." summary blocks for percent fields.
2. `ng911_extract_maturity.py` — parses the even-numbered state-value pages of the 2018–2020 reports, which carry the 8-category Maturity Model grid for 53–56 jurisdictions.
3. `ng911_stack_panel.py` — stacks per-year CSVs into the master `data/ng911/state_ng911_panel.csv` (392 rows = 56 jurisdictions × 7 years) and derives an `event_year` column equal to the first year any of the following fires: `ng911_rfp_released=Yes`, `n_operational_esinets ≥ 1`, or maturity `routing_location ≥ 2`.
4. `fetch_ng911_pdfs.py` — optional helper that downloads the eight Progress Report PDFs from `911.gov/assets/` to `data/ng911/raw_pdfs/`. Note that `911.gov` returns HTTP 403 to scripted clients because of Akamai fingerprinting; this script requires driving a Chromium instance with a fingerprint the edge accepts (Playwright works; `curl` and Tor SOCKS5 do not).

The package also includes the original kill-test event study and falsification scripts (`ng911_03_event_study.py`, `ng911_04_falsification.py`, `ng911_05_verdict.py`) for downstream users who want to reproduce the diagnostic battery.

# Quality control

The package was developed against the FARS 2015–2024 panel. The state-year panel covers 2013–2020 NG911 data (2017 was a survey suspension year; 2021 was a separate one-off report). Reproducing the master panel from `data/ng911/raw_pdfs/` takes under five seconds on a single core. Two schema-coverage gaps are documented:

- 2014, 2015, 2016 reports lack extractable state values for `ng911_plan_adopted` and `ng911_rfp_released` in their Appendix A repeats; the 2013 report has them.
- The 2010-data report uses a pre-3.2.x schema and is not extracted. It would only be useful as a 2010 control.

A worked downstream application is in `output/verdict_ng911.md`. Using 12 NG911-treated states (8 with 2018 milestone, 4 with 2020 milestone) joined to FARS 2015–2024 county-year data, a stacked event study with state-clustered standard errors yields a notification-time 2×2 DiD of −30.7 minutes (95% CI −110, +49; t = −0.76) and an urban falsification of +255 minutes (max |t| = 7.35). The urban falsification firing strongly is consistent with NG911 modernization being confounded with state-level reporting or measurement changes rather than a rural-specific dispatch improvement.

# Availability

The source code, the master panel CSV, and the eight source PDFs are archived together at the repository URL associated with this submission. The pipeline is implemented in Python 3.11 with `pypdf`, `pandas`, `numpy`, and `statsmodels` as the only non-stdlib dependencies.

# Acknowledgements

We thank the National 911 Program Office for publishing the underlying Progress Reports even after discontinuing curator support, and the JEMS archive for hosting earlier editions that remain accessible.

# References
