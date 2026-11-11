# Signature Prediction and Forecast: Sigma - Mahmoud Emad
import math, re, json, os, csv, shutil
from datetime import date
def poisson(lam,g):
    return (math.exp(-lam)*lam**g)/math.factorial(g)
def get_num(prompt, default):
    s = input(prompt).strip()
    if not s: return default
    m = re.search(r"\d+\.\d+|\d+", s)
    if not m: return default
    try:
        v = float(m.group(0))
        return v if 0 < v <= 8 else default
    except: return default
def pred(h,a, show=True):
    m={}; t=0.0
    for x in range(11):
        for y in range(11):
            p=poisson(h,x)*poisson(a,y); m[(x,y)]=p; t+=p
    m={k:v/t for k,v in m.items()}
    hw=sum(p for (x,y),p in m.items() if x>y); d=sum(p for (x,y),p in m.items() if x==y); aw=sum(p for (x,y),p in m.items() if x<y)
    btts=sum(p for (x,y),p in m.items() if x>0 and y>0); over25=sum(p for (x,y),p in m.items() if x+y>=3)
    try:
        import json as _j; _sh=_j.load(open('data/sigma_super_model.json', encoding='utf-8')).get('best_shrink',0.1)
        hw=0.333+(1-_sh)*(hw-0.333); d=0.333+(1-_sh)*(d-0.333); aw=0.333+(1-_sh)*(aw-0.333); _s=hw+d+aw; hw,d,aw=hw/_s,d/_s,aw/_s
    except: pass
    if show:
        print(f"1: {hw*100:.1f}%  X: {d*100:.1f}%  2: {aw*100:.1f}%")
        print(f"BTTS: {btts*100:.1f}%  Over 2.5: {over25*100:.1f}%")
        top=sorted(m.items(), key=lambda z:z[1], reverse=True)[:3]
        print("Top:", ", ".join([f"{x}-{y} {p*100:.1f}%" for (x,y),p in top]))
    return hw,d,aw,m,btts,over25
def grade_for(n, dq):
    if n>=30: return "A"
    if n>=15: return "B"
    if n>=5: return "C"
    return "D"
def load_verified():
    rows=[]
    for cand in ["data/sigma_real_verified.csv","sigma_real_verified.csv"]:
        if os.path.exists(cand):
            rows=list(csv.DictReader(open(cand, encoding="utf-8"))); break
    return rows
def team_stats():
    for cand in ["data/sigma_team_stats.json","sigma_team_stats.json"]:
        if os.path.exists(cand):
            try:
                j=json.load(open(cand, encoding="utf-8"))
                out={}
                for team, s in j.items():
                    out[team]={"n":s["n"],"scored":s["scored_avg"]*s["n"],"conceded":s["conceded_avg"]*s["n"],"home_scored":s.get("home_scored_avg",1.55),"away_scored":s.get("away_scored_avg",1.25),"home_conceded":s.get("home_conceded_avg",1.25),"away_conceded":s.get("away_conceded_avg",1.55),"btts_rate":s.get("btts_rate",50),"over25_rate":s.get("over25_rate",50),"form":s.get("form",""),"source":"history50"}
                return out
            except: pass
    rows=load_verified(); stats={}
    for r in rows:
        try:
            h,a=r["match"].split(" vs "); rh=int(r["real_home"]); ra=int(r["real_away"])
        except: continue
        for team, scored, conceded in [(h,rh,ra),(a,ra,rh)]:
            s=stats.get(team, {"n":0,"scored":0,"conceded":0})
            s["n"]+=1; s["scored"]+=scored; s["conceded"]+=conceded; stats[team]=s
    return stats

def find_team(stats, inp):
    if not inp: return None
    if inp in stats: return inp
    low = inp.lower().strip()
    for k in stats:
        if k.lower()==low: return k
    aliases = {"man city":"manchester city","man utd":"manchester united","man united":"manchester united","barca":"barcelona","real":"real madrid","spurs":"tottenham","psg":"paris saint","milan":"ac milan","inter":"inter","juve":"juventus","porto":"porto","benfica":"benfica","ajax":"ajax","psv":"psv","feyenoord":"feyenoord","atletico":"atletico","sevilla":"sevilla","valencia":"valencia","chelsea":"chelsea","arsenal":"arsenal","liverpool":"liverpool","city":"manchester city","united":"manchester united"}
    if low in aliases:
        want = aliases[low]
        for k in stats:
            if want in k.lower(): return k
    for k in stats:
        kl = k.lower()
        if low in kl or kl in low: return k
    parts = low.split()
    if parts:
        for k in stats:
            if parts[0] in k.lower(): return k
    return None

def predict_by_team():
    home=input("Home team: ").strip()
    away=input("Away team: ").strip()
    if not home or not away:
        print("اكتب الفريقين"); return
    stats=team_stats()
    base_h, base_a = 1.55, 1.25
    _rh = find_team(stats, home); _ra = find_team(stats, away)
    if _rh: print(f"Found: {home} -> {_rh}")
    if _ra: print(f"Found: {away} -> {_ra}")
    home = _rh or home; away = _ra or away
    hs=stats.get(home); aws=stats.get(away)
    def xg(team, is_home, opp):
        s=stats.get(team)
        if s and s.get("source")=="history50":
            base = s["home_scored"] if is_home else s["away_scored"]
            opp_conc = None
            if opp and opp.get("source")=="history50":
                opp_conc = opp["away_conceded"] if is_home else opp["home_conceded"]
            if opp_conc is not None:
                base = base * (opp_conc/1.35)
            base2=1.35+(base-1.35)*0.6+(0.22 if is_home else -0.066)
            return round(max(0.15,min(3.5, base2)),2)
        if s and s["n"]>=2:
            avg_scored=s["scored"]/s["n"]
            return round((s["n"]*avg_scored + 2*(base_h if is_home else base_a))/(s["n"]+2),2)
        return round(base_h*1.08 if is_home else base_a,2)
    h=xg(home, True, aws); a=xg(away, False, hs)
    n = min(hs["n"] if hs else 0, aws["n"] if aws else 0)
    dq = "full" if n>=30 else ("good" if n>=15 else "partial")
    src = "history50" if (hs and hs.get("source")=="history50") else f"verified{len(load_verified())}"
    print(f"{home} vs {away}  xG: {h} - {a}  n={n} dq={dq} src={src}")
    if hs: print(f"  {home}: n={hs['n']} scored={hs.get('home_scored',0)} form={hs.get('form','')}")
    if aws: print(f"  {away}: n={aws['n']} scored={aws.get('away_scored',0)} form={aws.get('form','')}")
    hw,d,aw,m,btts,over25 = pred(h,a, show=True)
    g=grade_for(n, dq)
    print(f"Grade: {g} - Source: {src} + League Avg - No invented lineup")
def match_list():
    p1="data/sigma_next_month.json"; p2="sigma_next_month.json"
    path = p1 if os.path.exists(p1) else p2 if os.path.exists(p2) else None
    if not path: print("No file: data/sigma_next_month.json"); return
    try:
        with open(path, encoding="utf-8") as f: data=json.load(f)
        items = data if isinstance(data, list) else data.get("matches", data.get("data", []))
        q=input("Search team (Enter = all): ").strip().lower()
        if q: items=[x for x in items if q in str(x).lower()]
        print(f"Matches: {len(items)}")
        for i,mm in enumerate(items[:20],1):
            date=str(mm.get("date", mm.get("utcDate","")))[:10]
            if "match" in mm and isinstance(mm["match"], str) and " vs " in mm["match"]:
                print(f"{i}. {date} {mm['match']}  [{mm.get('league','')}]"); continue
            home=mm.get("homeTeam", mm.get("home","?")); away=mm.get("awayTeam", mm.get("away","?"))
            if isinstance(home, dict): home=home.get("name","?")
            if isinstance(away, dict): away=away.get("name","?")
            print(f"{i}. {date} {home} vs {away}")
        if len(items)>20: print(f"... +{len(items)-20} more")
    except Exception as e: print("Error:", e)
def evaluation():
    rows=load_verified()
    if not rows: print("No verified file"); return
    hit=0; exact=0; mae=0.0; n=0
    for r in rows:
        try: ph=int(r["predicted_home"]); pa=int(r["predicted_away"]); rh=int(r["real_home"]); ra=int(r["real_away"])
        except: continue
        n+=1; pick="1" if ph>pa else "X" if ph==pa else "2"; real="1" if rh>ra else "X" if rh==ra else "2"
        if pick==real: hit+=1
        if ph==rh and pa==ra: exact+=1
        mae+=abs((ph+pa)-(rh+ra))
    print(f"Evaluation - {n} matches")
    print(f"Hit: {hit}/{n} = {hit/n*100:.1f}%")
    print(f"Exact: {exact}/{n} = {exact/n*100:.1f}%")
    print(f"MAE goals: {mae/n:.2f}")
def do_fetch():
    import subprocess, sys
    if os.path.exists("data/sigma_next_month.json"):
        try: shutil.copy("data/sigma_next_month.json", "data/sigma_next_month.backup.json"); print("Backup: data/sigma_next_month.backup.json")
        except: pass
    if os.path.exists("sigma_auto_fetch.py"):
        print("Running sigma_auto_fetch.py ...")
        r=subprocess.run([sys.executable, "sigma_auto_fetch.py"]); print(f"Fetch exit: {r.returncode}"); return
    print("No file: sigma_auto_fetch.py")
def predict_all():
    p1="data/sigma_next_month.json"
    if not os.path.exists(p1): print("No file: data/sigma_next_month.json - Run 5 Fetch first"); return
    data=json.load(open(p1, encoding="utf-8")); items=data if isinstance(data, list) else data.get("matches", [])
    league_avg={"England":(1.65,1.35),"Spain":(1.55,1.20),"Italy":(1.50,1.20),"Germany":(1.70,1.40),"Netherlands":(1.70,1.40),"France":(1.55,1.25),"Portugal":(1.55,1.20),"Belgium":(1.60,1.30),"PL":(1.65,1.35),"PD":(1.55,1.20),"SA":(1.50,1.20),"BL1":(1.70,1.40),"FL1":(1.55,1.25),"DED":(1.70,1.40),"PPL":(1.55,1.20),"JPL":(1.60,1.30)}
    stats=team_stats()
    out=[]
    for mm in items:
        league=mm.get("league","Default"); bh,ba=league_avg.get(league,(1.55,1.25))

        # History 50 اولا - لو الفريقين موجودين، xG منهم مش من الدوري
        try:
            _home, _away = mm.get("match","").split(" vs ")
        except:
            _home, _away = "", ""
        _hs=stats.get(_home); _aws=stats.get(_away)
        if _hs and _aws and _hs.get("source")=="history50" and _aws.get("source")=="history50":
            h=round(max(0.2,min(3.8, _hs["home_scored"] * (_aws["away_conceded"]/1.35))),2)
            a=round(max(0.2,min(3.8, _aws["away_scored"] * (_hs["home_conceded"]/1.35))),2)
            src="history50"
        else:
            h=round(bh*1.08,2); a=round(ba,2); src="league"

        hw,d,aw,m,btts,over25=pred(h,a, show=False)
        conf=max(hw,d,aw)
        out.append({"match":mm.get("match",""),"date":mm.get("date",""),"league":league,"xG":f"{h}-{a}","1":round(hw*100,1),"X":round(d*100,1),"2":round(aw*100,1),"BTTS":round(btts*100,1),"Over25":round(over25*100,1),"conf":round(conf*100,1),"src":src})
    out_sorted=sorted(out, key=lambda x: x["conf"], reverse=True)
    print(f"Predict All: {len(out)} - Top 10 by conf")
    for o in out_sorted[:10]:
        print(f"{o['date']} {o['match']}  xG:{o['xG']} 1:{o['1']}% X:{o['X']}% 2:{o['2']}%  BTTS:{o['BTTS']}% [{o.get('src','')}]")
    os.makedirs("data", exist_ok=True)
    with open("data/sigma_bulk_predictions.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["date","match","league","xG","1","X","2","BTTS","Over25","conf","src"]); w.writeheader(); w.writerows(out)
    print("Saved: data/sigma_bulk_predictions.csv")
def do_history():
    import subprocess, sys
    mode=input("1=Init 365d (أول مرة)  2=Daily 3d (تحديث) : ").strip()
    arg="--init" if mode!="2" else "--daily"
    if os.path.exists("sigma_history_fetch.py"):
        print(f"Running sigma_history_fetch.py {arg} ...")
        r=subprocess.run([sys.executable, "sigma_history_fetch.py", arg]); print(f"History exit: {r.returncode}"); return
    print("No file: sigma_history_fetch.py")
def do_learn():
    if not os.path.exists("data/sigma_history.csv"):
        print("No history - Run 7 History first"); return
    rows=list(csv.DictReader(open("data/sigma_history.csv", encoding="utf-8")))
    rows=[r for r in rows if r.get("status","FINISHED")=="FINISHED" or "status" not in r]
    n=len(rows)
    if n==0: print("History empty"); return
    avg=sum(int(r["home_goals"])+int(r["away_goals"]) for r in rows)/n
    home_win=sum(1 for r in rows if int(r["home_goals"])>int(r["away_goals"]))/n*100
    btts=sum(1 for r in rows if int(r["home_goals"])>0 and int(r["away_goals"])>0)/n*100
    over25=sum(1 for r in rows if int(r["home_goals"])+int(r["away_goals"])>=3)/n*100
    print(f"Learn - History n={n}")
    print(f"Avg goals: {avg:.2f}  Home Win: {home_win:.1f}%  BTTS: {btts:.1f}%  Over 2.5: {over25:.1f}%")
    from collections import Counter
    c=Counter()
    for r in rows: c[r["home"]]+=1; c[r["away"]]+=1
    print(f"Teams: {len(c)}  Avg per team: {sum(c.values())/max(1,len(c)):.1f}  Min: {min(c.values())}  Max: {max(c.values())}")
    print(f"Top teams by matches: {c.most_common(5)}")
    if home_win>50: print("Learn: Home advantage قوي - ارفع Home xG")
    if btts<45: print("Learn: BTTS منخفض - قلل ثقة BTTS")
    if avg>3.2: print("Learn: دوري هجومي - Over 2.5 أقوى")
def do_update_all():
    print("Update All: History Daily + Next Month")
    import subprocess, sys
    if os.path.exists("sigma_history_fetch.py"):
        subprocess.run([sys.executable, "sigma_history_fetch.py", "--daily"])
    if os.path.exists("sigma_auto_fetch.py"):
        subprocess.run([sys.executable, "sigma_auto_fetch.py"])
    print("Update All done")
while True:
    print("\n1. Predict xG  2. Predict team  3. List  4. Eval  5. Fetch  6. Predict All  7. History  8. Learn  9. Update All  0. Exit")
    c=input("Choose: ").strip()
    if c=="0": break
    if c=="1":
        h=get_num("Home xG: ", 1.78); a=get_num("Away xG: ", 1.35); print(f"Using: {h} - {a}"); pred(h,a)
    elif c=="2": predict_by_team()
    elif c=="3": match_list()
    elif c=="4": evaluation()
    elif c=="5": do_fetch()
    elif c=="6": predict_all()
    elif c=="7": do_history()
    elif c=="8": do_learn()
    elif c=="9": do_update_all()
