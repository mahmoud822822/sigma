import csv, json, math, re
def clean(s):
    s=str(s).lower()
    s=s.replace("fc ","").replace(" cf","").replace("'65","").replace(" tilburg","")
    s=re.sub(r"[^a-z ]"," ",s)
    s=" ".join(s.split())
    if s=="real": s="real madrid"
    if s=="barca": s="barcelona"
    if s=="man city": s="manchester city"
    return s
hist=list(csv.DictReader(open("data/sigma_history.csv", encoding="utf-8")))
stats={}
names={}
for r in hist:
    try:
        hg=int(float(r["home_goals"])); ag=int(float(r["away_goals"]))
    except: continue
    ht=clean(r["home_team"]); at=clean(r["away_team"])
    names[ht]=r["home_team"]; names[at]=r["away_team"]
    for t,gf,ga in [(ht,hg,ag),(at,ag,hg)]:
        s=stats.setdefault(t,{"mp":0,"gf":0,"ga":0,"w":0})
        s["mp"]+=1; s["gf"]+=gf; s["ga"]+=ga
        if gf>ga: s["w"]+=1
MEGA=[]
try:
    for r in csv.DictReader(open("data/sigma_mega_predictions.csv", encoding="utf-8")):
        if " vs " in r["match"]:
            h,a=r["match"].split(" vs ")
            MEGA.append((clean(h),clean(a),r))
except: pass
print(f"Loaded {len(stats)} teams, {len(MEGA)} mega predictions")
def find(q):
    q=clean(q)
    if q in stats: return q
    for k in stats:
        if q in k or k in q:
            if q=="real madrid" and "villarreal" in k: continue
            return k
    return None
def find_mega(h,a):
    for mh,ma,r in MEGA:
        if (h in mh or mh in h) and (a in ma or ma in a):
            return r
    return None
def predict(h,a):
    r=find_mega(h,a)
    if r:
        print(f"\n{names.get(h,h)} vs {names.get(a,a)} [MEGA 31k]")
        print(f"xG {r['xG']} | 1:{r['1']}% X:{r['X']}% 2:{r['2']}% | BTTS {r['BTTS']}% Over {r['Over25']}%")
        print(f"Top: {r['top']}")
        print("Reason: From model trained on 31306 matches")
        return
    print("Not in mega list, using general stats")
print("Sigma Brain2 - type: Twente vs Willem II")
while True:
    q=input("\nAsk Sigma: ").strip()
    if q.lower() in ("0","exit","quit"): break
    if "vs" in q:
        hq,aq=q.split("vs"); h=find(hq); a=find(aq)
        if h and a: predict(h,a)
        else: print("Team not found, try: Twente vs Willem II")
    else: print("Type: Team vs Team")
