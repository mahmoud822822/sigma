#!/usr/bin/env python3
# Sigma Auto-Fetch v2 - 10 days chunk - Mahmoud Emad
import os, json, csv, urllib.request, urllib.error, time
from datetime import date, timedelta
from pathlib import Path
BASE=Path(__file__).parent
DATA=BASE/"data"
DATA.mkdir(exist_ok=True)
COMP="2021,2014,2019,2002,2015,2003,2017,2004"
MAP={"Premier League":"England","La Liga":"Spain","Serie A":"Italy","Bundesliga":"Germany","Ligue 1":"France","Eredivisie":"Netherlands","Primeira Liga":"Portugal","Jupiler Pro League":"Belgium"}
def predict(home,away,league):
    avg={"England":3.43,"Spain":3.10,"Italy":3.00,"Germany":3.20,"Netherlands":3.30,"Portugal":3.00,"Belgium":3.10}.get(league,3.10)
    f=avg/3.10
    ph=round(1.55*f,1); pa=round(1.25*f,1)
    mk=[("Over 1",f"Over 1 ({ph+pa:.1f} exp)",9.0,82,"Gold"),("2H Over 0.5","2H Over 0.5 - Late 76-90 30%",9.5,85,"Gold"),("BTTS","BTTS - weight 70",7.0,67,"Value"),("X2",f"{away} X2",8.0,76,"Balanced"),("Home X2",f"{home} X2",8.0,76,"Balanced"),("Over 2.5",f"Over 2.5 - exp {ph+pa:.1f}",7.5,72,"Value"),("1X",f"{home} 1X",8.5,78,"Balanced"),("BTTS + Over 1.5","BTTS + Over 1.5 Combo",6.5,64,"Value")]
    return ph,pa,mk
def fetch_chunk(token,df,dt):
    url=f"https://api.football-data.org/v4/matches?dateFrom={df}&dateTo={dt}&competitions={COMP}"
    req=urllib.request.Request(url,headers={"X-Auth-Token":token})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return json.loads(r.read().decode()).get("matches",[])
    except urllib.error.HTTPError as e:
        print(f"API {e.code} for {df}->{dt}")
        return []
def main():
    today=date.today(); nxt=today+timedelta(days=35)
    print(f"Sigma Auto-Fetch v2 - {today} -> {nxt} in 10-day chunks")
    token="".join(c for c in os.environ.get("FOOTBALL_DATA_TOKEN","").strip() if c.isascii() and c.isalnum())
    if len(token)!=32:
        print(f"ERROR: Token len {len(token)} != 32")
        return
    all_matches=[]; cur=today
    while cur<=nxt:
        chunk_end=min(cur+timedelta(days=9),nxt)
        print(f"Fetching {cur} -> {chunk_end} ...")
        ms=fetch_chunk(token,cur.isoformat(),chunk_end.isoformat())
        print(f"  got {len(ms)}")
        all_matches.extend(ms); cur=chunk_end+timedelta(days=1); time.sleep(1)
    print(f"Fetched total: {len(all_matches)} matches")
    rows=[]; by={}
    for m in all_matches:
        comp=m.get("competition",{}).get("name","Default"); league=MAP.get(comp,"Default")
        home=m['homeTeam']['name']; away=m['awayTeam']['name']; match=f"{home} vs {away}"
        ph,pa,mk=predict(home,away,league)
        by[match]={"match":match,"date":m["utcDate"][:10],"league":league,"pred_home":ph,"pred_away":pa,"markets":[]}
        for market,pick,safe,conf,tier in mk:
            rows.append({"match":match,"date":m["utcDate"][:10],"league":league,"predicted_home":ph,"predicted_away":pa,"market":market,"pick":pick,"safety_score":safe,"confidence":conf,"tier":tier,"era":"NEXT_MONTH_AUTO"})
            by[match]["markets"].append({"market":market,"pick":pick,"safety":safe,"tier":tier,"conf":conf})
    payload={"generated":str(today),"from":str(today),"to":str(nxt),"total_matches":len(by),"total_predictions":len(rows),"matches":list(by.values())}
    (DATA/"sigma_next_month.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    if rows:
        with open(DATA/"sigma_next_month.csv","w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"Saved: {len(by)} matches, {len(rows)} predictions")
if __name__=="__main__":
    main()
