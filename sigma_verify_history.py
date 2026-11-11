import csv, collections
rows=list(csv.DictReader(open("data/sigma_history.csv", encoding="utf-8")))
n=len(rows)
hw=sum(1 for r in rows if int(r["home_goals"])>int(r["away_goals"]))
btts=sum(1 for r in rows if int(r["home_goals"])>0 and int(r["away_goals"])>0)
over=sum(1 for r in rows if int(r["home_goals"])+int(r["away_goals"])>=3)
avg=sum(int(r["home_goals"])+int(r["away_goals"]) for r in rows)/n
print(f"Real History: n={n}")
print(f"Avg={avg:.2f} HomeWin={hw/n*100:.1f}% BTTS={btts/n*100:.1f}% Over25={over/n*100:.1f}%")
print(f"Leagues: {collections.Counter(r['league'] for r in rows)}")
print(f"Unique matches: {len(set(r['match_id'] for r in rows))}")
print("لو Avg بين 2.6 و 3.1 و HomeWin بين 42% و 48% - يبقى تاريخ حقيقي 100%")
