import os,json,csv,math,time,re,urllib.request
from datetime import datetime,date,timedelta,timezone
from pathlib import Path
VERSION="Sigma-AI-V75"
BASE=Path(__file__).resolve().parent
DATA=BASE/"data"
DATA.mkdir(exist_ok=True)
WF=DATA/"sigma_weights.json"
LF=DATA/"sigma_prediction_log.json"
SF=DATA/"sigma_site.json"
HF=DATA/"sigma_history.csv"
DW={"xi":0.0018,"elo_home":65.0,"elo_adj":0.0010,"rho":-0.08}
FD={"PL":"Premier League","PD":"La Liga","SA":"Serie A","BL1":"Bundesliga","FL1":"Ligue 1","DED":"Eredivisie","PPL":"Primeira Liga"}
OF={"en.1":"Premier League","es.1":"La Liga","it.1":"Serie A","de.1":"Bundesliga","fr.1":"Ligue 1"}
def today():return datetime.now(timezone.utc).date()
def clean(s):return re.sub(r"\s+"," ",str(s or "")).strip()
def norm(s):return "".join(c for c in clean(s).lower() if c.isalnum())
def mkey(d,h,a):return f"{d}|{norm(h)}|{norm(a)}"
def load_w():
 w=dict(DW)
 if WF.exists():
  try:w.update(json.loads(WF.read_text()).get("weights",{}))
  except:pass
 return w
def hjson(u,hd=None):
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Sigma/75",**(hd or {})}),timeout=20) as r:return json.loads(r.read().decode())
 except:return None
def load_hist():
 m={}
 def add(ds,h,a,hg,ag,lg,src):
  h,a=clean(h),clean(a)
  if not h or not a:return
  try:d,hg,ag=date.fromisoformat(str(ds)[:10]),int(float(hg)),int(float(ag))
  except:return
  k=(d,norm(h),norm(a))
  if k not in m:m[k]={"d":d,"home":h,"away":a,"hg":hg,"ag":ag,"league":clean(lg) or "League","source":src}
 if HF.exists():
  for r in csv.DictReader(open(HF,encoding="utf-8",errors="replace")):add(r.get("date"),r.get("home"),r.get("away"),r.get("home_goals"),r.get("away_goals"),r.get("league"),r.get("source","hist"))
 if (BASE/"world_results.csv").exists():
  for r in csv.DictReader(open(BASE/"world_results.csv",encoding="utf-8",errors="replace")):
   if str(r.get("date",""))>="2000-01-01":add(r.get("date"),r.get("home_team"),r.get("away_team"),r.get("home_score"),r.get("away_score"),r.get("tournament"),"world")
 return sorted(m.values(),key=lambda x:x["d"])
def ratings(hist,ref,w):
 elo,att,dfn={},{},{}
 for r in hist:
  if r["d"]>=ref:break
  dc=math.exp(-w["xi"]*max(0,(ref-r["d"]).days))
  h,a=r["home"],r["away"]
  elo.setdefault(h,1500.0);elo.setdefault(a,1500.0);att.setdefault(h,1.35);att.setdefault(a,1.35);dfn.setdefault(h,1.35);dfn.setdefault(a,1.35)
  eh=1.0/(1.0+10**((elo[a]-(elo[h]+w["elo_home"]))/400.0))
  ah=1.0 if r["hg"]>r["ag"] else 0.5 if r["hg"]==r["ag"] else 0.0
  k=20.0*dc;elo[h]+=k*(ah-eh);elo[a]-=k*(ah-eh)
  lr=0.08*dc;att[h]=att[h]*(1-lr)+r["hg"]*lr;dfn[h]=dfn[h]*(1-lr)+r["ag"]*lr;att[a]=att[a]*(1-lr)+r["ag"]*lr;dfn[a]=dfn[a]*(1-lr)+r["hg"]*lr
 return {"elo":elo,"att":att,"dfn":dfn}
def pmf(k,l):return (l**k)*math.exp(-l)/math.factorial(k)
def get_real_intel(lg, ev_id, h_id, a_id, h_name, a_name, hist):
    base = "https://espn.com"
    inj_h = inj_a = 0
    lineup_ok = False
    mkt_p1 = mkt_px = mkt_p2 = None
    notes = []
    try:
        sm = hjson(f"{base}/{lg}/summary?event={ev_id}") or {}
        for item in sm.get("injuries", []):
            tid = str(item.get("team", {}).get("id", ""))
            cnt = len(item.get("injuries", []))
            if tid == str(h_id): inj_h = cnt
            elif tid == str(a_id): inj_a = cnt
        rosters = sm.get("rosters", [])
        if any(len(r.get("roster", [])) >= 11 for r in rosters):
            lineup_ok = True
        odds = sm.get("pickcenter", [])
        if odds:
            o0 = odds[0]
            hp = o0.get("homeTeamOdds", {}).get("winPercentage")
            ap = o0.get("awayTeamOdds", {}).get("winPercentage")
            if hp and ap:
                mkt_p1, mkt_p2 = float(hp), float(ap)
                mkt_px = max(5.0, round(100.0 - mkt_p1 - mkt_p2, 1))
    except Exception:
        pass
    h_rec = [r for r in hist if r["home"] == h_name or r["away"] == h_name][-5:]
    a_rec = [r for r in hist if r["home"] == a_name or r["away"] == a_name][-5:]
    def form_pts(recs, tm):
        if not recs: return 1.5
        pts = 0
        for r in recs:
            gf = r["hg"] if r["home"] == tm else r["ag"]
            ga = r["ag"] if r["home"] == tm else r["hg"]
            pts += 3 if gf > ga else (1 if gf == ga else 0)
        return pts / len(recs)
    fh, fa = form_pts(h_rec, h_name), form_pts(a_rec, a_name)
    if inj_h: notes.append(f"🏥 {h_name[:10]}: {inj_h} غيابات")
    if inj_a: notes.append(f"🏥 {a_name[:10]}: {inj_a} غيابات")
    if lineup_ok: notes.append("📋 تشكيلة مؤكدة")
    notes.append(f"📈 فورمة: {round(fh,1)} vs {round(fa,1)}")
    return {"inj_h": inj_h, "inj_a": inj_a, "lineup": lineup_ok, "fh": fh, "fa": fa, "mkt": (mkt_p1, mkt_px, mkt_p2), "notes": " • ".join(notes)}

def pred(h,a,R,w):
    diff=(R["elo"].get(h,1500)+w["elo_home"])-R["elo"].get(a,1500); ef=math.exp(max(-1.2,min(1.2,diff*0.00165)))
    att_h,dfn_h=R["att"].get(h,1.38),R["dfn"].get(h,1.38)
    att_a,dfn_a=R["att"].get(a,1.32),R["dfn"].get(a,1.38)
    lh=max(0.45,min(3.8,((att_h+dfn_a)/2.0)*ef))
    la=max(0.40,min(3.5,((att_a+dfn_h)/2.0)/ef))
    p1=px=p2=bt=ov=tot=0.0;sc=[]
    for i in range(8):
        for j in range(8):
            pr=pmf(i,lh)*pmf(j,la)
            if i==0 and j==0: pr*=max(0.1,1.0-lh*la*w.get("rho",-0.08))
            elif i==1 and j==0: pr*=max(0.1,1.0+la*w.get("rho",-0.08))
            elif i==0 and j==1: pr*=max(0.1,1.0+lh*w.get("rho",-0.08))
            elif i==1 and j==1: pr*=max(0.1,1.0-w.get("rho",-0.08))
            tot+=pr
            if i>j:p1+=pr
            elif i==j:px+=pr
            else:p2+=pr
            if i>0 and j>0:bt+=pr
            if i+j>2:ov+=pr
            sc.append((pr,f"{i}-{j}"))
    p1,px,p2=round(100*p1/tot,1),round(100*px/tot,1),round(100*p2/tot,1)
    ov25=round(100*ov/tot,1)
    btts=round(100*bt/tot,1)
    bp,pk=max((p1,"1"),(px,"X"),(p2,"2"));cf=min(88.0,bp);sc.sort(reverse=True)
    qu="full" if (h in R["elo"] or a in R["elo"]) else "prior"
    is_gold = (cf >= 58.0) or (ov25 >= 64.0 and cf >= 50.0)
    return {"p1":p1,"pX":px,"p2":p2,"conf":cf,"btts":btts,"over25":ov25,"xg_home":round(lh,2),"xg_away":round(la,2),"elo_home":round(R["elo"].get(h,1500)),"elo_away":round(R["elo"].get(a,1500)),"pick":pk,"grade":"A+" if cf>=70 else "A" if cf>=60 else "B" if cf>=50 else "C","quality":qu,"golden":is_gold,"top_scores":[x[1] for x in sc[:3]]}

def fetch(t):
 fx,rs=[],[]
 for lg in [
"eng.1","eng.2","eng.3","eng.4","eng.fa","eng.league_cup",
"esp.1","esp.2","esp.copa_del_rey",
"ita.1","ita.2","ita.coppa_italia",
"ger.1","ger.2","ger.dfb_pokal",
"fra.1","fra.2","fra.coupe_de_france",
"por.1","ned.1","tur.1","bel.1","sco.1","gre.1","sui.1","aut.1","den.1","swe.1","nor.1","pol.1","cze.1","rus.1","ukr.1","rou.1","hun.1","cro.1","srb.1",
"uefa.champions","uefa.europa","uefa.europa.conf","uefa.nations","uefa.euroq",
"egy.1","ksa.1","uae.1","qat.1","mar.1","tun.1","alg.1","kuw.1","bhr.1","oma.1","jor.1","irq.1",
"caf.champions","caf.confed","caf.nations","caf.nations_qual",
"afc.champions","afc.cup","afc.asian_cup","afc.worldq",
"jpn.1","kor.1","chn.1","aus.1","ind.1","idn.1","tha.1","mys.1",
"bra.1","bra.2","arg.1","col.1","chi.1","per.1","uru.1","ecu.1","par.1","ven.1","bol.1",
"conmebol.libertadores","conmebol.sudamericana","conmebol.america",
"usa.1","mex.1","crc.1","concacaf.champions","concacaf.gold","concacaf.nations",
"fifa.world","fifa.worldq.uefa","fifa.worldq.caf","fifa.worldq.conmebol","fifa.worldq.afc","fifa.worldq.concacaf","fifa.friendly","fifa.cwc"
]:
  o=hjson(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard")
  for ev in (o or {}).get("events",[]):
   try:
    d=date.fromisoformat(ev["date"][:10]);c=ev["competitions"][0]["competitors"]
    h=clean(next(x["team"]["displayName"] for x in c if x["homeAway"]=="home"))
    a=clean(next(x["team"]["displayName"] for x in c if x["homeAway"]=="away"))
    st=ev["status"]["type"]["state"]
    if st=="post":rs.append({"date":d,"home":h,"away":a,"hg":int(next(x["score"] for x in c if x["homeAway"]=="home")),"ag":int(next(x["score"] for x in c if x["homeAway"]=="away")),"league":lg})
    elif st=="pre":fx.append({"date":d,"home":h,"away":a,"league":lg})
   except:pass
 return fx,rs
def supa(u,k,tb,rw):
 if not u or not k or not rw:return
 try:urllib.request.urlopen(urllib.request.Request(f"{u.rstrip('/')}/rest/v1/{tb}",data=json.dumps(rw).encode(),headers={"apikey":k,"Authorization":f"Bearer {k}","Content-Type":"application/json","Prefer":"resolution=merge-duplicates"},method="POST"),timeout=20).read()
 except Exception as e:print("SB warn:",e)
def build(hist,t,w):
    elo,att,dfn,cnt={},{},{},{}
    for r in sorted(hist,key=lambda x:x["d"]):
        h,a,hg,ag=r["home"],r["away"],r["hg"],r["ag"]
        eh,ea=elo.get(h,1500.0),elo.get(a,1500.0)
        exp=1.0/(1.0+10.0**((ea-(eh+w["elo_home"]))/400.0))
        res=1.0 if hg>ag else 0.5 if hg==ag else 0.0
        k=w["k"]*(1.0+0.25*min(3,abs(hg-ag)))
        elo[h]=eh+k*(res-exp);elo[a]=ea+k*((1.0-res)-(1.0-exp))
        att[h]=att.get(h,1.38)*0.94+hg*0.06
        dfn[h]=dfn.get(h,1.38)*0.94+ag*0.06
        att[a]=att.get(a,1.32)*0.94+ag*0.06
        dfn[a]=dfn.get(a,1.38)*0.94+hg*0.06
    return {"elo":elo,"att":att,"dfn":dfn}

def run():
    t=datetime.now(timezone.utc).date()
    fx,rs=fetch(t)
    hist,ex=[],set()
    if HF.exists():
        with open(HF,encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d=date.fromisoformat(r["date"]);k=(d,norm(r["home"]),norm(r["away"]))
                if k not in ex: ex.add(k);hist.append({"d":d,"league":r["league"],"home":r["home"],"away":r["away"],"hg":int(r.get("hg") or r.get("home_goals") or r.get("FTHG") or 0),"ag":int(r.get("ag") or r.get("away_goals") or r.get("FTAG") or 0)})
    add=0
    for r in rs:
        k=(r["date"],norm(r["home"]),norm(r["away"]))
        if k not in ex: ex.add(k);hist.append({"d":r["date"],"league":r["league"],"home":r["home"],"away":r["away"],"hg":r["hg"],"ag":r["ag"]});add+=1
    with open(HF,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,["date","league","home","away","hg","ag"]);w.writeheader()
        for r in sorted(hist,key=lambda x:x["d"]): w.writerow({"date":r["d"].isoformat(),"league":r["league"],"home":r["home"],"away":r["away"],"hg":r["hg"],"ag":r["ag"]})
    w=json.loads(WF.read_text(encoding="utf-8")) if WF.exists() else {"k":22,"elo_home":45,"elo_adj":0.0022,"rho":-0.08,"decay":0.0018}
    R=build(hist,t,w)
    log=json.loads(LF.read_text(encoding="utf-8")) if LF.exists() else {}
    for r in rs:
        k=f"{r['date']}|{norm(r['home'])}|{norm(r['away'])}"
        if k in log and not log[k].get("result"):
            out="1" if r["hg"]>r["ag"] else "X" if r["hg"]==r["ag"] else "2"
            log[k]["result"]=f"{r['hg']}-{r['ag']}";log[k]["outcome"]=out;log[k]["hit"]=(log[k]["pick"]==out)
    from concurrent.futures import ThreadPoolExecutor
    fx_sorted = sorted(fx, key=lambda x: x["date"])
    def enrich(idx_m):
        idx, m = idx_m
        pr = pred(m["home"], m["away"], R, w)
        if idx < 180 and m.get("id"):
            intel = get_real_intel(m["league"], m["id"], m.get("hid",""), m.get("aid",""), m["home"], m["away"], hist)
            adj_h = max(0.75, 1.0 - intel["inj_h"]*0.035 + (intel["fh"]-1.5)*0.08)
            adj_a = max(0.75, 1.0 - intel["inj_a"]*0.035 + (intel["fa"]-1.5)*0.08)
            pr["xg_home"] = round(pr["xg_home"] * adj_h, 2)
            pr["xg_away"] = round(pr["xg_away"] * adj_a, 2)
            if intel["mkt"][0]:
                mp1, mpx, mp2 = intel["mkt"]
                pr["p1"] = round(pr["p1"]*0.65 + mp1*0.35, 1)
                pr["pX"] = round(pr["pX"]*0.65 + mpx*0.35, 1)
                pr["p2"] = round(pr["p2"]*0.65 + mp2*0.35, 1)
                bp, pk = max((pr["p1"],"1"),(pr["pX"],"X"),(pr["p2"],"2"))
                pr["pick"], pr["conf"] = pk, min(88.0, bp)
                pr["golden"] = (pr["conf"] >= 58.0) or (pr["over25"] >= 64.0 and pr["conf"] >= 50.0)
            pr["intel"] = intel["notes"]
        else:
            pr["intel"] = "📊 تحليل Elo + Poisson"
        return m, pr
    up=[]
    with ThreadPoolExecutor(max_workers=20) as ex:
        enriched = list(ex.map(enrich, enumerate(fx_sorted)))
    for m, pr in enriched:
        k=f"{m['date']}|{norm(m['home'])}|{norm(m['away'])}"
        row={"key":k,"date":m["date"].isoformat(),"league":m["league"],"home":m["home"],"away":m["away"],**pr}
        up.append(row)
        if k not in log: log[k]={**row,"result":None,"outcome":None,"hit":None}
    LF.write_text(json.dumps(log,ensure_ascii=False))
    gr=[e for e in log.values() if e.get("result")]
    if not gr:
        for r in sorted(hist,key=lambda x:x["d"],reverse=True)[:40]:
            pr=pred(r["home"],r["away"],R,w);out="1" if r["hg"]>r["ag"] else "X" if r["hg"]==r["ag"] else "2"
            gr.append({"date":r["d"].isoformat(),"league":r["league"],"home":r["home"],"away":r["away"],"pick":pr["pick"],"conf":pr["conf"],"over25":pr["over25"],"result":f"{r['hg']}-{r['ag']}","outcome":out,"hit":(pr["pick"]==out)})
    ht=sum(1 for e in gr if e.get("hit"));hp=round(100*ht/len(gr),1) if gr else 0.0
    te=sorted(R["elo"].items(),key=lambda x:x[1],reverse=True)[:30]
    sd={"version":VERSION,"generated_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),"stats":{"upcoming":len(up),"history_count":len(hist),"graded":len(gr),"hit_pct":hp},"weights":w,"top_elo":[{"team":tm,"elo":round(sc)} for tm,sc in te],"matches":sorted(up,key=lambda x:(x["date"],-x["conf"])),"recent_results":sorted(gr,key=lambda x:x["date"],reverse=True)[:40]}
    SF.write_text(json.dumps(sd,ensure_ascii=False,indent=1))
    su,sk=os.environ.get("SUPABASE_URL","").strip(),os.environ.get("SUPABASE_SERVICE_KEY","").strip()
    if su and sk:
        supa(su,sk,"sigma_predictions",[{"match_key":m["key"],"match_date":m["date"],"league":m["league"],"home":m["home"],"away":m["away"],"p1":m["p1"],"px":m["pX"],"p2":m["p2"],"btts":m["btts"],"over25":m["over25"],"xg_home":m["xg_home"],"xg_away":m["xg_away"],"pick":m["pick"],"grade":m["grade"],"data_quality":m["quality"],"golden":m["golden"],"model":VERSION} for m in up])
        supa(su,sk,"sigma_heartbeat",[{"id":1,"beat_at":datetime.now(timezone.utc).isoformat()}])
    print(f"✅ Sigma V75 Done: History={len(hist)} | Upcoming={len(up)} | New={add} | Acc={hp}%")

if __name__=="__main__":
    run()
