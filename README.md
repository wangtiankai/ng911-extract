# ng911-extract

Reproducible pipeline for state-by-year Next Generation 911 deployment data from public Profile Database Progress Reports.

## What it does

Ingests eight annual PDF reports hosted at `911.gov` (the U.S. National 911 Program), extracts the state-by-state NG911 deployment grid from each, and stacks them into a single tidy CSV at `data/ng911/state_ng911_panel.csv` (392 rows = 56 jurisdictions × 7 data years).

## Source reports

| Data year | File |
|---|---|
| 2010 | `data/ng911/raw_pdfs/2011_911_Profile_Database_RPT.pdf` (not extracted; pre-3.2.x schema) |
| 2013 | `data/ng911/raw_pdfs/2014_911_Profile_Database_RPT.pdf` |
| 2014 | `data/ng911/raw_pdfs/2015_911_Profile_Database_RPT.pdf` |
| 2015 | `data/ng911/raw_pdfs/2016_911_Profile_Database_RPT.pdf` |
| 2016 | `data/ng911/raw_pdfs/2017_911_Profile_Database_RPT.pdf` |
| 2018 | `data/ng911/raw_pdfs/2019_911_Profile_Database_RPT.pdf` |
| 2019 | `data/ng911/raw_pdfs/National_911_Annual_Report_2019_Data.pdf` |
| 2020 | `data/ng911/raw_pdfs/National_911_Annual_Report_2020_Data.pdf` |

## Pipeline

```bash
# 1. Extract per-year CSVs
python code/ng911_extract_321_v2.py    # 2013-2016 reports (3.2.x schema)
python code/ng911_extract_maturity.py  # 2018-2020 reports (Maturity Model)

# 2. Stack into master panel
python code/ng911_stack_panel.py
# -> data/ng911/state_ng911_panel.csv

# 3. (Optional) Downstream event study
python code/ng911_01_load_treatment.py
python code/ng911_03_event_study.py
python code/ng911_04_falsification.py
python code/ng911_05_verdict.py
```

## Reproducing the source PDFs

`911.gov` returns HTTP 403 to scripted clients (Akamai fingerprinting). Use Playwright driving Chromium through a session established on `https://www.911.gov/projects/national-911-annual-report/`. Raw `curl` and Tor SOCKS5 are blocked.

See `code/fetch_ng911_pdfs.py` for a reference implementation, and the in-session discussion in the JOSS paper for the workaround details.

## Master panel schema

`data/ng911/state_ng911_panel.csv`:

| Column | Type | Description |
|---|---|---|
| `state_fips` | str | 2-digit FIPS code |
| `state_abbr` | str | 2-letter postal abbreviation |
| `state_name` | str | Jurisdiction name |
| `year` | int | Data year (calendar year the report covers) |
| `ng911_plan_adopted` | str | Yes / No (2013 only) |
| `ng911_rfp_released` | str | Yes / No (2013 only) |
| `pct_pop_served` | float | 0–100 |
| `pct_geo_served` | float | 0–100 |
| `n_esinet_psaps` | int | Count |
| `n_operational_esinets` | int | Count |
| `routing_location` | int | Maturity Model level 0–6 (2018–2020) |
| `gis_data` | int | Maturity Model level 0–6 |
| `core_services` | int | Maturity Model level 0–6 |
| `network` | int | Maturity Model level 0–6 |
| `psap_call_handling` | int | Maturity Model level 0–6 |
| `security` | int | Maturity Model level 0–6 |
| `operations` | int | Maturity Model level 0–6 |
| `optional_interfaces` | int | Maturity Model level 0–6 |
| `event_year` | int | Derived: first year RFP released, ≥1 ESInet, or maturity ≥ Foundational |

## License

MIT for code; the underlying source PDFs are U.S. Government works and not subject to copyright in the United States.

## Citing

See `paper.bib` in the JOSS submission folder for the BibTeX entries.
