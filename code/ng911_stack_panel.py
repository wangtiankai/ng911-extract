"""
Stack per-year NG911 panels into one master panel.

Output: data/ng911/state_ng911_panel.csv
Columns: state_fips, state_abbr, state_name, year, plus all extracted fields
         and a derived 'event_year' = first year state has ng911_rfp_released=Yes
         OR n_operational_esinets>=1 OR routing_location>=2 (Foundational or above).
"""

import csv, os, sys

YEARS = [2013, 2014, 2015, 2016, 2018, 2019, 2020]
DIR = 'C:/Users/tw26/dead-zones/data/ng911'

ABBR = {
    '01':'AL','02':'AK','04':'AZ','05':'AR','06':'CA','08':'CO','09':'CT','10':'DE','11':'DC',
    '12':'FL','13':'GA','15':'HI','16':'ID','17':'IL','18':'IN','19':'IA','20':'KS','21':'KY',
    '22':'LA','23':'ME','24':'MD','25':'MA','26':'MI','27':'MN','28':'MS','29':'MO','30':'MT',
    '31':'NE','32':'NV','33':'NH','34':'NJ','35':'NM','36':'NY','37':'NC','38':'ND','39':'OH',
    '40':'OK','41':'OR','42':'PA','44':'RI','45':'SC','46':'SD','47':'TN','48':'TX','49':'UT',
    '50':'VT','51':'VA','53':'WA','54':'WV','55':'WI','56':'WY',
}

# Master schema: state_fips, state_abbr, state_name, year, then dynamic
KEYS = [
    'ng911_plan_adopted', 'ng911_rfp_released',
    'pct_pop_served', 'pct_geo_served',
    'n_esinet_psaps', 'n_operational_esinets',
    'routing_location', 'gis_data', 'core_services', 'network',
    'psap_call_handling', 'security', 'operations', 'optional_interfaces',
]

# Load each year and index by fips
by_year = {}
for yr in YEARS:
    path = os.path.join(DIR, f'state_ng911_panel_{yr}.csv')
    rows = list(csv.DictReader(open(path)))
    by_year[yr] = {r['state_fips']: r for r in rows}

# Build master panel: keep all states that appear in any year
all_fips = set()
for yr in YEARS:
    all_fips |= set(by_year[yr].keys())
all_fips = sorted(all_fips)

master = []
for fips in all_fips:
    abbr = ABBR.get(fips, '')
    name = ''
    for yr in YEARS:
        if fips in by_year[yr]:
            name = by_year[yr][fips].get('state_name','')
            if name: break
    for yr in YEARS:
        row = by_year[yr].get(fips)
        if row is None:
            # State missing in this year — emit a row with blanks
            row = {'state_fips': fips, 'state_name': name, 'year': str(yr)}
        out = {
            'state_fips': fips,
            'state_abbr': abbr,
            'state_name': name,
            'year': yr,
        }
        for k in KEYS:
            v = row.get(k, '')
            out[k] = '' if v in (None, 'None') else v
        master.append(out)

# Derive event_year per state
event_year = {}
for fips in all_fips:
    ey = None
    for row in master:
        if row['state_fips'] != fips: continue
        yr = row['year']
        triggered = False
        if row.get('ng911_rfp_released') == 'Yes':
            triggered = True
        if row.get('n_operational_esinets') not in ('', '0', '0.0', None):
            try:
                if float(row['n_operational_esinets']) >= 1:
                    triggered = True
            except ValueError:
                pass
        try:
            if int(row.get('routing_location') or 0) >= 2:
                triggered = True
        except ValueError:
            pass
        if triggered:
            ey = yr; break
    event_year[fips] = ey or ''

# Attach event_year to each row, but only on rows at or after the trigger year.
# Pre-treatment rows for that state carry an empty event_year so event_time
# is never negative-relative-to-future.
for row in master:
    ey = event_year[row['state_fips']]
    if ey == '' or int(row['year']) >= int(ey):
        row['event_year'] = ey
    else:
        row['event_year'] = ''

# Write master CSV
out_path = os.path.join(DIR, 'state_ng911_panel.csv')
fieldnames = ['state_fips','state_abbr','state_name','year'] + KEYS + ['event_year']
with open(out_path,'w',newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction='ignore')
    w.writeheader()
    w.writerows(master)

print(f'wrote {out_path}: {len(master)} rows, {len(all_fips)} states')
print()
print('event_year distribution:')
import collections
c = collections.Counter(str(event_year[fips]) for fips in all_fips)
for k in sorted(c.keys(), key=lambda x: (x=='', x)): print(f'  {k}: {c[k]}')
