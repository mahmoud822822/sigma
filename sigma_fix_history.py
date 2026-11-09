import csv
from pathlib import Path
BASE=Path("data")
# 1) الارشيف السليم من الملف الحالي - شيل الفاضي
cur=list(csv.DictReader(open(BASE/"sigma_history.csv", encoding="utf-8")))
good=[r for r in cur if str(r.get("home_team","")).strip() and str(r.get("away_team","")).strip()]
print(f"Good archive: {len(good)}")
# 2) القديم من الباك اب - ظبط اسماء الاعمدة
bak_path=BASE/"sigma_history_backup.csv"
old=[]
if bak_path.exists():
    for r in csv.DictReader(open(bak_path, encoding="utf-8")):
        ht=r.get("home_team") or r.get("home") or r.get("homeTeam") or ""
        at=r.get("away_team") or r.get("away") or r.get("awayTeam") or ""
        if not str(ht).strip() or not str(at).strip(): continue
        old.append({"date":r.get("date",""),"home_team":str(ht).strip(),"away_team":str(at).strip(),"home_goals":r.get("home_goals",""),"away_goals":r.get("away_goals",""),"league":r.get("league",""),"status":r.get("status","FINISHED"),"match_id":r.get("match_id","")})
    print(f"Backup old: {len(old)}")
keys=set((r["date"], r["home_team"], r["away_team"]) for r in good)
merged=good[:]
for r in old:
    k=(r["date"], r["home_team"], r["away_team"])
    if k not in keys:
        keys.add(k); merged.append(r)
merged.sort(key=lambda x: x["date"])
print(f"FIXED TOTAL: {len(merged)}")
with open(BASE/"sigma_history.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=["date","home_team","away_team","home_goals","away_goals","league","status","match_id"]); w.writeheader()
    for r in merged: w.writerow({k: r.get(k,"") for k in ["date","home_team","away_team","home_goals","away_goals","league","status","match_id"]})
print("Saved fixed: data/sigma_history.csv")
