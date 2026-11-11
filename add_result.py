import csv, pathlib, re, shutil
from datetime import date
BASE = pathlib.Path("data/sigma_real_verified.csv")
if BASE.exists():
    shutil.copy(BASE, BASE.with_suffix(".backup.csv"))
    print("backup done")
def num(prompt):
    s = input(prompt).strip()
    m = re.search(r"\d+", s)
    return int(m.group(0)) if m else 0
print("Add verified result - Sigma")
match = input("Match (Home vs Away): ").strip()
d = input(f"Date [{date.today()}]: ").strip() or str(date.today())
league = input("League: ").strip() or "England"
ph = num("Predicted home: ")
pa = num("Predicted away: ")
rh = num("Real home: ")
ra = num("Real away: ")
bet = input("Bet: ").strip()
res = input("Bet result (correct/wrong): ").strip() or "correct"
notes = input("Notes: ").strip()
with open(BASE, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow([match, d, league, ph, pa, rh, ra, bet, res, notes])
print("Saved - now run Eval")
