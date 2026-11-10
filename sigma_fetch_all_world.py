# Fetch All World Leagues - Real Only - Mahmoud Emad
# Source: football-data.co.uk - Free, No Key, Stdlib only
import urllib.request, csv, json, os
from pathlib import Path
from collections import defaultdict
BASE = Path(".")
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
LEAGUES = {
 "E0":"England Premier League","E1":"England Championship","E2":"England League 1","E3":"England League 2","EC":"England Conference",
 "SP1":"Spain La Liga","SP2":"Spain Segunda",
 "I1":"Italy Serie A","I2":"Italy Serie B",
 "D1":"Germany Bundesliga","D2":"Germany 2 Bundesliga",
 "F1":"France Ligue 1","F2":"France Ligue 2",
 "N1":"Netherlands Eredivisie","P1":"Portugal Primeira","B1":"Belgium Jupiler",
 "T1":"Turkey Super Lig","G1":"Greece Super League",
 "SC0":"Scotland Premiership","SC1":"Scotland Championship","SC2":"Scotland League 1","SC3":"Scotland League 2",
}
SEASONS = ["1516","1617","1718","1819","1920","2021","2122","2223","2324","2425","2526"]
all_rows=[]
for code, lname in LEAGUES.items():
    cnt=0
    for s in SEASONS:
        url=f"https://www.football-data.co.uk/mmz4281/{s}/{code}.csv"
        try:
            req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                txt=r.read().decode("utf-8", errors="ignore")
            reader=csv.DictReader(txt.splitlines())
            for row in reader:
                h=row.get("HomeTeam","").strip(); a=row.get("AwayTeam","").strip()
                hg=row.get("FTHG","").strip(); ag=row.get("FTAG","").strip()
                if not h or not a or hg=="" or ag=="": continue
                try: hg=int(float(hg)); ag=int(float(ag))
                except: continue
                res="1" if hg>ag else "X" if hg==ag else "2"
                all_rows.append({"season":s,"league_code":code,"league":lname,"date":row.get("Date",""),"home":h,"away":a,"home_goals":hg,"away_goals":ag,"result":res})
                cnt+=1
        except Exception as e:
            print(f"Skip {code} {s} - {e}")
            continue
    print(f"{lname} ({code}): {cnt}")
print(f"TOTAL: {len(all_rows)} matches - Leagues: {len(LEAGUES)}")
# Save history all
with open(DATA/"sigma_history_all.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=["season","league_code","league","date","home","away","home_goals","away_goals","result"])
    w.writeheader(); w.writerows(all_rows)
# Team stats all
stats={}
for r in all_rows:
    for team, scored, conceded, is_home in [(r["home"],r["home_goals"],r["away_goals"],True),(r["away"],r["away_goals"],r["home_goals"],False)]:
        s=stats.get(team, {"n":0,"scored":0,"conceded":0,"home_n":0,"home_scored":0,"home_conceded":0,"away_n":0,"away_scored":0,"away_conceded":0,"btts":0,"over25":0,"wins":0})
        s["n"]+=1; s["scored"]+=scored; s["conceded"]+=conceded
        if is_home: s["home_n"]+=1; s["home_scored"]+=scored; s["home_conceded"]+=conceded
        else: s["away_n"]+=1; s["away_scored"]+=scored; s["away_conceded"]+=conceded
        if r["home_goals"]>0 and r["away_goals"]>0: s["btts"]+=1
        if r["home_goals"]+r["away_goals"]>=3: s["over25"]+=1
        if (is_home and r["result"]=="1") or (not is_home and r["result"]=="2"): s["wins"]+=1
        stats[team]=s
out={}
for team,s in stats.items():
    n=s["n"] or 1
    out[team]={"n":s["n"],"scored_avg":round(s["scored"]/n,2),"conceded_avg":round(s["conceded"]/n,2),
    "home_scored_avg":round(s["home_scored"]/max(1,s["home_n"]),2),"away_scored_avg":round(s["away_scored"]/max(1,s["away_n"]),2),
    "home_conceded_avg":round(s["home_conceded"]/max(1,s["home_n"]),2),"away_conceded_avg":round(s["away_conceded"]/max(1,s["away_n"]),2),
    "btts_rate":round(s["btts"]/n*100,1),"over25_rate":round(s["over25"]/n*100,1),"win_rate":round(s["wins"]/n*100,1)}
(DATA/"sigma_team_stats_all.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Teams: {len(out)} - Saved: data/sigma_history_all.csv + data/sigma_team_stats_all.json")
# Verify
avg=sum(r["home_goals"]+r["away_goals"] for r in all_rows)/max(1,len(all_rows))
hw=sum(1 for r in all_rows if r["result"]=="1")/max(1,len(all_rows))*100
print(f"Verify - Avg goals: {avg:.2f} - HomeWin: {hw:.1f}% - Unique: {len(set((r['home'],r['away'],r['date']) for r in all_rows))}")
print("Signature Prediction and Forecast: Sigma - Mahmoud Emad")
