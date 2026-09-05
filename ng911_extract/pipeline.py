"""Public API: thin wrappers around the code/ scripts so the package is
importable as `ng911_extract` and the panel builder is testable without
shelling out to a subprocess.

The heavy lifting still lives in `code/ng911_*.py` so the existing scripts
remain runnable directly from the repo root.
"""

from __future__ import annotations

import csv
from pathlib import Path

PANEL_COLUMNS = [
    "state_fips", "state_abbr", "state_name", "year",
    "ng911_plan_adopted", "ng911_rfp_released",
    "pct_pop_served", "pct_geo_served",
    "n_esinet_psaps", "n_operational_esinets",
    "routing_location", "gis_data", "core_services", "network",
    "psap_call_handling", "security", "operations", "optional_interfaces",
    "event_year",
]


def load_panel(path: str | Path) -> list[dict]:
    """Load the master panel CSV as a list of dicts.

    Parameters
    ----------
    path : str or Path
        Path to `state_ng911_panel.csv`.

    Returns
    -------
    list of dict
        One dict per row; column names match PANEL_COLUMNS.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    with p.open() as f:
        return list(csv.DictReader(f))


def event_year_distribution(panel: list[dict]) -> dict[int | str, int]:
    """Return a count of how many distinct jurisdictions first 'treated' in each year.

    Jurisdictions with no event_year (empty string) are aggregated under the
    key '' for transparency.
    """
    counts: dict[int | str, int] = {}
    for r in panel:
        ey = r.get("event_year", "")
        key = int(ey) if ey else ""
        counts[key] = counts.get(key, 0) + 1
    return counts
