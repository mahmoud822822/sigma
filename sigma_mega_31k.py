import csv, pathlib, math, json, collections, re
rows=list(csv.DictReader(open("data/sigma_history.csv", encoding="utf-8")))
def norm(n):
    n=n.strip().lower()
    n=re.sub(r"\b(fc|cf|afc|sc|ac|ssc|us|rcd|real)\b","",n).strip()
    m={"man city":"manchester city","man united":"manchester united","man utd":"manchester united","tottenham":"tottenham hotspur","brighton":"brighton hove albion","wolves":"wolverhampton","leeds":"leeds united","leicester":"leicester city","west ham":"west ham united","west brom":"west bromwich albion","newcastle":"newcastle united","norwich":"norwich city","sheffield utd":"sheffield united","sheff utd":"sheffield united","qpr":"queens park rangers","stoke":"stoke city","swansea":"swansea city","crystal palace":"crystal palace","nottm forest":"nottingham forest","forest":"nottingham forest","birmingham":"birmingham city","blackburn":"blackburn rovers","bolton":"bolton wanderers","wigan":"wigan athletic","sunderland":"sunderland","middlesbrough":"middlesbrough","hull":"hull city","cardiff":"cardiff city","fulham":"fulham","brentford":"brentford","bournemouth":"bournemouth","burnley":"burnley","watford":"watford","everton":"everton","southampton":"southampton"}
    return m.get(n, n)
def get(r,*ns):
    for n in ns:
        if n in r and str(r[n]).strip() not in ("","None"): return str(r[n]).strip()
    return None
def num(v):
    try: return int(float(str(v).strip()))
    except: return None
H=[]
for r in rows:
    hg=num(get(r,"home_goals")); ag=num(get(r,"away_goals"))
    ht=norm(get(r,"home_team","home") or ""); at=norm(get(r,"away_team","away") or "")
    lg=get(r,"league") or "All"; dt=get(r,"date") or "2015-01-01"
    if hg is None or ag is None or not ht or not at: continue
    H.append([dt,hg,ag,ht,at,lg])
H.sort(key=lambda x: x[0])
print(f"Collected normalized: {len(H)}")
def pois(l,g): return math.exp(-l)*l**g/math.factorial(g) if l>0 else (1.0 if g==0 else 0.0)
def probs(xh,xa):
    hw=dr=aw=btts=over=tot=0
    for x in range(11):
        for y in range(11):
            v=pois(xh,x)*pois(xa,y)
            if x==0 and y==0: v*=0.92
            if x==1 and y==0: v*=1.05
            if x==0 and y==1: v*=1.05
            if x==1 and y==1: v*=0.95
            tot+=v
            if x>y: hw+=v
            elif x==y: dr+=v
            else: aw+=v
            if x>0 and y>0: btts+=v
            if x+y>=3: over+=v
    return hw/tot,dr/tot,aw/tot,btts/tot,over/tot
def run(ha,sh,ew,start,end):
    elo={}; att={}; defe={}; form={}; lg_goals=collections.defaultdict(list); out=[]
    for i,(dt,hg,ag,ht,at,lg) in enumerate(H):
        base=1.35
        if lg_goals[lg]: base=max(sum(lg_goals[lg])/len(lg_goals[lg])/2,0.8)
        eh=elo.get(ht,1500); ea=elo.get(at,1500)
        ah=att.get(ht,base); dh=defe.get(ht,base); aa=att.get(at,base); da=defe.get(at,base)
        fh=form.get(ht,0); fa=form.get(at,0)
        rh=ah/base*da/base*base+ha+ew*(eh-ea)/100+0.05*fh; ra=aa/base*dh/base*base-ha*0.3+ew*(ea-eh)/100+0.05*fa
        xh=max(0.15, min(3.5, base+(rh-base)*0.6)); xa=max(0.10, min(3.5, base+(ra-base)*0.6))
        if start<=i<end:
            hw,dr,aw,btts,over=probs(xh,xa)
            hw2=0.333+(1-sh)*(hw-0.333); dr2=0.333+(1-sh)*(dr-0.333); aw2=0.333+(1-sh)*(aw-0.333); s=hw2+dr2+aw2; hw2,dr2,aw2=hw2/s,dr2/s,aw2/s
            real=0 if hg>ag else 1 if hg==ag else 2
            brier=(hw2-(1 if real==0 else 0))**2+(dr2-(1 if real==1 else 0))**2+(aw2-(1 if real==2 else 0))**2
            out.append((hw2,dr2,aw2,btts,over,real,hg,ag,round(xh,2),round(xa,2),ht,at,dt,lg,brier))
        exp_h=1/(1+10**(-(eh+60-ea)/400)); act=1 if hg>ag else 0.5 if hg==ag else 0
        elo[ht]=eh+20*(act-exp_h); elo[at]=ea+20*(exp_h-act)
        a=0.12; att[ht]=(1-a)*ah+a*hg; defe[ht]=(1-a)*dh+a*ag; att[at]=(1-a)*aa+a*ag; defe[at]=(1-a)*da+a*hg
        form[ht]=0.7*fh+0.3*(hg-ag); form[at]=0.7*fa+0.3*(ag-hg); lg_goals[lg].append(hg+ag)
    return out, elo, att, defe
best=None
for ha in [0.08,0.15,0.22]:
    for sh in [0.10,0.15,0.20]:
        for ew in [0.0,0.10]:
            o,_,_,_=run(ha,sh,ew,500,2500)
            b=sum(x[-1] for x in o)/len(o)
            if best is None or b<best[0]: best=(b,ha,sh,ew)
print(f"Best 31k: Brier={best[0]:.3f} home_adv={best[1]} shrink={best[2]} elo_w={best[3]}")
# Final eval on last 5000 - الاحدث
out, elo, att, defe = run(best[1],best[2],best[3], len(H)-5000, len(H))
hit=sum(1 for x in out if [x[0],x[1],x[2]].index(max(x[0],x[1],x[2]))==x[5])
exact=sum(1 for x in out if round(x[8])==x[6] and round(x[9])==x[7])
mae=sum(abs((round(x[8])+round(x[9]))-(x[6]+x[7])) for x in out)/len(out)
btts=sum(1 for x in out if (x[3]>0.5)==(x[6]>0 and x[7]>0))/len(out)*100
over=sum(1 for x in out if (x[4]>0.5)==(x[6]+x[7]>=3))/len(out)*100
print(f"MEGA 31k - Last 5000: Hit {hit}/{len(out)}={hit/len(out)*100:.1f}% Exact {exact/len(out)*100:.1f}% MAE {mae:.2f} Brier {best[0]:.3f} BTTS {btts:.1f}% Over {over:.1f}%")
top_elo=sorted(elo.items(), key=lambda x: x[1], reverse=True)[:10]
top_att=sorted(att.items(), key=lambda x: x[1], reverse=True)[:10]
top_def=sorted(defe.items(), key=lambda x: x[1])[:10]
json.dump({"best_home_adv":best[1],"best_shrink":best[2],"best_elo_w":best[3],"brier":best[0],"hit":hit/len(out),"exact":exact/len(out),"n":len(out),"total_history":len(H)}, open("data/sigma_super_model.json","w"), indent=2)
with open("SUPER_LEARN_REPORT.txt","w",encoding="utf-8") as f:
    f.write(f"Sigma MEGA 31k - Mahmoud Emad\nTotal History {len(H)}\nBest home_adv={best[1]} shrink={best[2]} elo_w={best[3]}\nHit {hit}/{len(out)}={hit/len(out)*100:.1f}% Exact {exact/len(out)*100:.1f}% MAE {mae:.2f} Brier {best[0]:.3f} BTTS {btts:.1f}% Over {over:.1f}%\n\nTop Elo:\n")
    for t,v in top_elo: f.write(f"{t}: {v:.0f}\n")
    f.write("\nTop Attack:\n")
    for t,v in top_att: f.write(f"{t}: {v:.2f}\n")
    f.write("\nTop Defense:\n")
    for t,v in top_def: f.write(f"{t}: {v:.2f}\n")
print("Saved: SUPER_LEARN_REPORT.txt + data/sigma_super_model.json")
