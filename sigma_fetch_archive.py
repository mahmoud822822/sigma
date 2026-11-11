import csv, urllib.request, pathlib
# 11 موسم × 8 دوريات - كودات football-data.co.uk الحقيقية
LEAGUES={"England":"E0","Spain":"SP1","Italy":"I1","Germany":"D1","France":"F1","Netherlands":"N1","Portugal":"P1","Belgium":"B1"}
SEASONS=["1516","1617","1718","1819","1920","2021","2122","2223","2324","2425","2526"]
out=[]; seen=set()
for season in SEASONS:
 for league,code in LEAGUES.items():
  url=f"https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
  try:
   print(f"Fetching {league} {season} ...")
   data=urllib.request.urlopen(url, timeout=30).read().decode(errors="ignore").splitlines()
   r=list(csv.DictReader(data))
   for row in r:
    try:
     h=row["HomeTeam"]; a=row["AwayTeam"]; hg=int(row["FTHG"]); ag=int(row["FTAG"]); d=row["Date"]
    except: continue
    mid=f"{d}-{h}-{a}"
    if mid in seen: continue
    seen.add(mid)
    out.append({"match_id":mid,"date":d,"league":league,"home":h,"away":a,"home_goals":hg,"away_goals":ag,"status":"FINISHED"})
  except Exception as e: print(f"Fail {league} {season}: {e}")
print(f"Total Real History: {len(out)}")
pathlib.Path("data").mkdir(exist_ok=True)
with open("data/sigma_history.csv","w",newline="",encoding="utf-8") as f:
 w=csv.DictWriter(f, fieldnames=["match_id","date","league","home","away","home_goals","away_goals","status"]); w.writeheader(); w.writerows(out)
print("Saved: data/sigma_history.csv")
# تحقق فوري - لو طلع 100% بيت بيكسب يبقى ديمو، لو طلع طبيعي يبقى حقيقي
from collections import Counter
c=Counter(r["league"] for r in out)
print(c)
n=len(out); hw=sum(1 for r in out if r["home_goals"]>r["away_goals"]); btts=sum(1 for r in out if r["home_goals"]>0 and r["away_goals"]>0); over=sum(1 for r in out if r["home_goals"]+r["away_goals"]>=3); avg=sum(r["home_goals"]+r["away_goals"] for r in out)/n
print(f"n={n} Avg={avg:.2f} HomeWin={hw/n*100:.1f}% BTTS={btts/n*100:.1f}% Over25={over/n*100:.1f}%")
print("لو Avg بين 2.6 و 3.1 و HomeWin بين 42% و 48% - يبقى تاريخ حقيقي")
