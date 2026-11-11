import os, json, csv, time, urllib.request, urllib.error
from datetime import date, timedelta
from pathlib import Path
BASE=Path("data"); BASE.mkdir(exist_ok=True)
COMP="2021,2014,2019,2002,2015,2003,2017,2004"
MAP={"Premier League":"England","La Liga":"Spain","Serie A":"Italy","Bundesliga":"Germany","Ligue 1":"France","Eredivisie":"Netherlands","Primeira Liga":"Portugal","Jupiler Pro League":"Belgium"}
def fetch(token, df, dt):
    url=f"https://api.football-data.org/v4/matches?dateFrom={df}&dateTo={dt}&competitions={COMP}&status=FINISHED"
    for attempt in range(3):
        req=urllib.request.Request(url, headers={"X-Auth-Token": token})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode()).get("matches", [])
        except urllib.error.HTTPError as e:
            print(f"API {e.code} {df} attempt {attempt+1}")
            if e.code==429: time.sleep(60)
            elif e.code in (400,403,404): return []
            else: time.sleep(5)
        except Exception as e:
            print(f"Err {e}"); time.sleep(5)
    return []
token="".join(c for c in os.environ.get("FOOTBALL_DATA_TOKEN","").strip() if c.isascii() and c.isalnum())
if len(token)!=32:
    print("ERROR: Token len !=32 - run: export FOOTBALL_DATA_TOKEN=YOUR_32_CHAR_TOKEN")
    raise SystemExit
start=date(2020,1,1); end=date.today(); cur=start; seen=set(); out=[]
# لو فيه ملف قديم احفظه
old=BASE/"sigma_history.csv"
if old.exists():
    print("Backup old history...")
    import shutil; shutil.copy(old, BASE/"sigma_history_backup.csv")
chunk=timedelta(days=30)
while cur<=end:
    nxt=min(cur+chunk-timedelta(days=1), end)
    ms=fetch(token, cur.isoformat(), nxt.isoformat())
    new=0
    for m in ms:
        mid=m.get("id")
        if mid in seen: continue
        seen.add(mid)
        comp=m.get("competition",{}).get("name","Default"); lg=MAP.get(comp,"Default")
        out.append({"date":m["utcDate"][:10],"home_team":m["homeTeam"]["name"],"away_team":m["awayTeam"]["name"],"home_goals":m["score"]["fullTime"]["home"],"away_goals":m["score"]["fullTime"]["away"],"league":lg,"status":m.get("status","FINISHED"),"match_id":mid})
        new+=1
    print(f"{cur} -> {nxt}: got {len(ms)} new {new} total {len(out)}")
    cur=nxt+timedelta(days=1); time.sleep(6)
print(f"TOTAL COLLECTED: {len(out)} real finished matches")
out.sort(key=lambda x: x["date"])
with open(BASE/"sigma_history_full.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=["date","home_team","away_team","home_goals","away_goals","league","status","match_id"]); w.writeheader(); w.writerows(out)
print("Saved: data/sigma_history_full.csv")
