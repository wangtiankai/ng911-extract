"""Smoke tests for the ng911-extract master panel.

Run from the repository root:

    pytest tests/

or directly:

    python tests/test_panel.py
"""
from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
PANEL_PATH = ROOT / "data" / "ng911" / "state_ng911_panel.csv"

EXPECTED_COLUMNS = {
    "state_fips", "state_abbr", "state_name", "year",
    "ng911_plan_adopted", "ng911_rfp_released",
    "pct_pop_served", "pct_geo_served",
    "n_esinet_psaps", "n_operational_esinets",
    "routing_location", "gis_data", "core_services", "network",
    "psap_call_handling", "security", "operations", "optional_interfaces",
    "event_year",
}

EXPECTED_YEARS = {2013, 2014, 2015, 2016, 2018, 2019, 2020}
EXPECTED_FIPS_SAMPLE = {"01", "06", "12", "48", "56"}  # AL, CA, FL, TX, WY
MIN_ROWS = 350   # 50 states x 7 years = 350; territories add a bit more
MAX_ROWS = 420


def _load_panel() -> list[dict]:
    if not PANEL_PATH.exists():
        raise FileNotFoundError(
            f"Master panel not found at {PANEL_PATH}. "
            "Run the pipeline first: python code/ng911_stack_panel.py"
        )
    with PANEL_PATH.open() as f:
        return list(csv.DictReader(f))


def test_panel_exists():
    """Master panel CSV exists at the expected path."""
    assert PANEL_PATH.exists(), f"missing {PANEL_PATH}"


def test_panel_columns():
    """Columns match the documented schema exactly."""
    rows = _load_panel()
    assert rows, "panel is empty"
    actual = set(rows[0].keys())
    missing = EXPECTED_COLUMNS - actual
    extra = actual - EXPECTED_COLUMNS
    assert not missing, f"missing columns: {sorted(missing)}"
    assert not extra, f"unexpected columns: {sorted(extra)}"


def test_panel_shape():
    """Row count is between 350 (50 states x 7 years) and 420 (56 jurisdictions x 7 years)."""
    rows = _load_panel()
    n = len(rows)
    assert MIN_ROWS <= n <= MAX_ROWS, f"row count {n} outside [{MIN_ROWS}, {MAX_ROWS}]"


def test_panel_years():
    """Panel covers the expected data years."""
    rows = _load_panel()
    years = {int(r["year"]) for r in rows}
    assert EXPECTED_YEARS.issubset(years), f"missing years: {EXPECTED_YEARS - years}"


def test_state_fips_format():
    """state_fips is a 2-character string (with leading zero where needed)."""
    rows = _load_panel()
    for r in rows:
        fips = r["state_fips"]
        assert len(fips) == 2 and fips.isdigit(), f"bad fips: {fips!r}"


def test_sample_states_present():
    """A handful of canonical state FIPS codes appear in the panel."""
    rows = _load_panel()
    fips = {r["state_fips"] for r in rows}
    missing = EXPECTED_FIPS_SAMPLE - fips
    assert not missing, f"sample states missing: {sorted(missing)}"


def test_maturity_levels_in_range():
    """Maturity Model fields are integers in [0, 6] when present."""
    rows = _load_panel()
    cats = [
        "routing_location", "gis_data", "core_services", "network",
        "psap_call_handling", "security", "operations", "optional_interfaces",
    ]
    for r in rows:
        for c in cats:
            v = r[c]
            if v == "" or v is None:
                continue
            try:
                fv = int(v)
            except ValueError:
                raise AssertionError(f"non-integer maturity value: {c}={v!r}")
            assert 0 <= fv <= 6, f"maturity out of range: {c}={fv}"


def test_pct_fields_in_range():
    """pct_pop_served and pct_geo_served are in [0, 100] when present."""
    rows = _load_panel()
    for r in rows:
        for c in ("pct_pop_served", "pct_geo_served"):
            v = r[c]
            if v == "" or v is None:
                continue
            fv = float(v)
            assert 0 <= fv <= 100, f"pct out of range: {c}={fv}"


def test_event_year_consistent():
    """event_year is either empty or a 4-digit year in EXPECTED_YEARS."""
    rows = _load_panel()
    for r in rows:
        ey = r["event_year"]
        if ey == "":
            continue
        yi = int(ey)
        assert yi in EXPECTED_YEARS, f"unexpected event_year: {ey}"


def test_event_year_within_year_range():
    """If event_year is set on a row, year >= event_year. Pre-treatment rows
    for a state carry an empty event_year, so the comparison is well-defined."""
    rows = _load_panel()
    for r in rows:
        ey = r["event_year"]
        if ey == "":
            continue
        assert int(ey) <= int(r["year"]), (
            f"event_year {ey} after year {r['year']} for fips {r['state_fips']}"
        )


if __name__ == "__main__":
    # Allow direct invocation without pytest.
    failures = []
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS {name}")
            except AssertionError as e:
                failures.append((name, str(e)))
                print(f"  FAIL {name}: {e}")
            except FileNotFoundError as e:
                failures.append((name, str(e)))
                print(f"  FAIL {name}: {e}")
    if failures:
        print(f"\n{len(failures)} failure(s)")
        sys.exit(1)
    print("\nAll smoke tests passed.")
