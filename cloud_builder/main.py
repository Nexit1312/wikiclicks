import gzip,json,shutil,time
from pathlib import Path
from common import fetch_top1000
from catalog import build_catalog
from corpus import resolve_catalog,choose_corpus
from articles import build_articles
from graph_core import build_graph
from score import build_compact

def main():
    root=Path("cloud_run"); work=root/"work"; out=root/"output"
    work.mkdir(parents=True,exist_ok=True); out.mkdir(parents=True,exist_ok=True)
    started=time.time()
    print("WikiClicks Cloud Production Build")
    top=fetch_top1000(); print("Top-1000 geladen")
    data=build_catalog(top,work)
    title_to_id,canonical=resolve_catalog(data)
    corpus_ids,primary_titles=choose_corpus(top,data,title_to_id,canonical,connectors=12000,min_links=12)
    titles=data["titles"]; corpus_titles=[titles[i] for i in corpus_ids]
    articles=build_articles(work,titles,title_to_id,canonical,corpus_ids,max_links=120)
    low=[(t,len(articles[t]["links"])) for t in primary_titles if len(articles[t]["links"])<12]
    if low: raise RuntimeError("Primärartikel unter 12 Links: "+str(low[:20]))
    idx,g,pidx,dist,pred,rev,indeg,outdeg=build_graph(corpus_titles,primary_titles,articles)
    compact=build_compact(corpus_titles,primary_titles,articles,idx,g,pidx,dist,pred,rev,indeg,outdeg)
    payload={"version":"wikiclicks-cloud-2026-08","generatedAt":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"license":"CC BY-SA 4.0","articles":articles,"compact":compact}
    target=out/"wikiclicks-production.json.gz"
    with gzip.open(target,"wt",encoding="utf-8",compresslevel=6) as f: json.dump(payload,f,ensure_ascii=False,separators=(",",":"))
    manifest={"primaryArticles":1000,"corpusArticles":len(corpus_titles),"edges":compact["graphStats"]["edges"],"avgOut":compact["graphStats"]["avgOut"],"minPrimaryOut":compact["graphStats"]["minPrimaryOut"],"sizeBytes":target.stat().st_size,"elapsedSeconds":round(time.time()-started,1)}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),"utf-8")
    print(json.dumps(manifest,indent=2,ensure_ascii=False))
    print("BUILD COMPLETE")

if __name__=="__main__": main()
