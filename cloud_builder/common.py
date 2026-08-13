import bz2, json, re, time, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from config_full import ANALYTICS_BASE, USER_AGENT

BLOCKED_PREFIXES=("Wikipedia:","Spezial:","Datei:","Kategorie:","Portal:","Vorlage:","Hilfe:","Benutzer:","Diskussion:","MediaWiki:","Modul:","TimedText:")
BLOCKED_TITLE_RE=re.compile(r"^(Liste (der|des|von)\b|Nekrolog\b|Chronik\b)",re.I)
REDIRECT_RE=re.compile(r"^\s*#(?:WEITERLEITUNG|REDIRECT)\s*\[\[([^\]|#]+)",re.I)
WIKILINK_RE=re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
SPACE_RE=re.compile(r"\s+")

def norm_title(s): return SPACE_RE.sub(" ",(s or "").replace("_"," ").strip())
def title_ok(s):
    s=norm_title(s)
    return bool(s and len(s)<=120 and not s.startswith(BLOCKED_PREFIXES) and not BLOCKED_TITLE_RE.search(s))

def fetch_top1000():
    periods=[(2026,7),(2026,6),(2026,5),(2026,4),(2026,3),(2026,2)]
    out=[]; seen=set()
    for y,m in periods:
        url=f"{ANALYTICS_BASE}/{y:04d}/{m:02d}/all-days"
        req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT})
        with urllib.request.urlopen(req,timeout=60) as r: rows=(json.load(r).get("items") or [{}])[0].get("articles") or []
        for row in rows:
            t=norm_title(row.get("article",""))
            if not title_ok(t) or t in seen or t in {"Hauptseite","Wikipedia:Hauptseite","Spezial:Suche","-"}: continue
            seen.add(t); out.append(t)
            if len(out)==1000: return out
    raise RuntimeError(f"Nur {len(out)} gültige Top-Artikel gefunden")

def download_part(url,dest):
    tmp=dest.with_suffix(dest.suffix+".part")
    if tmp.exists(): tmp.unlink()
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT})
    print("↓",url.rsplit("/",1)[-1])
    with urllib.request.urlopen(req,timeout=180) as r, open(tmp,"wb") as f:
        total=int(r.headers.get("Content-Length") or 0); done=0; last=time.time()
        while True:
            b=r.read(4*1024*1024)
            if not b: break
            f.write(b); done+=len(b)
            if time.time()-last>5:
                print(f"  {done/1e9:.2f}"+(f"/{total/1e9:.2f} GB" if total else " GB")); last=time.time()
    tmp.replace(dest); return dest

def iter_pages(path):
    with bz2.open(path,"rb") as fh:
        for _,elem in ET.iterparse(fh,events=("end",)):
            if not elem.tag.endswith("page"): continue
            title=""; ns=None; pid=0; rid=0; text=""
            for c in elem:
                tag=c.tag.rsplit("}",1)[-1]
                if tag=="title": title=c.text or ""
                elif tag=="ns":
                    try: ns=int(c.text or "0")
                    except: ns=None
                elif tag=="id" and not pid:
                    try: pid=int(c.text or "0")
                    except: pass
                elif tag=="revision":
                    for rc in c:
                        rt=rc.tag.rsplit("}",1)[-1]
                        if rt=="id":
                            try: rid=int(rc.text or "0")
                            except: pass
                        elif rt=="text": text=rc.text or ""
            yield title,ns,pid,rid,text
            elem.clear()

def extract_links(text):
    out=[]; seen=set()
    for m in WIKILINK_RE.finditer(text or ""):
        t=norm_title(m.group(1))
        if title_ok(t) and t not in seen: seen.add(t); out.append(t)
    return out
