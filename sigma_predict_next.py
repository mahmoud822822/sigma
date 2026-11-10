import json, csv, math, pathlib, unicodedata, re
m=json.load(open("data/sigma_super_model.json", encoding="utf-8"))
HA=m["best_home_adv"]; SH=m["best_shrink"]
print(f"Using MEGA 31k: HA={HA} SH={SH} Brier={m['brier']:.3f}")
def clean(n):
    n=unicodedata.normalize("NFKD", str(n)).encode("ascii","ignore").decode()
    n=n.lower().strip(); n=re.sub(r"[^a-z0-9 ]","",n)
    n=re.sub(r"\b(fc|cf|afc|sc|ac|ssc|us|rcd|real|club)\b","",n).strip()
    n=re.sub(r"\s+"," ",n)
    if "munchen" in n: n=n.replace("munchen","munich")
    if "eindhoven" in n: return "p"+"sv"
    if n.startswith("p"+"sv"): return "p"+"sv"
    if "bay" in n and "ern" in n: return "ba"+"yern"
    if n in ("lille osc","lille"): return "li"+"lle"
    if n.startswith("paris"): return "paris saint germ"+"ain"
    if "sporting" in n or n.startswith("sp lisbon"): return "sporting lis"+"bon"
    if "man city" in n or "manchester city" in n: return "manchester ci"+"ty"
    return n
def pois(l,g): return math.exp(-l)*l**g/math.factorial(g) if l>0 else (1.0 if g==0 else 0.0)
rows=list(csv.DictReader(open("data/sigma_history.csv", encoding="utf-8")))
H=[]
for r in rows:
    try: hg=int(float(r["home_goals"])); ag=int(float(r["away_goals"]))
    except: continue
    H.append([r["date"],hg,ag,clean((r.get("home") or r.get("home_team") or "")),clean((r.get("away") or r.get("away_team") or ""))])
H.sort(key=lambda x: x[0])
att={}; defe={}
for dt,hg,ag,ht,at in H:
    base=1.35; ah=att.get(ht,base); dh=defe.get(ht,base); aa=att.get(at,base); da=defe.get(at,base)
    a=0.12; att[ht]=(1-a)*ah+a*hg; defe[ht]=(1-a)*dh+a*ag; att[at]=(1-a)*aa+a*ag; defe[at]=(1-a)*da+a*hg
print(f"Ratings: {len(att)} teams from {len(H)}")
data=json.load(open("data/sigma_next_month.json", encoding="utf-8")); items=data if isinstance(data,list) else data.get("matches",[])
out=[]
for mm in items:
    if "match" in mm and " vs " in str(mm["match"]): raw_ht,raw_at=str(mm["match"]).split(" vs ")
    else:
        h0=mm.get("homeTeam",{}); a0=mm.get("awayTeam",{})
        raw_ht=h0.get("name","?") if isinstance(h0,dict) else str(h0); raw_at=a0.get("name","?") if isinstance(a0,dict) else str(a0)
    ht=clean(raw_ht); at=clean(raw_at); base=1.35
    ah=att.get(ht,base); da=defe.get(at,base); aa=att.get(at,base); dh=defe.get(ht,base)
    raw_h=ah/base*da/base*base+HA; raw_a=aa/base*dh/base*base-HA*0.3
    xh=max(0.15, min(3.5, base+(raw_h-base)*0.6)); xa=max(0.10, min(3.5, base+(raw_a-base)*0.6))
    mp={}; tot=0
    for x in range(11):
        for y in range(11):
            v=pois(xh,x)*pois(xa,y)
            if x==0 and y==0: v*=0.92
            if x==1 and y==0: v*=1.05
            if x==0 and y==1: v*=1.05
            if x==1 and y==1: v*=0.95
            mp[(x,y)]=v; tot+=v
    hw=sum(v for (x,y),v in mp.items() if x>y)/tot; dr=sum(v for (x,y),v in mp.items() if x==y)/tot; aw=sum(v for (x,y),v in mp.items() if x<y)/tot
    btts=sum(v for (x,y),v in mp.items() if x>0 and y>0)/tot; over=sum(v for (x,y),v in mp.items() if x+y>=3)/tot
    hw2=0.333+(1-SH)*(hw-0.333); dr2=0.333+(1-SH)*(dr-0.333); aw2=0.333+(1-SH)*(aw-0.333); s=hw2+dr2+aw2; hw2,dr2,aw2=hw2/s,dr2/s,aw2/s
    top=sorted(mp.items(), key=lambda z: z[1], reverse=True)[:3]
    top_s=", ".join([f"{x}-{y} {v/tot*100:.1f}%" for (x,y),v in top])
    out.append({"date":mm.get("date",""),"match":f"{raw_ht} vs {raw_at}","league":mm.get("league",""),"xG":f"{xh:.2f}-{xa:.2f}","1":round(hw2*100,1),"X":round(dr2*100,1),"2":round(aw2*100,1),"BTTS":round(btts*100,1),"Over25":round(over*100,1),"conf":round(max(hw2,dr2,aw2)*100,1),"top":top_s})
out=sorted(out, key=lambda x: x["conf"], reverse=True)
print(f"MEGA Predictions: {len(out)}")
for o in out[:10]: print(f"{o['date']} {o['match']} xG {o['xG']} 1:{o['1']}% X:{o['X']}% 2:{o['2']}% BTTS:{o['BTTS']}% Top:{o['top']}")
with open("data/sigma_mega_predictions.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=["date","match","league","xG","1","X","2","BTTS","Over25","conf","top"]); w.writeheader(); w.writerows(out)
print("Saved: data/sigma_mega_predictions.csv")
