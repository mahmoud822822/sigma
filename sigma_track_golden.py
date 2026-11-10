import csv, pathlib
# بيقارن توقع 【entity-Golden¦canonical_name=Golden】 مع النتيجة الحقيقية من history
hist=list(csv.DictReader(open("data/sigma_history.csv", encoding="utf-8"))) if pathlib.Path("data/sigma_history.csv").exists() else []
def norm(s): return (s or "").lower().strip()
def same(a,b):
    a=norm(a); b=norm(b)
    return a==b or a in b or b in a
def find_result(match):
    try: h,a=match.split(" vs ")
    except: return None
    for r in hist:
        hh=r.get("home") or r.get("home_team") or ""
        aa=r.get("away") or r.get("away_team") or ""
        if same(hh,h) and same(aa,a):
            try: return int(float(r.get("home_goals",0))), int(float(r.get("away_goals",0))), r.get("date","")
            except: continue
    return None
rows=list(csv.DictReader(open("data/sigma_insight.csv", encoding="utf-8")))
hit=tot=0
for r in rows:
    res=find_result(r["match"])
    if not res: continue
    hg,ag,dt=res
    tot+=1
    g=r.get("Golden","")
    ok=False
    if "1X" in g and hg>=ag: ok=True
    if "X2" in g and hg<=ag: ok=True
    if "12" in g and hg!=ag: ok=True
    if "Over 0.5" in g and hg+ag>0: ok=True
    if "Over 1.5" in g and hg+ag>1: ok=True
    if "Under 4.5" in g and hg+ag<5: ok=True
    if ok: hit+=1
print(f"Golden Track: {hit}/{tot} = {hit/tot*100:.1f}% - from Real History" if tot else "Golden Track: No finished yet")
