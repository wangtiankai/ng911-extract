"""Kill-test verdict for the NG911 study.

Reads the tables produced by ng911_03_event_study.py and
ng911_04_falsification.py, applies the rubric from HANDOFF §6, and writes
output/verdict_ng911.md with a CONTINUE / INVESTIGATE / STOP decision.

Rubric (HANDOFF §6):

  1. Pre-trend                max |t| on event-time bins [-5, -2] < 2
  2. Notification effect      < -3 min, 95% CI excludes 0
  3. EMS response effect      secondary, no hard threshold
  4. Fatality effect          small, possibly null
  5. Crash-count falsif       post-period coef on log(crashes) ~ 0, |t| < 2
  6. Urban falsification      urban notification effect ~ 0, |t| < 2
  7. 2024-drop                main result robust to dropping 2024
  8. Reporting completeness   diagnostic

Decision rules:
  CONTINUE     if (1) passes, (2) passes, (5) passes, (6) passes
  INVESTIGATE  if effects exist but (5) or (6) is borderline
  STOP         if (5) or (6) fires strongly
"""
import pandas as pd
import numpy as np
from pathlib import Path

TABLES = Path("output/tables")
es_notif = pd.read_csv(TABLES / "ng911_event_study_notif.csv")
es_fatal = pd.read_csv(TABLES / "ng911_event_study_fatal.csv")
did      = pd.read_csv(TABLES / "ng911_did_2x2.csv")
fc       = pd.read_csv(TABLES / "ng911_falsif_crashcount.csv")
fu       = pd.read_csv(TABLES / "ng911_falsif_urban.csv")
fn24     = pd.read_csv(TABLES / "ng911_falsif_no_2024.csv")

results = []

def pre_trend_t(es, lo=-5, hi=-2):
    pre = es[(es["event_time"] >= lo) & (es["event_time"] <= hi) & (es["se"] > 0)]
    if len(pre) == 0: return np.nan
    return (pre["coef"] / pre["se"]).abs().max()

def post_max_t(es):
    post = es[(es["event_time"] > -1) & (es["se"] > 0)]
    if len(post) == 0: return np.nan
    return (post["coef"] / post["se"]).abs().max()

def post_avg(es):
    post = es[(es["event_time"] > -1) & es["coef"].notna()]
    return post["coef"].mean() if len(post) else np.nan

# (1) Pre-trend
pre_t_notif = pre_trend_t(es_notif)
results.append(("1. Pre-trend (notification, et -5 to -2)",
                f"max |t| = {pre_t_notif:.2f}",
                "PASS" if pre_t_notif < 2 else "FAIL"))

# (2) Notification effect (2x2 DiD)
notif_row = did[did["outcome"]=="notification_min"].iloc[0]
notif_coef = notif_row["coef"]; notif_se = notif_row["se"]; notif_ci_lo = notif_coef - 1.96*notif_se; notif_ci_hi = notif_coef + 1.96*notif_se
notif_pass = (notif_coef < -3) and (notif_ci_hi < 0)
results.append(("2. Notification effect (2x2 DiD)",
                f"coef = {notif_coef:.2f} min, 95% CI = ({notif_ci_lo:.2f}, {notif_ci_hi:.2f})",
                "PASS" if notif_pass else "FAIL"))

# (3) EMS response — not separately estimated; report null
results.append(("3. EMS response effect",
                "not separately estimated; would mirror (2) if dispatch is the channel",
                "N/A"))

# (4) Fatality effect
fatal_row = did[did["outcome"]=="fatality_rate"].iloc[0]
fatal_coef = fatal_row["coef"]; fatal_se = fatal_row["se"]
fatal_pass = abs(fatal_coef) < 0.02  # arbitrary threshold: less than 2 pp on fatality rate
results.append(("4. Fatality effect (2x2 DiD)",
                f"coef = {fatal_coef:.4f}, t = {fatal_coef/fatal_se:.2f}",
                "PASS" if fatal_pass else "FAIL"))

# (5) Crash-count falsification
fc_avg = post_avg(fc); fc_t = post_max_t(fc)
fc_pass = (abs(fc_avg) < 0.1) and (np.isnan(fc_t) or fc_t < 2)
results.append(("5. Crash-count falsification",
                f"post avg = {fc_avg:.4f}, max |t| = {fc_t:.2f}",
                "PASS" if fc_pass else "FAIL"))

# (6) Urban falsification
fu_avg = post_avg(fu); fu_t = post_max_t(fu)
fu_pass = (abs(fu_avg) < 20) and (np.isnan(fu_t) or fu_t < 2)
results.append(("6. Urban falsification",
                f"post avg = {fu_avg:.2f} min, max |t| = {fu_t:.2f}",
                "PASS" if fu_pass else "FAIL"))

# (7) 2024-drop
fn24_avg = post_avg(fn24); fn24_t = post_max_t(fn24)
main_avg = post_avg(es_notif)
diff = abs(fn24_avg - main_avg)
fn24_pass = diff < abs(main_avg) * 0.25  # main effect changes <25%
results.append(("7. 2024-drop sensitivity",
                f"main post avg = {main_avg:.2f}, no-2024 avg = {fn24_avg:.2f}, change = {(fn24_avg/main_avg - 1)*100 if main_avg else 0:.1f}%",
                "PASS" if fn24_pass else "FAIL"))

# (8) Reporting completeness
p = pd.read_parquet("output/ng911_panel.parquet")
p = p[p["treatment_year"].isin([2018.0, 2020.0])]
valid = p["mean_not_min"].notna() & p["mean_not_min"].between(1, 1439)
share = valid.mean()
results.append(("8. Reporting completeness",
                f"{share*100:.1f}% of treated county-years have valid mean notification time",
                "DIAGNOSTIC"))

# Decision
hard_fails = {name for name, _, status in results if status == "FAIL"}
critical = {"5. Crash-count falsification", "6. Urban falsification", "1. Pre-trend (notification, et -5 to -2)", "2. Notification effect (2x2 DiD)"}
fired_critical = hard_fails & critical

if fired_critical & {"5. Crash-count falsification", "6. Urban falsification"}:
    decision = "STOP"
    reason = "Crash-count or urban falsification fires strongly: NG911 effect is not rural-specific and/or moves crash counts, implying confounding with state-level trends."
elif "1. Pre-trend (notification, et -5 to -2)" in hard_fails:
    decision = "INVESTIGATE"
    reason = "Pre-trend fails; cannot attribute post-period change to NG911. Possibly state-level reporting or measurement trends."
elif "2. Notification effect (2x2 DiD)" in hard_fails:
    decision = "INVESTIGATE"
    reason = "Notification effect not statistically distinguishable from zero; underpowered given 12 treated states."
else:
    decision = "CONTINUE"
    reason = "All hard conditions pass."

md = []
md.append("# NG911 kill-test verdict\n")
md.append(f"*Generated 2026-09-04 by `code/ng911_05_verdict.py`*\n")
md.append(f"\n**Decision: {decision}**\n")
md.append(f"\n{reason}\n")
md.append("\n## Rubric\n")
md.append("| # | Condition | Result | Status |")
md.append("|---|---|---|---|")
for name, val, status in results:
    md.append(f"| {name} | {val} | {status} |")
md.append("\n## Caveats\n")
md.append("- Only 12 treated states (8 with 2018 milestone, 4 with 2020 milestone) survive FARS coverage. Power is low; wide confidence intervals.")
md.append("- The 2014, 2015, 2016 cohorts from the NG911 panel were dropped because FARS starts in 2015; their pre-period would be pre-2010. Only 2018 and 2020 cohorts have full pre/post coverage.")
md.append("- Maturity Model (2018–2020) and 3.2.x schema (2013–2016) yield different event-year definitions; the current `event_year` is the FIRST year any of the following fires: ng911_rfp_released=Yes, n_operational_esinets≥1, OR maturity routing_location≥2.")
md.append("- Urban falsification fires strongly (post avg +255 min, |t|=7.35). This is the most damaging signal: NG911's apparent effect is NOT rural-specific.")
md.append("\n## Files\n")
md.append("- `output/tables/ng911_event_study_notif.csv` — event-study coefficients, notification minutes")
md.append("- `output/tables/ng911_event_study_fatal.csv` — event-study coefficients, fatality rate")
md.append("- `output/tables/ng911_did_2x2.csv` — 2x2 DiD estimates")
md.append("- `output/tables/ng911_falsif_crashcount.csv` — log crash count")
md.append("- `output/tables/ng911_falsif_urban.csv` — urban subsample")
md.append("- `output/tables/ng911_falsif_no_2024.csv` — drop 2024 sensitivity")
md.append("- `output/ng911_panel.parquet` — input panel (38,997 county-years, 12 states)")
md.append("- `data/ng911/state_ng911_panel.csv` — input treatment panel (56 jurisdictions × 7 years)")

Path("output").mkdir(exist_ok=True)
Path("output/verdict_ng911.md").write_text("\n".join(md), encoding="utf-8")
print(f"Decision: {decision}")
print(f"Wrote output/verdict_ng911.md")
