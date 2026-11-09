# Sigma Mega - Max Collect + Super Learn - Mahmoud Emad
import csv, pathlib, math, json, collections
p = pathlib.Path("data/sigma_history.csv")
rows = list(csv.DictReader(open(p, encoding="utf-8")))
def get(r,*ns):
    for n in ns:
        if n in r and str(r[n]).strip() not in ("", "None"): return str(r[n]).strip()
    return None
def num(v):
    try: return int(float(str(v).strip()))
    except: return None
H=[]
for r in rows:
    hg=num(get(r,"home_goals","home_score","hg")); ag=num(get(r,"away_goals","away_score","ag"))
    ht=get(r,"home_team","home","homeTeam"); at=get(r,"away_team","away","awayTeam")
    lg=get(r,"league","competition") or "All"; dt=get(r,"date","match_date") or "2025-01-01"
    if hg is None or ag is None or not ht or not at: continue
    H.append([dt,hg,ag,ht,at,lg])
H.sort(key=lambda x: x[0])
print(f"Collected: {len(H)} real matches")
def pois(l,g): return math.exp(-l)*l**g/math.factorial(g) if l>0 else (1.0 if g==0 else 0.0)
def probs(xh,xa):
    m={}; t=0
    for x in range(11):
        for y in range(11):
            v=pois(xh,x)*pois(xa,y)
            # Dixon-Coles small correction for low scores
            if x==0 and y==0: v*=0.92
            if x==1 and y==0: v*=1.05
            if x==0 and y==1: v*=1.05
            if x==1 and y==1: v*=0.95
            m[(x,y)]=v; t+=v
    hw=sum(v for (x,y),v in m.items() if x>y)/t; dr=sum(v for (x,y),v in m.items() if x==y)/t; aw=sum(v for (x,y),v in m.items() if x<y)/t
    btts=sum(v for (x,y),v in m.items() if x>0 and y>0)/t; over=sum(v for (x,y),v in m.items() if x+y>=3)/t
    return hw,dr,aw,btts,over,m
# Grid search for best params on first 1000 after warmup
def run(home_adv, shrink, elo_w, start=300, end=None):
    elo={}; att={}; defe={}; form={}; h2h={}
    lg_goals=collections.defaultdict(list)
    out=[]
    for i,(dt,hg,ag,ht,at,lg) in enumerate(H):
        # league base from past only
        base=1.35
        if lg_goals[lg]:
            base=sum(lg_goals[lg])/len(lg_goals[lg])/2
            base=max(base,0.8)
        base=max(base,0.8)
        eh=elo.get(ht,1500); ea=elo.get(at,1500)
        ah=att.get(ht,base); dh=defe.get(ht,base); aa=att.get(at,base); da=defe.get(at,base)
        # form bonus: last 5 avg goals diff
        fh=form.get(ht,0); fa=form.get(at,0)
        xh=max(0.15, ah/ base * da/base * base + home_adv + elo_w*(eh-ea)/100 + 0.05*fh)
        xa=max(0.10, aa/base * dh/base * base - home_adv*0.3 + elo_w*(ea-eh)/100 + 0.05*fa)
        if i>=start and (end is None or i<end):
            hw,dr,aw,btts,over,m = probs(xh,xa)
            # shrink to 33%
            hw2=0.333+(1-shrink)*(hw-0.333); dr2=0.333+(1-shrink)*(dr-0.333); aw2=0.333+(1-shrink)*(aw-0.333)
            s=hw2+dr2+aw2; hw2,dr2,aw2=hw2/s,dr2/s,aw2/s
            real=0 if hg>ag else 1 if hg==ag else 2
            brier=(hw2-(1 if real==0 else 0))**2+(dr2-(1 if real==1 else 0))**2+(aw2-(1 if real==2 else 0))**2
            out.append((hw2,dr2,aw2,btts,over,real,hg,ag,round(xh,2),round(xa,2),ht,at,dt,lg,brier))
        # update Elo
        exp_h=1/(1+10**(-(eh+60-ea)/400)); act=1 if hg>ag else 0.5 if hg==ag else 0
        elo[ht]=eh+20*(act-exp_h); elo[at]=ea+20*(exp_h-act)
        # update attack/defense EWMA
        a=0.12
        att[ht]=(1-a)*ah+a*hg; defe[ht]=(1-a)*dh+a*ag
        att[at]=(1-a)*aa+a*ag; defe[at]=(1-a)*da+a*hg
        # form: last 5 goal diff moving
        form[ht]=0.7*fh+0.3*(hg-ag); form[at]=0.7*fa+0.3*(ag-hg)
        lg_goals[lg].append(hg+ag)
        key=tuple(sorted([ht,at]))
        h2h[key]=h2h.get(key,0)+1
    return out, elo, att, defe
best=None
for ha in [0.08,0.15,0.22]:
    for sh in [0.10,0.15,0.20]:
        for ew in [0.0,0.10,0.20]:
            o,_,_,_=run(ha,sh,ew,start=300,end=1300)
            if not o: continue
            b=sum(x[-1] for x in o)/len(o)
            if best is None or b<best[0]: best=(b,ha,sh,ew,len(o))
print(f"Best: Brier={best[0]:.3f} home_adv={best[1]} shrink={best[2]} elo_w={best[3]} on {best[4]} matches")
out, elo, att, defe = run(best[1],best[2],best[3],start=300)
hit=sum(1 for x in out if [x[0],x[1],x[2]].index(max(x[0],x[1],x[2]))==x[5])
exact=sum(1 for x in out if round(x[8])==x[6] and round(x[9])==x[7])
mae=sum(abs((round(x[8])+round(x[9]))-(x[6]+x[7])) for x in out)/len(out)
btts_hit=sum(1 for x in out if (x[3]>0.5)==(x[6]>0 and x[7]>0))
over_hit=sum(1 for x in out if (x[4]>0.5)==(x[6]+x[7]>=3))
print(f"MEGA Learn on {len(out)} matches: Hit {hit}/{len(out)}={hit/len(out)*100:.1f}% Exact {exact}/{len(out)}={exact/len(out)*100:.1f}% MAE {mae:.2f} Brier {best[0]:.3f} BTTS {btts_hit/len(out)*100:.1f}% Over {over_hit/len(out)*100:.1f}%")
# Top attack/defense by Elo-adjusted rating
top_att=sorted(att.items(), key=lambda x: x[1], reverse=True)[:10]
top_def=sorted(defe.items(), key=lambda x: x[1])[:10]
top_elo=sorted(elo.items(), key=lambda x: x[1], reverse=True)[:10]
pathlib.Path("data").mkdir(exist_ok=True)
with open("data/sigma_super_backtest.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["date","match","league","xG_home","xG_away","pred_home","pred_away","real_home","real_away","pick","real","brier"])
    for hw,dr,aw,btts,over,real,hg,ag,xh,xa,ht,at,dt,lg,b in out:
        pick=["1","X","2"][ [hw,dr,aw].index(max(hw,dr,aw)) ]; rr=["1","X","2"][real]
        w.writerow([dt,f"{ht} vs {at}",lg,xh,xa,round(xh),round(xa),hg,ag,pick,rr,round(b,3)])
json.dump({"best_home_adv":best[1],"best_shrink":best[2],"best_elo_w":best[3],"brier":best[0],"hit":hit/len(out),"exact":exact/len(out),"n":len(out)}, open("data/sigma_super_model.json","w",encoding="utf-8"), indent=2)
with open("SUPER_LEARN_REPORT.txt","w",encoding="utf-8") as f:
    f.write(f"Sigma MEGA Super Learn - Mahmoud Emad\nCollected {len(H)} real matches\nBest home_adv={best[1]} shrink={best[2]} elo_w={best[3]}\nHit {hit}/{len(out)}={hit/len(out)*100:.1f}% Exact {exact}/{len(out)}={exact/len(out)*100:.1f}% MAE {mae:.2f} Brier {best[0]:.3f}\nBTTS {btts_hit/len(out)*100:.1f}% Over {over_hit/len(out)*100:.1f}%\n\nTop Elo:\n")
    for t,v in top_elo: f.write(f"{t}: {v:.0f}\n")
    f.write("\nTop Attack:\n")
    for t,v in top_att: f.write(f"{t}: {v:.2f}\n")
    f.write("\nTop Defense (lowest conceded):\n")
    for t,v in top_def: f.write(f"{t}: {v:.2f}\n")
print("Saved: data/sigma_super_backtest.csv + data/sigma_super_model.json + SUPER_LEARN_REPORT.txt")
