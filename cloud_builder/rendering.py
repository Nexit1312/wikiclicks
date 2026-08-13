import html,re,mwparserfromhell
from common import norm_title,SPACE_RE
from mwparserfromhell.nodes import Text,Wikilink,Tag
TAG_RE=re.compile(r"<[^>]+>")

def render_article(raw,allowed,canon,max_links=120):
    links=[];seen=set();out=[]
    def walk(nodes):
        buf=[]
        for n in nodes:
            if isinstance(n,Text):buf.append(html.escape(str(n)))
            elif isinstance(n,Wikilink):
                t=canon.get(norm_title(str(n.title).split("#",1)[0]),norm_title(str(n.title).split("#",1)[0]))
                label=html.escape(mwparserfromhell.parse(str(n.text if n.text is not None else n.title)).strip_code(normalize=True,collapse=True))
                if t in allowed and (t in seen or len(links)<max_links):
                    if t not in seen:seen.add(t);links.append(t)
                    buf.append(f'<a href="#" data-wiki-title="{html.escape(t,quote=True)}">{label}</a>')
                else:buf.append(label)
            elif isinstance(n,Tag) and n.contents is not None and str(n.tag).lower() not in {"ref","gallery","math"}:buf.append(walk(n.contents.nodes))
        return "".join(buf)
    code=mwparserfromhell.parse(raw or "")
    total=0
    for i,sec in enumerate(code.get_sections(include_lead=True,include_headings=True,flat=True)[:15]):
        body=walk(sec.nodes);paras=[]
        for p in re.split(r"\n\s*\n",body):
            p=SPACE_RE.sub(" ",p).strip()
            if len(TAG_RE.sub("",p))>=35:paras.append(f"<p>{p}</p>")
        body="".join(paras);plain=TAG_RE.sub("",body)
        if not body:continue
        if total and total+len(plain)>30000 and len(links)>=24:break
        total+=len(plain)
        out.append(f'<section class="article-section open"><div class="section-body">{body}</div></section>' if i==0 else f'<section class="article-section"><button class="section-toggle" aria-expanded="false"><span>Abschnitt</span><b>＋</b></button><div class="section-body">{body}</div></section>')
    return "".join(out),links
