"""Extract the NG911 Maturity Model state grid from a Progress Report PDF.

Same algorithm as the earlier 2019-extract: even-numbered pages (after the
legend page) carry the state x category x level matrix.
"""
import pypdf, csv, os, re

# (pdf filename, output data year, even-pages with state values)
RUNS = [
    ('2019_911_Profile_Database_RPT.pdf',        2018, [74, 76, 78, 80, 82, 84, 86, 88]),
    ('National_911_Annual_Report_2020_Data.pdf', 2020, [69, 71, 73, 75, 77, 79, 81, 83]),
]

# Category names per even page (in order)
CATEGORIES = [
    'routing_location',
    'gis_data',
    'core_services',
    'network',
    'psap_call_handling',
    'security',
    'operations',
    'optional_interfaces',
]

NAME_TO_FIPS = {
    'Alabama':'01','Alaska':'02','Arizona':'04','Arkansas':'05','California':'06','Colorado':'08',
    'Connecticut':'09','Delaware':'10','District of Columbia':'11','Florida':'12','Georgia':'13',
    'Hawaii':'15','Idaho':'16','Illinois':'17','Indiana':'18','Iowa':'19','Kansas':'20',
    'Kentucky':'21','Louisiana':'22','Maine':'23','Maryland':'24','Massachusetts':'25',
    'Michigan':'26','Minnesota':'27','Mississippi':'28','Missouri':'29','Montana':'30',
    'Nebraska':'31','Nevada':'32','New Hampshire':'33','New Jersey':'34','New Mexico':'35',
    'New York':'36','North Carolina':'37','North Dakota':'38','Ohio':'39','Oklahoma':'40',
    'Oregon':'41','Pennsylvania':'42','Rhode Island':'44','South Carolina':'45','South Dakota':'46',
    'Tennessee':'47','Texas':'48','Utah':'49','Vermont':'50','Virginia':'51','Washington':'53',
    'West Virginia':'54','Wisconsin':'55','Wyoming':'56',
    'American Samoa':'60','Guam':'66','Northern Mariana Islands':'69','Puerto Rico':'72',
    'Virgin Islands (US)':'78',
}
NAME_RE = re.compile('|'.join(re.escape(n) for n in NAME_TO_FIPS))

LEVEL_MAP = {
    'Unknown':0,'Legacy':1,'Foundational':2,'Transitional':3,
    'Intermediate':4,'Jurisdictional End':5,'Jurisdictional End State':5,'National End State':6
}

PDF_DIR = 'C:/Users/tw26/dead-zones/data/ng911/raw_pdfs'
OUT_DIR = 'C:/Users/tw26/dead-zones/data/ng911'

for fname, year, value_pages in RUNS:
    print(f'== {year} ({fname}) ==')
    r = pypdf.PdfReader(os.path.join(PDF_DIR, fname))
    panel = {}
    for fips, name in NAME_TO_FIPS.items():
        panel[fips] = {'state_fips': fips, 'state_name': name, 'year': year}
    for one_based, cat in zip(value_pages, CATEGORIES):
        t = r.pages[one_based-1].extract_text() or ''
        matched = 0
        for i, L in enumerate(t.split('\n')):
            s = L.strip()
            m = NAME_RE.match(s)
            if not m: continue
            name = m.group(0)
            tail = s[m.end():].strip()
            if tail in LEVEL_MAP or tail in ('?','x'):
                val = tail
            elif tail == '' and i+1 < len(t.split('\n')) and (t.split('\n')[i+1].strip() in LEVEL_MAP or t.split('\n')[i+1].strip() in ('?','x')):
                val = t.split('\n')[i+1].strip()
            else:
                continue
            row = panel[name]
            row.setdefault('state_fips', NAME_TO_FIPS[name])
            if val in LEVEL_MAP:
                row[cat] = LEVEL_MAP[val]; matched += 1
            elif val in ('?','x'):
                row[cat+'_flag'] = 'unknown' if val=='?' else 'did_not_submit'
                matched += 1
        print(f'  p{one_based} ({cat}): {matched}')
    # Drop territories
    keep_fips = [k for k in panel if k not in {'60','66','69','72','78'}]
    rows = [panel[k] for k in keep_fips]
    out = os.path.join(OUT_DIR, f'state_ng911_panel_{year}.csv')
    fieldnames = ['state_fips','state_name','year'] + CATEGORIES
    with open(out,'w',newline='') as fh:
        # Use union of all keys as fieldnames to capture _flag columns too
        all_keys = sorted({k for row in rows for k in row.keys()})
        w = csv.DictWriter(fh, fieldnames=all_keys, extrasaction='ignore')
        w.writeheader()
        for row in rows: w.writerow(row)
    print(f'  wrote {out}')
