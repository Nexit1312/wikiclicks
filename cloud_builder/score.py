import numpy as np
from route_utils import u16b64,pred_b64,rebuild_path,words

def build_compact(corpus_titles,primary_titles,articles,idx,g,pidx,dist,pred,rev,indeg,outdeg):
    routes=[]
    for si,snode in enumerate(pidx):
        for ti,tnode in enumerate(pidx):
            if si==ti or not np.isfinite(dist[si,tnode]):
                continue
            d=int(dist[si,tnode])
            if d<2:
                continue
            path=rebuild_path(pred[si],int(snode),int(tnode))
            if not path:
                continue
            branch=float(np.mean([outdeg[x] for x in path[:-1]])) if path[:-1] else 0.0
            a=words(articles[primary_titles[si]]["html"][:6000]); b=words(articles[primary_titles[ti]]["html"][:6000])
            theme=1.0-len(a&b)/max(1,len(a|b))
            hub=float(np.mean([indeg[x] for x in path[1:-1]])) if len(path)>2 else 0.0
            raw=22*d + min(30.0,branch/3.0) + 22*theme - min(10.0,hub/5000.0)
            score=max(1,min(100,int(round(raw))))
            routes.append((score,d,si,ti))
    vals=np.array([x[0] for x in routes],dtype=float)
    q1=float(np.percentile(vals,35)); q2=float(np.percentile(vals,70))
    buckets={"easy":[],"medium":[],"hard":[]}; scores={"easy":[],"medium":[],"hard":[]}
    for score,d,si,ti in routes:
        key="easy" if score<=q1 and d<=4 else ("hard" if score>=q2 and d>=4 else "medium")
        buckets[key].extend([si,ti]); scores[key].append(score)
    return {"corpusTitles":corpus_titles,"primaryTitles":primary_titles,"predU16B64":pred_b64(pred),"buckets":{k:u16b64(v) for k,v in buckets.items()},"bucketScores":{k:u16b64(v) for k,v in scores.items()},"difficultyThresholds":{"easyMax":round(q1,1),"hardMin":round(q2,1)},"graphStats":{"nodes":len(corpus_titles),"edges":int(g.nnz),"avgOut":round(float(g.nnz)/len(corpus_titles),2),"minPrimaryOut":min(int(outdeg[idx[t]]) for t in primary_titles),"maxOut":int(outdeg.max())}}
