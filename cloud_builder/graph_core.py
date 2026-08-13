import base64
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

def build_graph(corpus_titles,primary_titles,articles):
    idx={t:i for i,t in enumerate(corpus_titles)};rows=[];cols=[]
    indeg=np.zeros(len(corpus_titles),dtype=np.uint32);outdeg=np.zeros(len(corpus_titles),dtype=np.uint16)
    for t in corpus_titles:
        i=idx[t];links=list(dict.fromkeys(idx[x] for x in articles[t]["links"] if x in idx and x!=t));outdeg[i]=len(links)
        for j in links:rows.append(i);cols.append(j);indeg[j]+=1
    g=csr_matrix((np.ones(len(rows),dtype=np.uint8),(rows,cols)),shape=(len(corpus_titles),len(corpus_titles)))
    pidx=np.array([idx[t] for t in primary_titles],dtype=np.int32)
    print(f"Graph: {len(corpus_titles):,} Artikel · {len(rows):,} Links")
    dist,pred=shortest_path(g,directed=True,unweighted=True,indices=pidx,return_predecessors=True)
    rev=shortest_path(g.transpose().tocsr(),directed=True,unweighted=True,indices=pidx,return_predecessors=False)
    return idx,g,pidx,dist,pred,rev,indeg,outdeg

def encode_u16(a):
    return base64.b64encode(np.asarray(a,dtype="<u2").tobytes()).decode("ascii")

def encode_pred(pred):
    out=np.full(pred.shape,65535,dtype=np.uint16);mask=pred>=0;out[mask]=pred[mask].astype(np.uint16)
    return encode_u16(out)
