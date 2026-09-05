"""Falsification battery for NG911 event study.

Restricts to the 2018 and 2020 treatment cohorts (only ones with full FARS
coverage in event_time ∈ [-3, +4]).

  1. Crash incidence falsification: NG911 should NOT change crash counts.
  2. Urban falsification: rural-only specification should produce null
     effects in metro counties.
  3. 2024-drop sensitivity: drop 2024 and re-run.

Each falsification writes its own CSV to output/tables/.
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path

if not Path("output/ng911_panel.parquet").exists():
    raise SystemExit("ng911_panel.parquet missing; run code/ng911_01_load_treatment.py first")

p = pd.read_parquet("output/ng911_panel.parquet")
# Restrict to 2018 and 2020 treatment cohorts (only ones with full FARS coverage)
p = p[p["treatment_year"].isin([2018.0, 2020.0])].copy()
p = p.dropna(subset=["treatment_year", "event_time"])

# Event-time bins covered by both cohorts: [-3, +4]
BINS = list(range(-3, 5))

def run_event_study(df, outcome_col, weight_col="n_crashes"):
    df = df.copy()
    df["et"] = pd.Categorical(df["event_time"], categories=BINS, ordered=False)
    dummies = pd.get_dummies(df["et"], prefix="et", drop_first=False).astype(float).drop(columns=["et_-1"])
    state_dum = pd.get_dummies(df["state_fips"].astype(str), prefix="st", drop_first=True)
    year_dum = pd.get_dummies(df["year"].astype(str), prefix="yr", drop_first=True)
    X = pd.concat([dummies, state_dum, year_dum], axis=1).astype(float)
    X = sm.add_constant(X)
    y = df[outcome_col].fillna(0).values
    if isinstance(weight_col, str):
        w = (df[weight_col].fillna(0) + 1).values
    else:
        w = np.full(len(df), float(weight_col) + 1 if weight_col else 1.0)
    m = sm.WLS(y, X, weights=w).fit(
        cov_type="cluster", cov_kwds={"groups": df["state_fips"].astype(str).values}
    )
    rows = []
    for k in BINS:
        if k == -1:
            rows.append({"event_time": k, "coef": 0.0, "se": 0.0, "ci_lo": 0.0, "ci_hi": 0.0})
        else:
            key = f"et_{k}"
            if key in m.params:
                c, s = m.params[key], m.bse[key]
                rows.append({"event_time": k, "coef": c, "se": s, "ci_lo": c - 1.96*s, "ci_hi": c + 1.96*s})
            else:
                rows.append({"event_time": k, "coef": np.nan, "se": np.nan, "ci_lo": np.nan, "ci_hi": np.nan})
    return pd.DataFrame(rows)


# Falsification 1: crash count (log), restricted to non-zero-crash cells
p["log_crashes"] = np.log(p["n_crashes"].fillna(0).clip(lower=1))
p_nonzero = p[p["n_crashes"] > 0].copy()
print(f"non-zero-crash cells: {len(p_nonzero)}")
es_crashcount = run_event_study(p_nonzero, "log_crashes", weight_col=0)
print("=== FALSIFICATION 1: log crash count (non-zero-crash cells) ===")
print(es_crashcount.to_string(index=False))

# Falsification 2: urban subsample
if "rucc" in p.columns:
    p_urban = p[(p["rucc"] <= 3)].copy()
    print(f"\nurban counties in falsification: {p_urban['county_id'].nunique()}")
    es_urban = run_event_study(p_urban, "mean_not_min")
    print("=== FALSIFICATION 2: urban only (notification) ===")
    print(es_urban.to_string(index=False))
else:
    print("RUCC not available; skipping urban falsification")
    es_urban = pd.DataFrame(columns=["event_time","coef","se","ci_lo","ci_hi"])

# Falsification 3: drop 2024
p_no24 = p[p["year"] != 2024].copy()
es_no24 = run_event_study(p_no24, "mean_not_min")
print("=== FALSIFICATION 3: drop 2024 ===")
print(es_no24.to_string(index=False))

Path("output/tables").mkdir(parents=True, exist_ok=True)
es_crashcount.to_csv("output/tables/ng911_falsif_crashcount.csv", index=False)
es_urban.to_csv("output/tables/ng911_falsif_urban.csv", index=False)
es_no24.to_csv("output/tables/ng911_falsif_no_2024.csv", index=False)

def post_avg(es):
    post = es[(es["event_time"] > -1) & es["coef"].notna()]
    return post["coef"].mean() if len(post) else np.nan

def post_max_t(es):
    post = es[(es["event_time"] > -1) & es["coef"].notna() & (es["se"] > 0)]
    return (post["coef"] / post["se"]).abs().max() if len(post) else np.nan

print()
print("=== SUMMARY ===")
print(f"crash-count post avg: {post_avg(es_crashcount):.4f}, max |t|: {post_max_t(es_crashcount):.2f}")
if len(es_urban):
    print(f"urban notification post avg: {post_avg(es_urban):.2f}, max |t|: {post_max_t(es_urban):.2f}")
print(f"no-2024 notification post avg: {post_avg(es_no24):.2f}, max |t|: {post_max_t(es_no24):.2f}")
print("\nPASS criteria: crash-count effect ~0, urban effect ~0, no-2024 effect close to main.")
