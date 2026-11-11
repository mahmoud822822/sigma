import json, csv, pathlib, math, collections
# Load best model
m=json.load(open("data/sigma_super_model.json", encoding="utf-8"))
HA=m["best_home_adv"]; SH=m["best_shrink"]
print(f"Using MEGA: home_adv={HA} shrink={SH} Brier={m['brier']:.3f}")
# Build final ratings from all history
rows=list(csv.DictReader(open("data/sigma_history.csv", encoding="utf-8")))
def get(r,*ns):
    for n in ns:
        if n in r and str(r[n]).strip() not in ("","None"): return str(r[n]).strip()
    return None
def num(v):
    try: return int(float(str(v).strip()))
    except: return None
H=[]
for r in rows:
    hg=num(get(r,"home_goals","home_score")); ag=num(get(r,"away_goals","away_score"))
    ht=get(r,"home_team","home"); at=get(r,"away_team","away")
    if hg is None or ag is None: continue
    H.append([get(r,"date") or "2025-01-01",hg,ag,ht,at])
H.sort(key=lambda x: x[0])
att={}; defe={}; lg={}; 
for dt,hg,ag,ht,at in H:
    base=1.35
    ah=att.get(ht,base); dh=defe.get(ht,base); aa=att.get(at,base); da=defe.get(at,base)
    a=0.12
    att[ht]=(1-a)*ah+a*hg; defe[ht]=(1-a)*dh+a*ag
    att[at]=(1-a)*aa+a*ag; defe[at]=(1-a)*da+a*hg
def pois(l,g): return math.exp(-l)*l**g/math.factorial(g) if l>0 else (1.0 if g==0 else 0.0)
# Next matches
data=json.load(open("data/sigma_next_month.json", encoding="utf-8"))
items=data if isinstance(data,list) else data.get("matches",[])
out=[]
for mm in items:
    if "match" in mm and " vs " in str(mm["match"]):
        ht,at=str(mm["match"]).split(" vs ")
    else:
        ht=mm.get("homeTeam",{}).get("name","?") if isinstance(mm.get("homeTeam"),dict) else mm.get("homeTeam","?")
        at=mm.get("awayTeam",{}).get("name","?") if isinstance(mm.get("awayTeam"),dict) else mm.get("awayTeam","?")
    base=1.35; ah=att.get(ht,base); da=defe.get(at,base); aa=att.get(at,base); dh=defe.get(ht,base)
    bs=max(base,0.8)
    xh=max(0.15, ah/bs*da/bs*base+HA); xa=max(0.10, aa/bs*dh/bs*base-HA*0.3)
    hw=dr=aw=0; btts=over=0; tot=0; mp={}
    for x in range(11):
        for y in range(11):
            v=pois(xh,x)*pois(xa,y); mp[(x,y)]=v; tot+=v
    hw=sum(v for (x,y),v in mp.items() if x>y)/tot; dr=sum(v for (x,y),v in mp.items() if x==y)/tot; aw=sum(v for (x,y),v in mp.items() if x<y)/tot
    hw2=0.333+(1-SH)*(hw-0.333); dr2=0.333+(1-SH)*(dr-0.333); aw2=0.333+(1-SH)*(aw-0.333); s=hw2+dr2+aw2; hw2,dr2,aw2=hw2/s,dr2/s,aw2/s
    out.append({"date":mm.get("date",""),"match":f"{ht} vs {at}","league":mm.get("league",""),"xG":f"{xh:.2f}-{xa:.2f}","1":round(hw2*100,1),"X":round(dr2*100,1),"2":round(aw2*100,1),"conf":round(max(hw2,dr2,aw2)*100,1)})
out=sorted(out, key=lambda x: x["conf"], reverse=True)
print(f"MEGA Predictions: {len(out)}")
for o in out[:10]: print(f"{o['date']} {o['match']} xG {o['xG']} 1:{o['1']}% X:{o['X']}% 2:{o['2']}%")
with open("data/sigma_mega_predictions.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=["date","match","league","xG","1","X","2","conf"]); w.writeheader(); w.writerows(out)
print("Saved: data/sigma_mega_predictions.csv")
