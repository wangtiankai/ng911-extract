"""Unit tests for PDF grid parsing in code/ng911_extract_321_v2.py."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))

from ng911_extract_321_v2 import parse_grid  # noqa: E402

# Minimal page fragment mimicking 2013 Progress Report, 3.2.1.1 grid (4-column).
SNIPPET_4COL = """
3.2.1.1 Statewide NG911 Plan Adopted
State Response State Response State Response State Response
AK No ME Yes OK No AL No
AL No IA Yes MI No OR Yes
"""

# 2014+ two-column "State Response (%)" layout.
SNIPPET_2COL = """
3.2.2.1 Statewide Request for Proposal
State Response (%) State Response (%)
AL 12 AK 0
CA 45 CO 8
"""

# Summary block for percentage fields (states at 100% geographic coverage).
SNIPPET_SUMMARY_PCT = """
3.2.3.3 Percentage of Geographical Area Served by NG911
State Response State Response State Response State Response
AK 10
100% of Geographic Area Served: AL, CA, TX
"""


def test_parse_grid_4col():
    out = parse_grid(SNIPPET_4COL, "yn")
    # First data row (2013 report layout); territories like GU are outside ABBR_TO_FIPS.
    assert out["AK"] == "No"
    assert out["ME"] == "Yes"
    assert out["OK"] == "No"
    assert out["AL"] == "No"
    assert out["IA"] == "Yes"
    assert out["MI"] == "No"
    assert out["OR"] == "Yes"


def test_parse_grid_2col():
    out = parse_grid(SNIPPET_2COL, "pct")
    assert out["AL"] == "12"
    assert out["AK"] == "0"
    assert out["CA"] == "45"
    assert out["CO"] == "8"


def test_parse_grid_summary_block():
    out = parse_grid(SNIPPET_SUMMARY_PCT, "pct")
    assert out["AL"] == "100"
    assert out["CA"] == "100"
    assert out["TX"] == "100"
    assert out["AK"] == "10"
