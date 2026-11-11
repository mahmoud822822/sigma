import json, csv, re
from datetime import datetime, date
# 1. Check history header
with open("data/sigma_history.csv", encoding="utf-8", errors="ignore") as f:
    r = csv.DictReader(f)
    print("History columns:", r.fieldnames)
    rows = list(r)[:3]
    for row in rows:
        print(row)
