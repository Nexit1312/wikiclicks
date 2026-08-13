import numpy as np

def resolve_catalog(data):
    titles = data["titles"]
    title_to_id = {t:i for i,t in enumerate(titles)}
    canonical = np.arange(len(titles), dtype=np.int32)
    direct = {int(i):title_to_id.get(t) for i,t in data["redirects"].items()}
    for i, target in direct.items():
        if target is None:
            continue
        seen = {i}; cur = target
        for _ in range(12):
            nxt = direct.get(cur)
            if nxt is None or nxt in seen:
                break
            seen.add(cur); cur = nxt
        canonical[i] = cur
    return title_to_id, canonical

def choose_corpus(top_titles, data, title_to_id, canonical, connectors=12000, min_links=12):
    titles = data["titles"]
    dis = set(data["disambig"])
    primary, primary_titles = [], []
    for t in top_titles:
        i = title_to_id.get(t)
        if i is None:
            continue
        i = int(canonical[i])
        if i in dis or i in primary:
            continue
        primary.append(i); primary_titles.append(titles[i])
    if len(primary) != 1000:
        raise RuntimeError(f"Nur {len(primary)} der Top-1000 im Dump auflösbar")
    forced, score, resolved = set(), {}, {}
    raw_map = data.get("primaryLinks", {})
    for pid, original, canonical_title in zip(primary, top_titles, primary_titles):
        raw = raw_map.get(canonical_title) or raw_map.get(original) or []
        out, seen = [], set()
        for pos, lt in enumerate(raw):
            j = title_to_id.get(lt)
            if j is None:
                continue
            j = int(canonical[j])
            if j == pid or j in dis or j in seen:
                continue
            seen.add(j); out.append(j)
            score[j] = score.get(j, 0.0) + 10.0 + max(0, 60-pos)*0.2
        if len(out) < min_links:
            raise RuntimeError(f"{canonical_title} hat nur {len(out)} gültige interne Links")
        resolved[pid] = out
        forced.update(out[:min_links])
    selected = set(primary) | forced
    ranked = sorted(score, key=lambda i:(-score[i], titles[i]))
    for i in ranked:
        if len(selected) - 1000 >= connectors:
            break
        selected.add(i)
    if len(selected)-1000 < connectors:
        raise RuntimeError(f"Nur {len(selected)-1000} Connectoren gefunden")
    pset = set(primary)
    conn = [i for i in selected if i not in pset]
    conn.sort(key=lambda i:(-score.get(i,0), titles[i]))
    ids = primary + conn[:connectors]
    print(f"Korpus: 1.000 Primär + {len(ids)-1000:,} Connectoren = {len(ids):,}")
    return ids, primary_titles
