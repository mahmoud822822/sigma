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
def pred(h,a,R,w):
 ef=math.exp(((R["elo"].get(h,1500)+w["elo_home"])-R["elo"].get(a,1500))*w["elo_adj"])
 lh=max(0.25,min(3.8,((R["att"].get(h,1.35)+R["dfn"].get(a,1.35))/2)*ef))
 la=max(0.20,min(3.5,((R["att"].get(a,1.35)+R["dfn"].get(h,1.35))/2)/ef))
 p1=px=p2=bt=ov=tot=0.0;sc=[]
 for i in range(7):
  for j in range(7):
   pr=pmf(i,lh)*pmf(j,la);tot+=pr
   if i>j:p1+=pr
   elif i==j:px+=pr
   else:p2+=pr
   if i>0 and j>0:bt+=pr
   if i+j>2:ov+=pr
   sc.append((pr,f"{i}-{j}"))
 p1,px,p2=round(100*p1/tot,1),round(100*px/tot,1),round(100*p2/tot,1)
 bp,pk=max((p1,"1"),(px,"X"),(p2,"2"));cf=min(85.0,bp);sc.sort(reverse=True)
 qu="full" if (h in R["elo"] and a in R["elo"]) else "prior"
 return {"p1":p1,"pX":px,"p2":p2,"conf":cf,"btts":round(100*bt/tot,1),"over25":round(100*ov/tot,1),"xg_home":round(lh,2),"xg_away":round(la,2),"elo_home":round(R["elo"].get(h,1500)),"elo_away":round(R["elo"].get(a,1500)),"pick":pk,"grade":"A+" if cf>=70 else "A" if cf>=60 else "B" if cf>=50 else "C","quality":qu,"golden":(62<=cf<=82 and qu=="full"),"top_scores":[x[1] for x in sc[:3]]}
def fetch(t):
 fx,rs=[],[]
 for lg in ["eng.1","eng.2","esp.1","ita.1","ger.1","fra.1","por.1","ned.1","tur.1","bel.1","sco.1","uefa.champions","uefa.europa","uefa.europa.conf","uefa.nations","fifa.world","fifa.worldq.uefa","fifa.worldq.caf","fifa.worldq.conmebol","fifa.worldq.afc","fifa.friendly","egy.1","ksa.1","caf.champions","afc.champions","bra.1","arg.1","usa.1","mex.1"]:
  o=hjson(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard?dates={t.strftime('%Y%m%d')}-{(t+timedelta(days=14)).strftime('%Y%m%d')}")
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
def run():
 t=today();w=load_w();hist=load_hist();fx,rs=fetch(t)
 ex={(r["d"],norm(r["home"]),norm(r["away"])) for r in hist};add=0
 for r in rs:
  k=(r["date"],norm(r["home"]),norm(r["away"]))
  if k not in ex:ex.add(k);hist.append({"d":r["date"],"home":r["home"],"away":r["away"],"hg":r["hg"],"ag":r["ag"],"league":r["league"],"source":"api"});add+=1
 with open(HF,"w",encoding="utf-8",newline="") as f:
  wr=csv.writer(f);wr.writerow(["date","home","away","home_goals","away_goals","league","source"])
  for r in sorted(hist,key=lambda x:x["d"]):wr.writerow([r["d"].isoformat(),r["home"],r["away"],r["hg"],r["ag"],r["league"],r.get("source","hist")])
 R=ratings(hist,t,w);log=json.loads(LF.read_text()) if LF.exists() else {}
 hidx={mkey(r["d"].isoformat(),r["home"],r["away"]):r for r in hist}
 for k,e in log.items():
  if e.get("result") is None and k in hidx:
   r=hidx[k];out="1" if r["hg"]>r["ag"] else "X" if r["hg"]==r["ag"] else "2"
   e["result"],e["outcome"],e["hit"]=f"{r['hg']}-{r['ag']}",out,(e["pick"]==out)
 up=[]
 for f in fx:
  k=mkey(f["date"].isoformat(),f["home"],f["away"]);p=pred(f["home"],f["away"],R,w)
  row={"key":k,"date":f["date"].isoformat(),"league":f["league"],"home":f["home"],"away":f["away"],**p};up.append(row)
  if k not in log:log[k]={**row,"result":None,"outcome":None,"hit":None}
 LF.write_text(json.dumps(log,ensure_ascii=False,indent=1))
 gr=[e for e in log.values() if e.get("result")];ht=sum(1 for e in gr if e.get("hit"));hp=round(100*ht/len(gr),1) if gr else 0.0
 te=sorted(R["elo"].items(),key=lambda x:x[1],reverse=True)[:30]
 sd={"version":VERSION,"generated_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),"stats":{"upcoming":len(up),"history_count":len(hist),"graded":len(gr),"hit_pct":hp},"weights":w,"top_elo":[{"team":tm,"elo":round(sc)} for tm,sc in te],"matches":sorted(up,key=lambda x:(x["date"],-x["conf"])),"recent_results":sorted(gr,key=lambda x:x["date"],reverse=True)[:40]}
 SF.write_text(json.dumps(sd,ensure_ascii=False,indent=1))
 su,sk=os.environ.get("SUPABASE_URL","").strip(),os.environ.get("SUPABASE_SERVICE_KEY","").strip()
 if su and sk:
  supa(su,sk,"sigma_predictions",[{"match_key":m["key"],"match_date":m["date"],"league":m["league"],"home":m["home"],"away":m["away"],"p1":m["p1"],"px":m["pX"],"p2":m["p2"],"btts":m["btts"],"over25":m["over25"],"xg_home":m["xg_home"],"xg_away":m["xg_away"],"pick":m["pick"],"grade":m["grade"],"data_quality":m["quality"],"golden":m["golden"],"model":VERSION} for m in up])
  supa(su,sk,"sigma_heartbeat",[{"id":1,"beat_at":datetime.now(timezone.utc).isoformat()}])
 print(f"✅ Sigma V75 Done: History={len(hist)} | Upcoming={len(up)} | New={add}")
if __name__=="__main__":run()
