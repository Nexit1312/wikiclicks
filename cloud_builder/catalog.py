import gzip, json
from config_full import DUMP_BASE, PARTS
from common import download_part, iter_pages, norm_title, title_ok, REDIRECT_RE, extract_links

def build_catalog(top_titles, work):
    cache = work / "catalog.json.gz"
    if cache.exists():
        with gzip.open(cache, "rt", encoding="utf-8") as f:
            return json.load(f)
    titles, page_ids, disambig = [], [], []
    redirects, primary_links = {}, {}
    top = set(top_titles)
    temp = work / "current.bz2"
    for pi, name in enumerate(PARTS, 1):
        download_part(f"{DUMP_BASE}/{name}", temp)
        print(f"PASS 1/2 – Katalog {pi}/{len(PARTS)}")
        count = 0
        for title, ns, pid, rid, text in iter_pages(temp):
            if ns != 0:
                continue
            t = norm_title(title)
            if not title_ok(t):
                continue
            idx = len(titles)
            titles.append(t); page_ids.append(pid or 0)
            m = REDIRECT_RE.search((text or "")[:500])
            if m:
                redirects[str(idx)] = norm_title(m.group(1))
            if "{{Begriffsklärung" in (text or "")[:5000] or t.endswith("(Begriffsklärung)"):
                disambig.append(idx)
            if t in top:
                primary_links[t] = extract_links(text)
            count += 1
            if count % 100000 == 0:
                print(f"  {count:,} Seiten")
        temp.unlink(missing_ok=True)
    data = {"titles":titles,"pageIds":page_ids,"redirects":redirects,"disambig":disambig,"primaryLinks":primary_links}
    with gzip.open(cache, "wt", encoding="utf-8", compresslevel=6) as f:
        json.dump(data, f, ensure_ascii=False, separators=(",",":"))
    return data
