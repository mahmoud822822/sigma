import csv, json
from pathlib import Path
M={"Spanien":"Spain","Norwegen":"Norway","Tschechien":"Czech Republic","Kroatien":"Croatia","Deutschland":"Germany","Frankreich":"France","Italien":"Italy","England":"England","Portugal":"Portugal","Niederlande":"Netherlands","Holland":"Netherlands","Osterreich":"Austria","Schweiz":"Switzerland","Belgien":"Belgium","Danemark":"Denmark","Schweden":"Sweden","Finnland":"Finland","Polen":"Poland","Ungarn":"Hungary","Griechenland":"Greece","Turkei":"Turkey","Rumanien":"Romania","Bulgarien":"Bulgaria","Serbien":"Serbia","Slowakei":"Slovakia","Slowenien":"Slovenia","Irland":"Ireland","Schottland":"Scotland","Wales":"Wales","Nordirland":"Northern Ireland"}
p=Path("data/sigma_history.csv")
rows=list(csv.DictReader(open(p, encoding="utf-8")))
f=0
for r in rows:
    for k in ["home","away"]:
        if r.get(k) in M: r[k]=M[r[k]]; f+=1
with open(p,"w",newline="",encoding="utf-8") as fh:
    w=csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("history fixed", f)
fp=Path("data/sigma_universal_fixtures.json")
d=json.load(open(fp, encoding="utf-8"))
lst=d.get("matches") or d.get("fixtures") or d if isinstance(d, dict) else d
f2=0
for r in lst:
    for k in ["home","away","home_team","away_team"]:
        if r.get(k) in M: r[k]=M[r[k]]; f2+=1
    for tk in ["homeTeam","awayTeam"]:
        if isinstance(r.get(tk), dict) and r[tk].get("name") in M: r[tk]["name"]=M[r[tk]["name"]]; f2+=1
if isinstance(d, dict) and "matches" in d: d["matches"]=lst
elif isinstance(d, dict) and "fixtures" in d: d["fixtures"]=lst
else: d=lst
json.dump(d, open(fp,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("fixtures fixed", f2)
print("DONE - German names -> English")