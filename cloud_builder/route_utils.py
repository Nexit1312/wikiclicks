import base64,re
import numpy as np
TAG_RE=re.compile(r"<[^>]+>");TOKEN_RE=re.compile(r"[A-Za-zÄÖÜäöüß]{4,}")

def words(s):return set(x.lower() for x in TOKEN_RE.findall(TAG_RE.sub(" ",s or "")))
def rebuild_path(row,source,target):
    cur=int(target);out=[cur]
    while cur!=source:
        cur=int(row[cur])
        if cur<0:return []
        out.append(cur)
        if len(out)>len(row):return []
    return out[::-1]
def u16b64(values):return base64.b64encode(np.asarray(values,dtype="<u2").tobytes()).decode("ascii")
def pred_b64(pred):
    out=np.full(pred.shape,65535,dtype=np.uint16);mask=pred>=0;out[mask]=pred[mask].astype(np.uint16)
    return u16b64(out)
