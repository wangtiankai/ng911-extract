"""Stacked event study for NG911 ESInet operational milestone.

Reads:
- output/ng911_panel.parquet

Writes:
- output/tables/ng911_event_study_notif.csv
- output/tables/ng911_event_study_fatal.csv

Specifications:
1. Event study (drop empty event-time bins): y_{cst} = Σ_{k≠-1} β_k · 1[et=k]
   + α_s + δ_t + ε_{cst}, SEs clustered at state.
2. Simple 2x2: y_{cst} = β · Treated_s · Post_t + α_s + δ_t + ε_{cst}.
   This is the kill-test primary spec — robust to sparse cohort event-time bins.
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path

if not Path("output/ng911_panel.parquet").exists():
    raise SystemExit("ng911_panel.parquet missing; run code/ng911_01_load_treatment.py first")

p = pd.read_parquet("output/ng911_panel.parquet")
print(f"county-years: {len(p):,}")
print(f"states: {p['state_fips'].nunique()}")
print(f"treatment_years: {sorted(p['treatment_year'].dropna().unique())}")
print(f"event_time range: [{p['event_time'].min()}, {p['event_time'].max()}]")

# Restrict to treatment years with full FARS coverage: 2018 and 2020.
# (Earlier years need pre-period < 2015; later years need post-period > 2024.)
p = p[p["treatment_year"].isin([2018.0, 2020.0])].copy()
p = p.dropna(subset=["treatment_year", "event_time"])
print(f"\nafter cohort restriction: {len(p):,} county-years, {p['state_fips'].nunique()} states")

# Keep event_time bins covered by BOTH cohorts (else the bin is unidentifiable).
# 2018 cohort: event_time ∈ [-3, +5] (years 2015-2023); 2020 cohort: [-5, +4] (years 2015-2024).
# Intersection: [-3, +4].
bins = list(range(-3, 5))
p["et"] = pd.Categorical(p["event_time"], categories=bins, ordered=False)
dummies = pd.get_dummies(p["et"], prefix="et", drop_first=False).astype(float).drop(columns=["et_-1"])
state_dum = pd.get_dummies(p["state_fips"].astype(str), prefix="st", drop_first=True)
year_dum = pd.get_dummies(p["year"].astype(str), prefix="yr", drop_first=True)
X_es = pd.concat([dummies, state_dum, year_dum], axis=1).astype(float)
X_es = sm.add_constant(X_es)

w = (p["n_crashes"] + 1).values

results = {}

def extract_event_study(model, label):
    rows = []
    for k in bins:
        if k == -1:
            rows.append({"event_time": k, "coef": 0.0, "se": 0.0, "ci_lo": 0.0, "ci_hi": 0.0})
        else:
            key = f"et_{k}"
            if key in model.params:
                c, s = model.params[key], model.bse[key]
                rows.append({"event_time": k, "coef": c, "se": s, "ci_lo": c - 1.96*s, "ci_hi": c + 1.96*s})
            else:
                rows.append({"event_time": k, "coef": np.nan, "se": np.nan, "ci_lo": np.nan, "ci_hi": np.nan})
    return pd.DataFrame(rows)

# Primary: notification time (rural counties)
y_notif = p["mean_not_min"].fillna(0).values
m_notif = sm.WLS(y_notif, X_es, weights=w).fit(
    cov_type="cluster", cov_kwds={"groups": p["state_fips"].astype(str).values}
)
es_notif = extract_event_study(m_notif, "notif")
results["notif"] = es_notif

# Secondary: fatality rate (per crash)
y_fatal = (p["n_fatalities"] / p["n_crashes"].clip(lower=1)).fillna(0).values
m_fatal = sm.WLS(y_fatal, X_es, weights=w).fit(
    cov_type="cluster", cov_kwds={"groups": p["state_fips"].astype(str).values}
)
es_fatal = extract_event_study(m_fatal, "fatal")
results["fatal"] = es_fatal

Path("output/tables").mkdir(parents=True, exist_ok=True)
es_notif.to_csv("output/tables/ng911_event_study_notif.csv", index=False)
es_fatal.to_csv("output/tables/ng911_event_study_fatal.csv", index=False)

post = es_notif[es_notif["event_time"] > -1]
post_avg = post["coef"].mean()
post_se = np.sqrt((post["se"] ** 2).sum()) / len(post)

print("\n=== EVENT STUDY: mean notification minutes (rural counties) ===")
print(es_notif.to_string(index=False))
print(f"\nPost-period avg (event_time>-1): {post_avg:.2f}  se={post_se:.2f}  95% CI=({post_avg - 1.96*post_se:.2f}, {post_avg + 1.96*post_se:.2f})")

print("\n=== EVENT STUDY: fatality rate ===")
print(es_fatal.to_string(index=False))

# 2x2 DiD: Treated x Post
post_years = {2018.0: [2018, 2019, 2020, 2021, 2022, 2023, 2024],
              2020.0: [2020, 2021, 2022, 2023, 2024]}
p["post"] = p.apply(lambda r: int(r["year"] in post_years.get(r["treatment_year"], [])), axis=1)
p["treated_x_post"] = (p["treatment_year"].notna().astype(int) * p["post"]).astype(float)
state_dum_d = pd.get_dummies(p["state_fips"].astype(str), prefix="st", drop_first=True)
year_dum_d = pd.get_dummies(p["year"].astype(str), prefix="yr", drop_first=True)
X_did = pd.concat([p[["treated_x_post"]], state_dum_d, year_dum_d], axis=1).astype(float)
X_did = sm.add_constant(X_did)
m_did_notif = sm.WLS(y_notif, X_did, weights=w).fit(
    cov_type="cluster", cov_kwds={"groups": p["state_fips"].astype(str).values}
)
m_did_fatal = sm.WLS(y_fatal, X_did, weights=w).fit(
    cov_type="cluster", cov_kwds={"groups": p["state_fips"].astype(str).values}
)

print("\n=== 2x2 DiD: Treated x Post ===")
for label, m, y in [("notification_min", m_did_notif, y_notif), ("fatality_rate", m_did_fatal, y_fatal)]:
    c = m.params["treated_x_post"]; s = m.bse["treated_x_post"]
    print(f"  {label:20s} coef={c:8.3f}  se={s:8.3f}  t={c/s:6.2f}  95% CI=({c-1.96*s:.3f}, {c+1.96*s:.3f})")

# Save 2x2 estimates
did = pd.DataFrame([
    {"outcome":"notification_min","coef":m_did_notif.params["treated_x_post"],"se":m_did_notif.bse["treated_x_post"],"t":m_did_notif.tvalues["treated_x_post"]},
    {"outcome":"fatality_rate","coef":m_did_fatal.params["treated_x_post"],"se":m_did_fatal.bse["treated_x_post"],"t":m_did_fatal.tvalues["treated_x_post"]},
])
did.to_csv("output/tables/ng911_did_2x2.csv", index=False)
print("\nWrote: output/tables/ng911_event_study_notif.csv")
print("Wrote: output/tables/ng911_event_study_fatal.csv")
print("Wrote: output/tables/ng911_did_2x2.csv")
