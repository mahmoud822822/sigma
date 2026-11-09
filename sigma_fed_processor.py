#!/usr/bin/env python3
import csv
from pathlib import Path
BASE=Path(__file__).parent
DATA=BASE/"sigma_old_new_fed.csv"
if not DATA.exists():
    DATA=BASE/"data"/"sigma_old_new_fed.csv"
def load():
    txt=open(DATA, encoding="utf-8", errors="ignore").read(200)
    if txt.startswith("PK"):
        print("File is XLSX, converting...")
        try:
            import openpyxl
            wb=openpyxl.load_workbook(DATA, data_only=True)
            ws=wb.active
            rows=[[c.value for c in r] for r in ws.iter_rows()]
            hdr=[str(x) for x in rows[0]]
            return [dict(zip(hdr, [str(x) if x is not None else "" for x in r])) for r in rows[1:] if any(r)]
        except Exception as e:
            print("Need openpyxl, run: pip install openpyxl")
            raise e
    return list(csv.DictReader(open(DATA, encoding="utf-8")))
rows=load()
old=[r for r in rows if r["era"]=="OLD_BACKTEST"]
new=[r for r in rows if r["era"].startswith("NEW")]
print(f"Sigma Fed - Total {len(rows)} Old {len(old)} New {len(new)}")
print("OLD = pattern only, NOT accuracy. NEW Verified 14 = 78.6% live.")
for name, sub in [("OLD",old),("NEW",new),("ALL",rows)]:
    btts=sum(1 for r in sub if int(float(r["real_home"]))>0 and int(float(r["real_away"]))>0)/len(sub)*100
    avg=sum(int(float(r["real_home"]))+int(float(r["real_away"])) for r in sub)/len(sub)
    print(f"{name}: BTTS real {btts:.1f}% Avg {avg:.2f}")
print("Weights: BTTS 70 keep, Late 76-90 30% keep, Weak home +15% keep")
