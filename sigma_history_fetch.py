# Signature Prediction and Forecast: Sigma - Mahmoud Emad
import os, json, csv, urllib.request, urllib.error, time
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict
BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
COMP = "2021,2014,2019,2002,2015,2003,2017,2004"
MAP = {"Premier League":"England","La Liga":"Spain","Serie A":"Italy","Bundesliga":"Germany","Ligue 1":"France","Eredivisie":"Netherlands","Primeira Liga":"Portugal","Jupiler Pro League":"Belgium","Belgian Pro League":"Belgium","First Division A":"Belgium","Pro League":"Belgium"}
HIST_CSV = DATA / "sigma_history.csv"
STATS_JSON = DATA / "sigma_team_stats.json"
LEAGUE_JSON = DATA / "sigma_league_stats.json"
def get_token():
    return "".join(c for c in os.environ.get("FOOTBALL_DATA_TOKEN","").strip() if c.isascii() and c.isalnum())
def fetch_chunk(token, df, dt):
    url = f"https://api.football-data.org/v4/matches?dateFrom={df}&dateTo={dt}&competitions={COMP}"
    req = urllib.request.Request(url, headers={"X-Auth-Token": token})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode()).get("matches", [])
        except urllib.error.HTTPError as e:
            print(f"API {e.code} {df}->{dt} attempt {attempt+1}")
            if e.code == 429:
                print("Rate limit - sleep 65s")
                time.sleep(65)
                continue
            return []
        except Exception as e:
            print(f"Err {e} {df}")
            return []
    return []
def load_existing():
    rows = {}
    if HIST_CSV.exists():
        try:
            with open(HIST_CSV, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    rows[r["match_id"]] = r
        except: pass
    return rows
def save_history(rows_dict):
    rows = sorted(rows_dict.values(), key=lambda x: x["date"])
    with open(HIST_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["match_id","date","league","home","away","home_goals","away_goals","status"])
        w.writeheader(); w.writerows(rows)
    print(f"History saved: {len(rows)} matches -> {HIST_CSV}")
def build_stats(rows_dict):
    by_team = defaultdict(list)
    for r in rows_dict.values():
        if r["status"] != "FINISHED": continue
        try: hg=int(r["home_goals"]); ag=int(r["away_goals"])
        except: continue
        by_team[r["home"]].append({"date":r["date"],"opp":r["away"],"scored":hg,"conceded":ag,"home":True,"result":"W" if hg>ag else "D" if hg==ag else "L"})
        by_team[r["away"]].append({"date":r["date"],"opp":r["home"],"scored":ag,"conceded":hg,"home":False,"result":"W" if ag>hg else "D" if ag==hg else "L"})
    stats = {}
    for team, ms in by_team.items():
        ms_sorted = sorted(ms, key=lambda x: x["date"], reverse=True)[:50]
        n = len(ms_sorted)
        scored = sum(x["scored"] for x in ms_sorted); conceded = sum(x["conceded"] for x in ms_sorted)
        home_ms = [x for x in ms_sorted if x["home"]]; away_ms = [x for x in ms_sorted if not x["home"]]
        wins = sum(1 for x in ms_sorted if x["result"]=="W"); draws = sum(1 for x in ms_sorted if x["result"]=="D")
        btts = sum(1 for x in ms_sorted if x["scored"]>0 and x["conceded"]>0)
        over25 = sum(1 for x in ms_sorted if x["scored"]+x["conceded"]>=3)
        last5 = ms_sorted[:5]
        stats[team] = {
            "n": n, "scored_avg": round(scored/max(1,n),2), "conceded_avg": round(conceded/max(1,n),2),
            "home_scored_avg": round(sum(x["scored"] for x in home_ms)/max(1,len(home_ms)),2) if home_ms else 1.55,
            "away_scored_avg": round(sum(x["scored"] for x in away_ms)/max(1,len(away_ms)),2) if away_ms else 1.25,
            "home_conceded_avg": round(sum(x["conceded"] for x in home_ms)/max(1,len(home_ms)),2) if home_ms else 1.25,
            "away_conceded_avg": round(sum(x["conceded"] for x in away_ms)/max(1,len(away_ms)),2) if away_ms else 1.55,
            "win_rate": round(wins/max(1,n)*100,1), "draw_rate": round(draws/max(1,n)*100,1),
            "btts_rate": round(btts/max(1,n)*100,1), "over25_rate": round(over25/max(1,n)*100,1),
            "form": "".join(x["result"] for x in last5), "last_date": ms_sorted[0]["date"] if ms_sorted else "",
            "last50_dates": f"{ms_sorted[-1]['date']} -> {ms_sorted[0]['date']}" if ms_sorted else ""
        }
    STATS_JSON.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Team stats: {len(stats)} teams, each up to 50 -> {STATS_JSON}")
    league = {}
    by_league = defaultdict(list)
    for r in rows_dict.values():
        if r["status"]!="FINISHED": continue
        try: by_league[r["league"]].append((int(r["home_goals"]), int(r["away_goals"])))
        except: continue
    for lg, pairs in by_league.items():
        n=len(pairs); avg=sum(h+a for h,a in pairs)/max(1,n)
        home_win=sum(1 for h,a in pairs if h>a)/max(1,n)*100
        btts=sum(1 for h,a in pairs if h>0 and a>0)/max(1,n)*100
        league[lg]={"n":n,"avg_goals":round(avg,2),"home_win":round(home_win,1),"btts":round(btts,1)}
    LEAGUE_JSON.write_text(json.dumps(league, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"League stats: {league}")
    return stats
def main():
    import sys
    mode = "--daily" if "--daily" in sys.argv else "--init"
    token = get_token()
    if len(token)!=32:
        print(f"ERROR: Token len {len(token)} != 32"); return
    today = date.today()
    if mode=="--daily":
        start = today - timedelta(days=3); end = today
        print(f"History Daily: {start} -> {end} (نتائج جديدة)")
    else:
        start = today - timedelta(days=365); end = today
        print(f"History Init: {start} -> {end} (365 يوم = ~50 لكل فريق)")
    existing = load_existing()
    print(f"Existing history: {len(existing)}")
    cur = start
    total_new = 0
    while cur <= end:
        chunk_end = min(cur+timedelta(days=9), end)
        print(f"Fetching {cur} -> {chunk_end} ...")
        ms = fetch_chunk(token, cur.isoformat(), chunk_end.isoformat())
        print(f"  got {len(ms)}")
        for m in ms:
            if m.get("status")!="FINISHED": continue
            try:
                mid=str(m["id"]); comp=m.get("competition",{}).get("name","Default"); league=MAP.get(comp,"Default")
                home=m["homeTeam"]["name"]; away=m["awayTeam"]["name"]
                hg=m["score"]["fullTime"]["home"]; ag=m["score"]["fullTime"]["away"]
                if hg is None or ag is None: continue
                if mid not in existing:
                    total_new+=1
                existing[mid]={"match_id":mid,"date":m["utcDate"][:10],"league":league,"home":home,"away":away,"home_goals":hg,"away_goals":ag,"status":"FINISHED"}
            except Exception as e: continue
        cur = chunk_end+timedelta(days=1)
        if cur <= end: time.sleep(7)
    print(f"New: {total_new} | Total: {len(existing)}")
    save_history(existing)
    build_stats(existing)
    print("Done - History + Stats ready for Learning")
if __name__=="__main__":
    main()
