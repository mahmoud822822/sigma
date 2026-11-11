import csv, urllib.request, collections
from pathlib import Path
DATA = Path("data"); DATA.mkdir(exist_ok=True)
def get(u):
    try:
        r = urllib.request.Request(u, headers={"User-Agent":"Sigma"})
        with urllib.request.urlopen(r, timeout=60) as x: return x.read().decode("utf-8", errors="ignore")
    except Exception as e: print("SKIP", e); return None
def ml(t):
    t=str(t or "").lower()
    if "world cup" in t: return "World Cup"
    if "uefa euro" in t: return "Euro"
    if "nations league" in t: return "UEFA Nations League"
    if "copa am" in t: return "Copa America"
    if "african" in t: return "African Cup"
    if "asian" in t: return "Asian Cup"
    if "gold cup" in t: return "Gold Cup"
    return "International"
new=[]
txt=get("https://raw.githubusercontent.com/martj42/international_results/master/results.csv")
rows=list(csv.DictReader(txt.splitlines())); print("raw", len(rows))
for r in rows:
    d=str(r.get("date") or "")[:10]
    if d < "2010-01-01": continue
    h=(r.get("home_team") or "").strip(); a=(r.get("away_team") or "").strip()
    s1,s2=r.get("home_score"),r.get("away_score")
    if not h or not a or s1 in (None,"") or s2 in (None,""): continue
    new.append({"date":d,"home":h,"away":a,"home_goals":int(float(s1)),"away_goals":int(float(s2)),"league":ml(r.get("tournament")),"status":"FINISHED","source":"international_results"})
print("kept", len(new))
hist=DATA/"sigma_history.csv"
old=list(csv.DictReader(open(hist, encoding="utf-8"))) if hist.exists() else []
print("old", len(old))
seen={(r["date"],r["home"].lower(),r["away"].lower(),r["league"].lower()) for r in old}
add=0
for r in new:
    k=(r["date"],r["home"].lower(),r["away"].lower(),r["league"].lower())
    if k not in seen: seen.add(k); old.append(r); add+=1
old.sort(key=lambda x: x["date"])
with open(hist,"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, extrasaction='ignore', fieldnames=["date","home","away","home_goals","away_goals","league","status","source"]); w.writeheader(); w.writerows(old)
print("added", add, "total", len(old))
c=collections.Counter(r["league"] for r in old)
for lg in ["World Cup","Euro","UEFA Nations League","African Cup","Asian Cup","Copa America","Gold Cup","International"]:
    if c.get(lg): print(lg, c[lg])
print("DONE")