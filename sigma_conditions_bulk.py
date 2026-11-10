import csv, pathlib
from sigma_conditions import team_attack, LEAGUE_CORNER
rows=list(csv.DictReader(open("data/sigma_mega_predictions.csv", encoding="utf-8")))
out=[]
for r in rows:
    try: home,away=r["match"].split(" vs ")
    except: continue
    lg=r.get("league","Default"); ch,ca=LEAGUE_CORNER.get(lg, LEAGUE_CORNER["Default"])
    ha=team_attack(home, True); aa=team_attack(away, False)
    cor_h=round(max(2,min(11, ch*(0.75+0.25*(ha/1.55)))),1); cor_a=round(max(2,min(11, ca*(0.75+0.25*(aa/1.25)))),1)
    thr_h=round(max(12,min(35, 23*(0.8+0.2*(ha/1.55)))),1); thr_a=round(max(10,min(32, 19*(0.8+0.2*(aa/1.25)))),1)
    r["Corners"]=f"{cor_h}-{cor_a} Tot {round(cor_h+cor_a,1)}"
    r["Throw"]=f"{thr_h}-{thr_a} Tot {round(thr_h+thr_a,1)}"
    out.append(r)
print(f"Bulk: {len(out)}")
pathlib.Path("data/sigma_mega_conditions.csv").write_text("", encoding="utf-8")
with open("data/sigma_mega_conditions.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print("Saved: data/sigma_mega_conditions.csv")
