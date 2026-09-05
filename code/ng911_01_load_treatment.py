"""Load state-year NG911 panel and merge onto FARS county-year panel.

Treatment: first year state has operational ESInet (state_ng911_panel_mock.csv or real).

Reads:
- data/ng911/state_ng911_panel_<source>.csv (mock or real)
- output/fars_clean.parquet (already built)

Writes:
- output/ng911_panel.parquet with columns
    state, county_id, year, mean_not_min, n_crashes, n_fatalities,
    treatment_year, event_time, rural

The pipeline mirrors code/04_event_study.py but uses state-year treatment
instead of county-year treatment. Unit of analysis is county-year within a state,
clustered at state level.
"""
import pandas as pd
import numpy as np
from pathlib import Path

# Pick the source: real if present, else mock
real_path = Path("data/ng911/state_ng911_panel.csv")
mock_path = Path("data/ng911/state_ng911_panel_mock.csv")

if real_path.exists():
    print(f"Using real NG911 panel: {real_path}")
    treatment = pd.read_csv(real_path)
elif mock_path.exists():
    print(f"Using mock NG911 panel: {mock_path} (waiting for real data)")
    treatment = pd.read_csv(mock_path)
else:
    raise SystemExit("no NG911 panel found; run code/ng911_make_mock.py or wait for Profile Database")

# Required columns: state_fips, event_year
print(f"treatment rows: {len(treatment)}, columns: {treatment.columns.tolist()}")
assert "state_fips" in treatment.columns, "missing state_fips column"
assert "event_year" in treatment.columns, "missing event_year column"

# FARS
fars = pd.read_parquet("output/fars_clean.parquet")
print(f"FARS rows: {len(fars):,}")

# Crash aggregation to county-year
crash_panel = (
    fars.groupby(["state_fips", "county_id", "year"])
    .agg(
        n_crashes=("case_no", "count"),
        n_fatalities=("fatalities", "sum"),
        mean_not_min=("notif_min", lambda x: x[x.between(1, 1439)].mean()),
    )
    .reset_index()
)

# Full grid
all_years = list(range(2015, 2026))
all_counties = crash_panel["county_id"].unique()
grid = pd.MultiIndex.from_product(
    [all_counties, all_years], names=["county_id", "year"]
).to_frame(index=False)
# Recover state_fips from county_id (county_id // 1000)
grid["state_fips"] = grid["county_id"] // 1000

panel = grid.merge(crash_panel, on=["state_fips", "county_id", "year"], how="left")
panel[["n_crashes", "n_fatalities"]] = panel[["n_crashes", "n_fatalities"]].fillna(0)

# Merge treatment
panel = panel.merge(
    treatment[["state_fips", "event_year"]].rename(columns={"event_year": "treatment_year"}),
    on="state_fips", how="left"
)

# Restrict to states with a defined treatment year in 2014-2020 (so we have pre/post windows of FARS data 2015-2024)
panel = panel[panel["treatment_year"].between(2014, 2020)].copy()

# Event time
panel["event_time"] = panel["year"] - panel["treatment_year"]
panel = panel[panel["event_time"].between(-5, 5)].copy()

# Rural flag (use RUCC if available), but DON'T restrict — keep all counties for urban falsification
rucc_path = Path("data/rucc_2013.csv")
if rucc_path.exists():
    rucc = pd.read_csv(rucc_path)
    panel = panel.merge(rucc, on="county_id", how="left")
    panel["rural"] = ((panel["rucc"] >= 4) & (panel["density"] < 500)).astype(int)
    print(f"rural counties: {panel[panel['rural']==1]['county_id'].nunique()}, urban counties: {panel[panel['rural']==0]['county_id'].nunique()}")

# Save
Path("output").mkdir(exist_ok=True)
panel.to_parquet("output/ng911_panel.parquet", index=False)
print(f"\nwrote output/ng911_panel.parquet with {len(panel):,} county-years")
print(f"treatment years: {sorted(panel['treatment_year'].unique())}")
print(f"event-time distribution:")
print(panel.groupby("event_time").size())