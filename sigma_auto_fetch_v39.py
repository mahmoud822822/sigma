#!/usr/bin/env python3
# Sigma Auto-Fetch V39 - Mahmoud Emad
# يجيب المستقبل 35 يوم + يتوقع بـ V39 Ensemble لو team_stats موجود، ولو مش موجود يرجع لمتوسط الدوري
# يحفظ: data/sigma_next_month.json + data/sigma_next_month.csv
# stdlib ONLY
import os, json, csv, urllib.request, urllib.error, time, sys
from datetime import date, timedelta
from pathlib import Path
BASE = Path(__file__).parent
DATA = BASE/"data"
DATA.mkdir(exist_ok=True)
COMP="2021,2014,2019,2002,2015,2003,2017,2004"
MAP={"Premier League":"England","La Liga":"Spain","Serie A":"Italy","Bundesliga":"Germany","Ligue 1":"France","Eredivisie":"Netherlands","Primeira Liga":"Portugal","Jupiler Pro League":"Belgium"}
# حاول تستورد V39 - لو مش موجود، fallback
try:
    sys.path.insert(0, str(BASE))
    import sigma_v39 as V39
    HAS_V39=True
except Exception as e:
    print(f"V39 not importable ({e}) - fallback to league avg")
    HAS_V39=False

def fetch_chunk(token, df, dt):
    url=f"https://api.football-data.org/v4/matches?dateFrom={df}&dateTo={dt}&competitions={COMP}"
    req=urllib.request.Request(url, headers={"X-Auth-Token": token})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode()).get("matches", [])
        except urllib.error.HTTPError as e:
            print(f"API {e.code} {df}->{dt} attempt {attempt+1}")
            if e.code==429:
                print("Rate limit - sleep 65s"); time.sleep(65); continue
            return []
        except Exception as e:
            print(f"Err {e} {df}"); return []
    return []

def fallback_predict(home, away, league):
    avg={"England":3.43,"Spain":3.10,"Italy":3.00,"Germany":3.20,"Netherlands":3.30,"Portugal":3.00,"Belgium":3.10}.get(league,3.10)
    f=avg/3.10
    ph=round(1.55*f,1); pa=round(1.25*f,1)
    mk=[("Over 1",f"Over 1 ({ph+pa:.1f} exp)",9.0,82,"Gold"),("2H Over 0.5","2H Over 0.5 - Late 76-90 30%",9.5,85,"Gold"),("BTTS","BTTS - weight 70",7.0,67,"Value"),("X2",f"{away} X2",8.0,76,"Balanced"),("Home X2",f"{home} X2",8.0,76,"Balanced")]
    return ph,pa,mk,{"1":0,"X":0,"2":0}

def main():
    today=date.today(); nxt=today+timedelta(days=35)
    print(f"Sigma Auto-Fetch V39 - {today} -> {nxt} in 10-day chunks")
    token="".join(c for c in os.environ.get("FOOTBALL_DATA_TOKEN","").strip() if c.isascii() and c.isalnum())
    if len(token)!=32:
        print(f"ERROR: Token len {len(token)} != 32")
        print("في Termux: export FOOTBALL_DATA_TOKEN=توكنك_32_حرف")
        return
    # جهز stats مرة واحدة
    stats=None
    if HAS_V39:
        try:
            stats,_meta=V39.build_team_stats()
            print(f"V39 stats ready: {len(stats)} teams - هنستخدم Ensemble مش متوسط دوري بس")
        except Exception as e:
            print(f"Stats build failed ({e}) - fallback"); stats=None
    all_matches=[]; cur=today
    while cur<=nxt:
        chunk_end=min(cur+timedelta(days=9),nxt)
        print(f"Fetching {cur} -> {chunk_end} ...")
        ms=fetch_chunk(token,cur.isoformat(),chunk_end.isoformat())
        print(f"  got {len(ms)}")
        all_matches.extend(ms); cur=chunk_end+timedelta(days=1)
        if cur<=nxt: time.sleep(7)
    print(f"Fetched total: {len(all_matches)} matches")
    rows=[]; by={}
    for m in all_matches:
        comp=m.get("competition",{}).get("name","Default"); league=MAP.get(comp,"Default")
        home=m['homeTeam']['name']; away=m['awayTeam']['name']; match=f"{home} vs {away}"
        if stats is not None and HAS_V39:
            try:
                pr=V39.predict_match(home, away, league, stats=stats)
                ph=round(pr["xG_home"],1); pa=round(pr["xG_away"],1)
                mk=[("Over 1",f"Over 1 ({pr['exp_goals']:.1f} exp)",9.0,round(pr["safety"]["Over 1"],1),"Gold"),
                    ("2H Over 0.5","2H Over 0.5 - Late 76-90 30%",9.5,85,"Gold"),
                    ("BTTS",f"BTTS - weight 70 ({pr['BTTS']}%)",7.0,round(pr["safety"]["BTTS"],1),"Value"),
                    ("X2",f"{away} X2 ({pr['2']:.1f}%)",8.0,76,"Balanced"),
                    ("Home X2",f"{home} X2 ({pr['1']:.1f}%)",8.0,76,"Balanced")]
                extra={"1":pr["1"],"X":pr["X"],"2":pr["2"],"BTTS":pr["BTTS"],"Over25":pr["Over25"],"conf":pr["conf"],"grade":pr["grade"],"tier":pr["tier"],"xG":pr["xG"]}
            except Exception as e:
                print(f"Predict failed {match}: {e}")
                ph,pa,mk,extra=fallback_predict(home,away,league); extra={"1":0,"X":0,"2":0}
        else:
            ph,pa,mk,extra=fallback_predict(home,away,league)
        by[match]={"match":match,"date":m["utcDate"][:10],"league":league,"pred_home":ph,"pred_away":pa,"markets":[],"v39":extra}
        for market,pick,safe,conf,tier in mk:
            rows.append({"match":match,"date":m["utcDate"][:10],"league":league,"predicted_home":ph,"predicted_away":pa,"market":market,"pick":pick,"safety_score":safe,"confidence":conf,"tier":tier,"era":"NEXT_MONTH_V39"})
            by[match]["markets"].append({"market":market,"pick":pick,"safety":safe,"tier":tier,"conf":conf})
    payload={"generated":str(today),"from":str(today),"to":str(nxt),"total_matches":len(by),"total_predictions":len(rows),"version":"V39","matches":list(by.values())}
    (DATA/"sigma_next_month.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    if rows:
        with open(DATA/"sigma_next_month.csv","w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"Saved: {len(by)} matches, {len(rows)} predictions -> data/sigma_next_month.json")
    print("Next: python sigma_v39.py --unified  ثم  python sigma_v39.py --predict-all")

if __name__=="__main__":
    main()
