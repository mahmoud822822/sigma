import csv, json, re
from pathlib import Path
from datetime import date
BASE = Path(".")
DATA = BASE / "data"
def norm(n):
    s = str(n or "").lower().strip()
    s = s.replace("ß","ss").replace("ä","a").replace("ö","o").replace("ü","u").replace(".","").replace("-"," ")
    s = re.sub(r"\s+", " ", s).strip()
    # drop prefix tokens
    toks = [t for t in s.split() if t not in ("1","fc","vfl","sv","sc","spvgg","sg","tsv","vfb","vsg","djk","msv","07","04","05","98","1846","1899","1921","1860","11","20")]
    s2 = " ".join(toks)
    # drop eintracht/borussia prefix, keep city name
    for p in ("eintracht ", "borussia "):
        if s2.startswith(p):
            s2 = s2[len(p):].strip()
    if "gladbach" in s2:
        s2 = "gladbach"
    if "koln" in s2 or "cologne" in s2:
        s2 = "cologne"
    if "munchen" in s2 or "munich" in s2:
        s2 = "munich"
    if "nurnberg" in s2 or "nuremberg" in s2:
        s2 = "nuremberg"
    if s2.startswith("hertha"):
        s2 = "hertha"
    return s2
def match(a,b):
    return a==b or a in b or b in a
# fix history spaces
hp = DATA / "sigma_history.csv"
rows = list(csv.DictReader(open(hp, encoding="utf-8")))
for r in rows:
    for k in list(r.keys()):
        if isinstance(r[k], str):
            r[k] = r[k].strip()
with open(hp, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","home","away","home_goals","away_goals","league","status","source"])
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k,"") for k in ["date","home","away","home_goals","away_goals","league","status","source"]})
print(f"history cleaned: {len(rows)}")
# build history set with norm
hist = []
for r in rows:
    try:
        d = str(r.get("date") or "")[:10]
        if not d: continue
        hist.append((d, norm(r.get("home")), norm(r.get("away"))))
    except: pass
pu_path = DATA / "sigma_passed_unverified.json"
pu = json.loads(pu_path.read_text(encoding="utf-8"))
ms = pu.get("matches", [])
kept = []
removed = []
for m in ms:
    d = str(m.get("date") or "")[:10]
    nh, na = norm(m.get("home")), norm(m.get("away"))
    found = False
    for hd, hh, ha in hist:
        # allow 1-day shift for Heidenheim case
        try:
            dd = abs((date.fromisoformat(d) - date.fromisoformat(hd)).days) if d and hd else 99
        except: dd = 99
        if dd <= 1 and match(nh, hh) and match(na, ha):
            found = True
            break
    if found:
        removed.append(m)
    else:
        kept.append(m)
print(f"passed_unverified: {len(ms)} -> {len(kept)} (removed {len(removed)} by norm-match)")
for r in removed:
    print(f"  FIXED-REMOVED: {r.get('date')} {r.get('home')} vs {r.get('away')}")
pu["matches"] = kept
pu["total"] = len(kept)
pu_path.write_text(json.dumps(pu, ensure_ascii=False, indent=2), encoding="utf-8")
with open(DATA / "sigma_passed_unverified.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","home","away","league","competition","source","status","reason"])
    w.writeheader()
    for r in kept:
        w.writerow({k: r.get(k,"") for k in ["date","home","away","league","competition","source","status","reason"]})
print("DONE - fix applied, now re-run sigma_run_full.py")
