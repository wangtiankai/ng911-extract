"""
Fetch historical National 911 Profile Database PDFs.

Simplest reliable approach: drive a real Chromium page (real TLS fingerprint)
and fetch each URL via in-page `fetch()`, which returns ArrayBuffer; base64
encode and return to Python. This bypasses Akamai's bot block on both raw
curl and Playwright's separate HTTP API.
"""

from playwright.sync_api import sync_playwright
import pathlib, time, json, base64

URLS = {
    "2011_911_Profile_Database_RPT.pdf":        "https://www.911.gov/assets/2011_911_Profile_Database_RPT.pdf",
    "2014_911_Profile_Database_RPT.pdf":        "https://www.911.gov/assets/2014_911_Profile_Database_RPT.pdf",
    "2015_911_Profile_Database_RPT.pdf":        "https://www.911.gov/assets/2015_911_Profile_Database_RPT.pdf",
    "2016_911_Profile_Database_RPT.pdf":        "https://www.911.gov/assets/2016_911_Profile_Database_RPT.pdf",
    "2017_911_Profile_Database_RPT.pdf":        "https://www.911.gov/assets/2017_911_Profile_Database_RPT.pdf",
    "2019_911_Profile_Database_RPT.pdf":        "https://www.911.gov/assets/2019_911_Profile_Database_RPT.pdf",
    "National_911_Annual_Report_2019_Data.pdf": "https://www.911.gov/assets/National_911_Annual_Report_2019_Data.pdf",
    "National_911_Annual_Report_2020_Data.pdf": "https://www.911.gov/assets/National_911_Annual_Report_2020_Data.pdf",
}

OUTDIR = pathlib.Path("C:/Users/tw26/AppData/Local/Temp/ng911_pdfs")
OUTDIR.mkdir(parents=True, exist_ok=True)

results = {}

# JS snippet: fetch the URL, return base64 or status
FETCH_JS = """
async (url) => {
    try {
        const r = await fetch(url, {credentials: 'omit', cache: 'no-store'});
        if (!r.ok) return {status: r.status};
        const ab = await r.arrayBuffer();
        let bin = '';
        const bytes = new Uint8Array(ab);
        const CHUNK = 0x8000;
        for (let i = 0; i < bytes.length; i += CHUNK) {
            bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
        }
        return {status: 200, b64: btoa(bin), bytes: bytes.length};
    } catch (e) {
        return {status: 'err', msg: String(e)};
    }
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    # Need a real origin so the browser treats the session normally. Navigate to the
    # 911.gov annual report page first to set referer / cookie state.
    page.goto("https://www.911.gov/projects/national-911-annual-report/", wait_until="domcontentloaded", timeout=60_000)
    print("loaded hub page")
    for fname, url in URLS.items():
        out = OUTDIR / fname
        if out.exists() and out.stat().st_size > 50_000:
            results[fname] = {"status": "exists", "bytes": out.stat().st_size}
            print(f"SKIP {fname} (exists, {out.stat().st_size/1024:.1f} KB)")
            continue
        try:
            t0 = time.time()
            res = page.evaluate(FETCH_JS, url)
            if not isinstance(res, dict) or res.get("status") != 200:
                results[fname] = {"status": "fetch_fail", "result": res, "url": url}
                print(f"ERR {fname:48s} -> {res}")
                continue
            data = base64.b64decode(res["b64"])
            out.write_bytes(data)
            results[fname] = {"status": "ok", "bytes": res["bytes"], "url": url, "elapsed_s": round(time.time()-t0, 2)}
            print(f"OK  {fname:48s} {res['bytes']/1024:7.1f} KB  {time.time()-t0:.1f}s")
        except Exception as e:
            results[fname] = {"status": "error", "error": str(e)[:200], "url": url}
            print(f"ERR {fname:48s} {str(e)[:200]}")
        time.sleep(0.5)
    browser.close()

(OUTDIR / "fetch_log.json").write_text(json.dumps(results, indent=2))
print("done")
