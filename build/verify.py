import csv,re,json,subprocess,html,datetime
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36"
def fetch(row):
    name,url=row
    try:
        p=subprocess.run(["curl","-sL","-m","20","-A",UA,"-w","\n__META__%{http_code} %{url_effective}",url],capture_output=True,text=True,errors="ignore",timeout=25).stdout
    except Exception as e: return name,url,None,"timeout"
    body,_,meta=p.rpartition("\n__META__"); code,_,final=meta.partition(" ")
    t=re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>"," ",body); t=html.unescape(re.sub(r"<[^>]+>"," ",t)); t=re.sub(r"\s+"," ",t)
    sents=[s.strip() for s in re.split(r"(?<=[.!?])\s+",t) if re.search(r"\bcancel",s,re.I) and 25<len(s)<300]
    bad=re.search(r"captcha|access denied|are you a robot|enable javascript|page not found|404",t[:3000],re.I)
    base=lambda u:".".join(urlparse(u).netloc.split(".")[-2:])
    ok=code=="200" and len(sents)>=2 and not bad and base(final)==base(url)
    return name,url,{"code":code,"final":final,"snips":sents[:4]} if ok else None,f"{code} sents={len(sents)} bad={bool(bad)}"
rows=[r for r in csv.reader(open("candidates.tsv"),delimiter="\t")]
out,fail=[],[]
with ThreadPoolExecutor(16) as ex:
    for name,url,res,why in ex.map(fetch,rows):
        (out.append({"merchant":name,"source_url":res["final"],"evidence":res["snips"]}) if res else fail.append((name,url,why)))
json.dump(out,open("verified_raw.json","w"),indent=1); json.dump(fail,open("failed.json","w"),indent=1)
print(len(out),"ok",len(fail),"fail")
