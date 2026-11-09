import csv, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime
BASE=Path("data"); BASE.mkdir(exist_ok=True)
LEAGUES={"E0":"England","SP1":"Spain","I1":"Italy","D1":"Germany","F1":"France","N1":"Netherlands","P1":"Portugal","B1":"Belgium"}
SEASONS=["1516","1617","1718","1819","1920","2021","2122","2223","2324","2425","2526"]
def parse_date(s):
    s=s.strip()
    for fmt in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d"):
        try: return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except: pass
    return None
new=[]
for season in SEASONS:
    for div, lg in LEAGUES.items():
        url=f"https://www.football-data.co.uk/mmz4281/{season}/{div}.csv"
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                txt=r.read().decode(errors="ignore").splitlines()
        except urllib.error.HTTPError:
            print(f"Skip {season} {div} - no file"); continue
        except Exception as e:
            print(f"Err {season} {div} {e}"); continue
        rows=list(csv.DictReader(txt))
        cnt=0
        for row in rows:
            try:
                hg=row.get("FTHG","").strip(); ag=row.get("FTAG","").strip()
                ht=row.get("HomeTeam","").strip(); at=row.get("AwayTeam","").strip()
                if not hg or not ag or not ht or not at: continue
                dt=parse_date(row.get("Date",""))
                if not dt: continue
                new.append({"date":dt,"home_team":ht,"away_team":at,"home_goals":int(float(hg)),"away_goals":int(float(ag)),"league":lg,"status":"FINISHED","match_id":""})
                cnt+=1
            except: continue
        print(f"{season} {div} {lg}: +{cnt} total {len(new)}")
print(f"ARCHIVE COLLECTED: {len(new)}")
# ادمج مع القديم من غير تكرار
old=list(csv.DictReader(open(BASE/"sigma_history.csv", encoding="utf-8")))
keys=set((r["date"], r.get("home_team") or r.get("home"), r.get("away_team") or r.get("away")) for r in old)
merged=old[:]
for r in new:
    k=(r["date"], r["home_team"], r["away_team"])
    if k not in keys:
        keys.add(k); merged.append(r)
merged.sort(key=lambda x: x["date"])
print(f"MERGED TOTAL: {len(merged)} (old {len(old)} + archive new)")
with open(BASE/"sigma_history_full.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=["date","home_team","away_team","home_goals","away_goals","league","status","match_id"]); w.writeheader()
    for r in merged:
        w.writerow({k: r.get(k,"") for k in ["date","home_team","away_team","home_goals","away_goals","league","status","match_id"]})
print("Saved: data/sigma_history_full.csv")
