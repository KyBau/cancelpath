"""Re-fetch each verified source and derive clean excerpts + steps strictly from source text."""
import json,re,html,subprocess
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
UA="Mozilla/5.0 (X11; Linux x86_64) Chrome/128 Safari/537.36"
NAV=re.compile(r"help center|sign in|join netflix|skip to|cookie|explore premium|install app|log in to your|search|menu|privacy|terms of use|copyright|©|was this (article )?helpful|related articles|contact us|need more help|-->|\|",re.I)
KEY=re.compile(r"cancel|subscri|membership|plan|renew|billing|account|settings|select|tap|click|go to|open|confirm|refund|trial|apple|google play",re.I)
def curl(u): return subprocess.run(["curl","-sL","-m","20","-A",UA,u],capture_output=True,text=True,errors="ignore",timeout=25).stdout
def text(h): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",h))).strip()
def body_html(v):
    u=v["source_url"]
    m=re.search(r"/articles/(\d+)",u)
    if v["verification_method"]=="official_help_api" and m:
        host=urlparse(u).netloc
        try: return json.loads(curl(f"https://{host}/api/v2/help_center/articles/{m.group(1)}.json"))["article"]["body"]
        except Exception: return ""
    h=curl(u); h=re.sub(r"(?is)<(script|style|noscript|nav|header|footer|svg)[^>]*>.*?</\1>"," ",h)
    mm=re.search(r"(?is)<(main|article)[^>]*>(.*?)</\1>",h); return mm.group(2) if mm else h
STRICT=re.compile(r"cookie|©|copyright|was this (article )?helpful|related articles|skip to|-->|'>|heading-label|is-app=|recommended topics|a country must be selected",re.I)
VERB=re.compile(r"^(go|select|tap|click|open|sign|log|choose|under|in|on|from|follow|visit|confirm|continue|find|navigate|scroll|enter|head|press|toggle|turn|review|check|using|at the|next to|then|if you subscribed|to cancel)\b",re.I)
def ok(s): return 15<len(s)<260 and not NAV.search(s)
def okstep(s):
    s=s.replace("\u200b","").strip()
    return 15<len(s)<260 and len(s.split())>=3 and not STRICT.search(s) and VERB.search(s) and not re.search(r"\b(pause|extend|resume|reactivat|restart|rejoin|upgrade|change plan|switch plan)",s,re.I)
def clean(item):
    k,v=item
    if v["verification_method"]=="official_page_via_search": return k,v,"kept"
    h=body_html(v)
    if not h: return k,v,"nofetch"
    lis=[text(x) for x in re.findall(r"(?is)<li[^>]*>(.*?)</li>",h)]
    seen=set();steps=[]
    for x in lis:
        x=re.sub(r"\s+([.,])",r"\1",x.replace("\u200b","")).strip()
        if okstep(x) and x.lower() not in seen: seen.add(x.lower()); steps.append(x)
    steps=steps[:7]
    t=text(re.sub(r"(?is)<li[^>]*>.*?</li>"," ",h))
    sents=[s.strip() for s in re.split(r"(?<=[.!?])\s+",t)]
    ex=[s.replace("\u200b","").replace("\ufeff","").strip() for s in sents if ok(s) and not STRICT.search(s) and re.search(r"cancel",s,re.I)][:4]
    if not steps: steps=[s for s in sents if okstep(s)][:6]
    v=dict(v); v["evidence_excerpts"]=ex; v["steps"]=steps or None
    v["notes"]="Steps and excerpts are verbatim from the source page." if steps else "No step list on source page; see excerpts and source_url."
    return k,v,"ok" if (steps or len(ex)>=1) else "empty"
d=json.load(open("playbooks.json"))
with ThreadPoolExecutor(12) as ex: res=list(ex.map(clean,d.items()))
from collections import Counter; print(Counter(r[2] for r in res))
out={k:v for k,v,s in res}
print([k for k,v,s in res if s in("nofetch","empty")])
json.dump(out,open("playbooks.cleaned.json","w"),indent=1)
