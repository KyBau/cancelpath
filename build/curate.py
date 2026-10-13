"""Manual trims: keep only cancellation-relevant verbatim lines (subsets of auto-extracted steps)."""
import json
d=json.load(open("playbooks.cleaned.json"))
pick={"netflix":[0,1,2],"spotify":[0,1],"siriusxm":[0,1],"box":[0,3,4,5,6],"new-york-times":[2,3,4,5],"typeform":[1,2,4,5],"fitbod":[0,1,3,4,5,6]}
for k,ix in pick.items(): d[k]["steps"]=[d[k]["steps"][i] for i in ix]
for k in ["notion","t-mobile","talkspace","hinge","backblaze"]:
    d[k]["steps"]=None; d[k]["notes"]="Source page has no clean cancellation step list; see excerpts and source_url."
d.pop("shopify")  # source covers pausing a store, not cancelling
json.dump(d,open("../playbooks.json" if False else "playbooks.json","w"),indent=1,ensure_ascii=False)
print(len(d))
