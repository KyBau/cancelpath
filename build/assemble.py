import json,re,datetime
from search_verified import S
D="2026-10-13"
drop={"Vimeo","Britbox","Figma","Memrise","Wyze","Calm Sleep","Apple Music","Apple TV+","Spotify Family","Webflow","NordVPN","Quizlet","Rover","Medium","Fubo"}
rename={"Life360":"Tile Premium","Apple subscriptions":"Apple (App Store subscriptions)","NYTimes":"New York Times","DoorDash DashPass":"DoorDash DashPass","Discord Nitro":"Discord Nitro"}
raw={}
for f in ["zd2.json","zd3.json","zd4.json","zd5.json","verified_raw.json"]:
    for x in json.load(open(f)): raw.setdefault(x["merchant"],x)
out={}
def slug(n): return re.sub(r"[^a-z0-9]+","-",n.lower()).strip("-")
for n,x in raw.items():
    if n in drop: continue
    n=rename.get(n,n)
    ev=[e for e in x["evidence"] if len(e)<280][:4]
    out[slug(n)]={"merchant":n,"source_url":x["source_url"],"source_title":x.get("title"),"verified_date":D,
      "verification_method":"official_help_api" if x.get("title") else "official_page_fetch","evidence_excerpts":ev,"steps":None,"channel":None,"notes":"Steps not paraphrased; follow evidence excerpts / source page."}
for n,u,ch,steps,notes in S:
    out[slug(n)]={"merchant":n,"source_url":u,"source_title":None,"verified_date":D,"verification_method":"official_page_via_search","evidence_excerpts":[],"steps":steps,"channel":ch,"notes":notes}
for a in ["netflix","spotify","youtube-premium"]: pass
json.dump(dict(sorted(out.items())),open("../playbooks.json","w"),indent=1)
print(len(out))
