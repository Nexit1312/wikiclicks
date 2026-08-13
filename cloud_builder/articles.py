from config_full import DUMP_BASE,PARTS
from common import download_part,iter_pages,norm_title,extract_links
from rendering import render_article

def build_articles(work,titles,title_to_id,canonical,corpus_ids,max_links=120):
    corpus=set(corpus_ids);names=[titles[i] for i in corpus_ids];allowed=set(names)
    canon={titles[i]:titles[int(canonical[i])] for i in range(len(titles)) if int(canonical[i])!=i}
    articles={};tmp=work/"current.bz2"
    for pi,name in enumerate(PARTS,1):
        download_part(f"{DUMP_BASE}/{name}",tmp)
        print(f"PASS 2/2 – Spielartikel {pi}/{len(PARTS)}")
        for title,ns,pid,rid,text in iter_pages(tmp):
            if ns!=0:continue
            t=norm_title(title);sid=title_to_id.get(t)
            if sid is None or sid not in corpus or int(canonical[sid])!=sid:continue
            raw=[];seen=set()
            for lt in extract_links(text):
                j=title_to_id.get(lt)
                if j is None:continue
                j=int(canonical[j]);ct=titles[j]
                if j in corpus and j!=sid and ct not in seen:
                    seen.add(ct);raw.append(ct)
            body,visible=render_article(text,allowed,canon,max_links=max_links)
            links=list(dict.fromkeys([x for x in visible+raw if x!=t]))[:max_links]
            articles[t]={"title":t,"revisionId":rid,"html":body,"links":links}
        tmp.unlink(missing_ok=True)
    missing=[t for t in names if t not in articles]
    if missing:raise RuntimeError(f"{len(missing)} ausgewählte Artikel fehlen")
    return articles
