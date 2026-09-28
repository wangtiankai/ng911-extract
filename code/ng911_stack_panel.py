"""Stack per-year NG911 panels into one master panel.

Reads ``state_ng911_panel_<year>.csv`` files produced by the extractors and
writes ``data/ng911/state_ng911_panel.csv``.

Schema (master panel)
---------------------
- ``state_fips``, ``state_abbr``, ``state_name``, ``year``
- ``ng911_plan_adopted``, ``ng911_rfp_released`` (2013--2016 reports; Yes/No)
- ``pct_pop_served``, ``pct_geo_served`` (0--100 when present)
- ``n_esinet_psaps``, ``n_operational_esinets`` (counts)
- Maturity Model levels 0--6 (2018--2020): ``routing_location``, ``gis_data``,
  ``core_services``, ``network``, ``psap_call_handling``, ``security``,
  ``operations``, ``optional_interfaces``
- ``event_year``: first calendar year any adoption signal fires for the state
  (see ``derive_event_year``); blank on pre-treatment rows and when no signal
  ever fires
"""

from __future__ import annotations

import collections
import csv
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "ng911"

YEARS = [2013, 2014, 2015, 2016, 2018, 2019, 2020]

ABBR = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC",
    "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT",
    "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
    "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY",
}

KEYS = [
    "ng911_plan_adopted",
    "ng911_rfp_released",
    "pct_pop_served",
    "pct_geo_served",
    "n_esinet_psaps",
    "n_operational_esinets",
    "routing_location",
    "gis_data",
    "core_services",
    "network",
    "psap_call_handling",
    "security",
    "operations",
    "optional_interfaces",
]


def load_by_year(data_dir: Path, years: list[int]) -> dict[int, dict[str, dict[str, str]]]:
    """Load per-year extractor CSVs indexed by ``state_fips``."""
    by_year: dict[int, dict[str, dict[str, str]]] = {}
    for yr in years:
        path = data_dir / f"state_ng911_panel_{yr}.csv"
        with path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        by_year[yr] = {r["state_fips"]: r for r in rows}
    return by_year


def build_master_rows(
    by_year: dict[int, dict[str, dict[str, str]]],
    years: list[int],
) -> tuple[list[dict[str, Any]], list[str]]:
    """One row per state-year; missing years get blank NG911 fields."""
    all_fips: set[str] = set()
    for yr in years:
        all_fips |= set(by_year[yr].keys())
    fips_sorted = sorted(all_fips)

    master: list[dict[str, Any]] = []
    for fips in fips_sorted:
        abbr = ABBR.get(fips, "")
        name = ""
        for yr in years:
            if fips in by_year[yr]:
                name = by_year[yr][fips].get("state_name", "")
                if name:
                    break
        for yr in years:
            row = by_year[yr].get(fips)
            if row is None:
                row = {"state_fips": fips, "state_name": name, "year": str(yr)}
            out: dict[str, Any] = {
                "state_fips": fips,
                "state_abbr": abbr,
                "state_name": name,
                "year": yr,
            }
            for k in KEYS:
                v = row.get(k, "")
                out[k] = "" if v in (None, "None") else v
            master.append(out)
    return master, fips_sorted


def row_triggers_event_year(row: dict[str, Any]) -> bool:
    """Return True if this state-year row satisfies any adoption milestone.

    The three signals are intentionally OR-ed (not equivalent):

    1. ``ng911_rfp_released == 'Yes'`` — state issued an NG911 RFP.
    2. ``n_operational_esinets >= 1`` — at least one operational ESInet.
    3. ``routing_location >= 2`` — Maturity Model at Foundational or above.

    Any one is enough to mark the year as the state's first treated period.
    """
    if row.get("ng911_rfp_released") == "Yes":
        return True
    if row.get("n_operational_esinets") not in ("", "0", "0.0", None):
        try:
            if float(row["n_operational_esinets"]) >= 1:
                return True
        except ValueError:
            pass
    try:
        if int(row.get("routing_location") or 0) >= 2:
            return True
    except ValueError:
        pass
    return False


def derive_event_year(master: list[dict[str, Any]], fips_list: list[str]) -> dict[str, int | str]:
    """First calendar year (ascending) when any milestone fires for each state.

    Scans ``master`` in row order (state blocks sorted by year). The first
    triggering year wins; later stronger signals do not move ``event_year``.
    """
    event_year: dict[str, int | str] = {}
    for fips in fips_list:
        ey: int | str = ""
        for row in master:
            if row["state_fips"] != fips:
                continue
            if row_triggers_event_year(row):
                ey = row["year"]
                break
        event_year[fips] = ey
    return event_year


def attach_event_year(
    master: list[dict[str, Any]],
    event_year: dict[str, int | str],
) -> None:
    """Set ``event_year`` on each row.

    Pre-treatment rows (year before the state's first trigger) get a blank
    ``event_year`` so stacked event studies never use negative relative time
    from a future treatment date.
    """
    for row in master:
        ey = event_year[row["state_fips"]]
        if ey == "" or int(row["year"]) >= int(ey):
            row["event_year"] = ey
        else:
            row["event_year"] = ""


def write_master_panel(master: list[dict[str, Any]], out_path: Path) -> None:
    """Write the stacked panel CSV."""
    fieldnames = ["state_fips", "state_abbr", "state_name", "year"] + KEYS + ["event_year"]
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(master)


def print_event_year_summary(event_year: dict[str, int | str], fips_list: list[str]) -> None:
    """Print a frequency table of derived event years to stdout."""
    counts = collections.Counter(str(event_year[fips]) for fips in fips_list)
    print("event_year distribution:")
    for k in sorted(counts.keys(), key=lambda x: (x == "", x)):
        print(f"  {k}: {counts[k]}")


def main() -> None:
    by_year = load_by_year(DATA_DIR, YEARS)
    master, fips_list = build_master_rows(by_year, YEARS)
    ey_map = derive_event_year(master, fips_list)
    attach_event_year(master, ey_map)

    out_path = DATA_DIR / "state_ng911_panel.csv"
    write_master_panel(master, out_path)
    print(f"wrote {out_path}: {len(master)} rows, {len(fips_list)} states")
    print()
    print_event_year_summary(ey_map, fips_list)


if __name__ == "__main__":
    main()
