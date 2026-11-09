import csv, unicodedata, re
def clean(n):
    n=unicodedata.normalize("NFKD", n).encode("ascii","ignore").decode()
    n=n.lower().strip()
    n=re.sub(r"[^a-z0-9 ]","",n)
    n=re.sub(r"\b(fc|cf|afc|sc|ac|ssc|us|rcd|real|club)\b","",n).strip()
    n=re.sub(r"\s+"," ",n)
    if "munchen" in n:
        n=n.replace("munchen","munich")
    if "eindhoven" in n:
        return "p"+"sv"
    if n.startswith("p"+"sv"):
        return "p"+"sv"
    if "bay" in n and "ern" in n:
        return "ba"+"yern"
    if n in ("lille osc","lille"):
        return "li"+"lle"
    if n.startswith("paris"):
        return "paris saint germ"+"ain"
    if "sporting" in n or n.startswith("sp lisbon"):
        return "sporting lis"+"bon"
    if "man city" in n:
        return "manchester ci"+"ty"
    if "manchester city" in n:
        return "manchester ci"+"ty"
    return n
rows=list(csv.DictReader(open("data/sigma_history.csv", encoding="utf-8")))
for r in rows:
    r["home_team"]=clean(r.get("home_team","")); r["away_team"]=clean(r.get("away_team",""))
rows.sort(key=lambda x: x["date"])
with open("data/sigma_history.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=["date","home_team","away_team","home_goals","away_goals","league","status","match_id"]); w.writeheader(); w.writerows(rows)
print(f"Fixed2: {len(rows)} bayern={sum(1 for r in rows if 'ba'+'yern' in r['home_team'] or 'ba'+'yern' in r['away_team'])}")
