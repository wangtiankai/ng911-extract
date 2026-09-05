"""
Re-extract state-level NG911 fields from the 2013, 2014, 2015, 2016 Progress
Reports with proper handling of the 4-column "State Response" grid layout.

The grid format is:
   State Response State Response State Response State Response
   AK No           GU Yes          ME Yes        OK No
   AL No           IA Yes          MI No         OR Yes
   ...

So after the "State Response" header line, every 4 subsequent (abbr, value)
pairs fill one data row. We tokenize after the header and consume them in
groups of 4 columns x 2 tokens = 8 tokens per row.
"""

import pypdf, re, csv, os, sys

ABBR_TO_FIPS = {
    'AL':'01','AK':'02','AZ':'04','AR':'05','CA':'06','CO':'08','CT':'09','DE':'10','DC':'11',
    'FL':'12','GA':'13','HI':'15','ID':'16','IL':'17','IN':'18','IA':'19','KS':'20','KY':'21',
    'LA':'22','ME':'23','MD':'24','MA':'25','MI':'26','MN':'27','MS':'28','MO':'29','MT':'30',
    'NE':'31','NV':'32','NH':'33','NJ':'34','NM':'35','NY':'36','NC':'37','ND':'38','OH':'39',
    'OK':'40','OR':'41','PA':'42','RI':'44','SC':'45','SD':'46','TN':'47','TX':'48','UT':'49',
    'VT':'50','VA':'51','WA':'53','WV':'54','WI':'55','WY':'56',
}
FIPS_TO_NAME = {
    '01':'Alabama','02':'Alaska','04':'Arizona','05':'Arkansas','06':'California','08':'Colorado',
    '09':'Connecticut','10':'Delaware','11':'District of Columbia','12':'Florida','13':'Georgia',
    '15':'Hawaii','16':'Idaho','17':'Illinois','18':'Indiana','19':'Iowa','20':'Kansas',
    '21':'Kentucky','22':'Louisiana','23':'Maine','24':'Maryland','25':'Massachusetts',
    '26':'Michigan','27':'Minnesota','28':'Mississippi','29':'Missouri','30':'Montana',
    '31':'Nebraska','32':'Nevada','33':'New Hampshire','34':'New Jersey','35':'New Mexico',
    '36':'New York','37':'North Carolina','38':'North Dakota','39':'Ohio','40':'Oklahoma',
    '41':'Oregon','42':'Pennsylvania','44':'Rhode Island','45':'South Carolina','46':'South Dakota',
    '47':'Tennessee','48':'Texas','49':'Utah','50':'Vermont','51':'Virginia','53':'Washington',
    '54':'West Virginia','55':'Wisconsin','56':'Wyoming',
}

REPORTS = [
    ('2014_911_Profile_Database_RPT.pdf', 2013),
    ('2015_911_Profile_Database_RPT.pdf', 2014),
    ('2016_911_Profile_Database_RPT.pdf', 2015),
    ('2017_911_Profile_Database_RPT.pdf', 2016),
]

# (short name, section pattern, header pattern to match the State Response grid heading)
FIELDS = [
    ('ng911_plan_adopted',     r'3\.2\.1\.1',                       r'Statewide NG911 Plan Adopted',                              'yn'),
    ('ng911_rfp_released',     r'3\.2\.2\.1',                       r'Statewide.*Request for Proposal',                           'yn'),
    ('pct_pop_served',         r'3\.2\.3\.2',                       r'Percentage of.*Population Served.*NG911',                   'pct'),
    ('pct_geo_served',         r'3\.2\.3\.3',                       r'Percentage of.*Geographical Area.*Served.*NG911',           'pct'),
    ('n_esinet_psaps',         r'3\.2\.4\.1',                       r'ESInet connected PSAPs',                                    'count'),
    ('n_operational_esinets',  r'3\.2\.4\.3',                       r'Operational ESInets Deployed',                              'count'),
]

PDF_DIR = 'C:/Users/tw26/dead-zones/data/ng911/raw_pdfs'
OUT_DIR = 'C:/Users/tw26/dead-zones/data/ng911'

def find_data_page(r, sec_pat, head_pat):
    """Return (page_text, page_number) of the page that contains BOTH the
    section heading AND a 'State Response' header followed by state-value pairs.

    Skip pages with only the section heading (TOC entries, prose) or with only
    prose — we want the page that contains the actual 4-column grid.
    """
    for i in range(len(r.pages)):
        t = r.pages[i].extract_text() or ''
        if not (re.search(sec_pat, t) and re.search(head_pat, t, re.I)):
            continue
        if 'State Response' not in t:
            continue
        return t, i+1
    return None, None

def parse_grid(text, value_format):
    """Parse the state grid from a page. Two layouts are supported:
    (a) 4-column 'State Response' grid: 8 tokens per line, (abbr value)*4
    (b) 2-column 'State Response (%)' grid: 4 tokens per line, (abbr value)*2
    Plus a summary block '100% of <field> Served: AL, CA, ...' which lists
    states with the maximum value for percentage fields.
    """
    out = {}
    lines = text.split('\n')
    hdr_idx = None
    for i, L in enumerate(lines):
        if 'State Response' in L and L.count('State') >= 2:
            hdr_idx = i; break
    if hdr_idx is None:
        return out
    # Walk data lines
    for j in range(hdr_idx+1, len(lines)):
        s = lines[j].strip()
        if not s: continue
        parts = s.split()
        if len(parts) < 2: continue
        # Walk pairs
        k = 0
        while k + 1 < len(parts):
            abbr = parts[k]
            val = parts[k+1]
            k += 2
            if abbr not in ABBR_TO_FIPS:
                continue
            if val in ('Response','State'):
                continue
            if value_format == 'yn' and val not in ('Yes','No','?','x','Unknown'):
                continue
            out[abbr] = val
        # End on narrative line
        if (len(parts) % 2 != 0 and not any(p in ABBR_TO_FIPS for p in parts)) or s.endswith(':') or 'Served:' in s or 'Did not' in s:
            break
    # Handle summary block like "100% of Geographic Area Served: AL, CA, ..."
    if value_format == 'pct':
        for j in range(hdr_idx+1, min(len(lines), hdr_idx+60)):
            s = lines[j].strip()
            if ('100%' in s or '0%' in s) and 'Served' in s:
                # Pull state abbreviations from this and continuation lines until a blank/non-list line
                tail = s.split(':', 1)[1] if ':' in s else s
                tokens = tail.replace(',', ' ').split()
                for t in tokens:
                    if t in ABBR_TO_FIPS and t not in out:
                        out[t] = '100' if '100%' in s else '0'
                # Continuation: next lines starting with whitespace and abbrs
                k = j + 1
                while k < len(lines):
                    s2 = lines[k].strip()
                    if not s2 or not any(x in ABBR_TO_FIPS for x in s2.split()):
                        break
                    for t in s2.replace(',', ' ').split():
                        if t in ABBR_TO_FIPS and t not in out:
                            out[t] = '100' if '100%' in s else '0'
                    k += 1
    return out

def normalize(val, fmt):
    if val is None or val == '': return None
    if fmt == 'yn':
        if val.lower() in ('yes','y'): return 'Yes'
        if val.lower() in ('no','n'): return 'No'
        if val in ('?','x'): return None
        return val
    if fmt == 'pct':
        try:
            f = float(val.replace('%','').strip())
            return None if f > 100 else f
        except ValueError:
            return None
    if fmt == 'count':
        try: return int(float(val.replace(',','').strip()))
        except ValueError: return None
    return val

for fname, year in REPORTS:
    print(f'== {year} ==')
    r = pypdf.PdfReader(os.path.join(PDF_DIR, fname))
    panel = {fips: {'state_fips': fips, 'state_name': name, 'year': year} for fips, name in FIPS_TO_NAME.items()}
    for short, sec_pat, head_pat, fmt in FIELDS:
        text, page = find_data_page(r, sec_pat, head_pat)
        if text is None:
            print(f'  [{year}] {short}: section page not found')
            continue
        vals = parse_grid(text, fmt)
        if not vals:
            print(f'  [{year}] {short}: no grid parsed on p{page}')
            continue
        for abbr, raw in vals.items():
            fips = ABBR_TO_FIPS[abbr]
            panel[fips][short] = normalize(raw, fmt)
        print(f'  [{year}] {short}: {len(vals)} states from p{page}')
    out = os.path.join(OUT_DIR, f'state_ng911_panel_{year}.csv')
    fieldnames = ['state_fips','state_name','year'] + [s for s,_,_,_ in FIELDS]
    with open(out,'w',newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader()
        for fips in sorted(panel): w.writerow(panel[fips])
    print(f'  wrote {out}')
