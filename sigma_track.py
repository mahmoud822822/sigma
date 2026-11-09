import csv, pathlib, re, unicodedata
def clean(n):
    n=unicodedata.normalize("NFKD", str(n)).encode("ascii","ignore").decode()
    n=n.lower().strip(); n=re.sub(r"[^a-z0-9 ]","",n)
    n=re.sub(r"\b(fc|cf|afc|sc|ac|ssc|us|rcd|real|club)\b","",n).strip()
    n=re.sub(r"\s+"," ",n)
    if "munchen" in n: n=n.replace("munchen","munich")
    if "eindhoven" in n: return "psv"
    if n.startswith("psv"): return "psv"
    if "bay" in n and "ern" in n: return "bayern"
    if n in ("lille osc","lille"): return "lille"
    if n.startswith("paris"): return "paris saint germain"
    if "sporting" in n or n.startswith("sp lisbon"): return "sporting lisbon"
    if "man city" in n or "manchester city" in n: return "manchester city"
    return n
pred=list(csv.DictReader(open("data/sigma_mega_predictions.csv", encoding="utf-8")))
hist=list(csv.DictReader(open("data/sigma_history.csv", encoding="utf-8")))
ver_path=pathlib.Path("data/sigma_real_verified.csv")
ver=list(csv.DictReader(open(ver_path, encoding="utf-8"))) if ver_path.exists() else []
fields=list(ver[0].keys()) if ver else ["match","predicted_home","predicted_away","real_home","real_away","bet","bet_result"]
print(f"Verified fields: {fields} total {len(ver)}")
have=set(clean(r.get("match","")) for r in ver)
hmap={}
for r in hist:
    ht=clean(r.get("home_team","")); at=clean(r.get("away_team",""))
    try: hg=int(float(r.get("home_goals",""))); ag=int(float(r.get("away_goals","")))
    except: continue
    hmap[(r.get("date",""), ht, at)]=(hg,ag)
new=0
for pr in pred:
    if " vs " not in pr["match"]: continue
    ht_raw,at_raw=pr["match"].split(" vs ")
    ht=clean(ht_raw); at=clean(at_raw)
    if clean(pr["match"]) in have: continue
    key=(pr.get("date",""), ht, at)
    if key not in hmap: continue
    rh,ra=hmap[key]
    xh,xa=pr["xG"].split("-"); ph=int(round(float(xh))); pa=int(round(float(xa)))
    def pick(a,b): return "1" if a>b else "X" if a==b else "2"
    res="correct" if pick(ph,pa)==pick(rh,ra) else "incorrect"
    row={"match":pr["match"],"predicted_home":ph,"predicted_away":pa,"real_home":rh,"real_away":ra,"bet":"1X2","bet_result":res}
    ver.append({k: row.get(k,"") for k in fields})
    have.add(clean(pr["match"])); new+=1
    print(f"NEW {pr['date']} {pr['match']} pred {ph}-{pa} real {rh}-{ra} {res}")
print(f"Added {new} - Verified total {len(ver)}")
if new>0:
    with open(ver_path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(ver)
    print("Saved verified")
else: print("No mega finished yet - matches start 2026-11-20")
