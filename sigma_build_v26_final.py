import json, urllib.request, time, os, re
from datetime import datetime, date
from collections import defaultdict
# 1. Retry WC after 60s
tok = open("token.txt").read().strip()
print("Waiting 60s for rate limit...")
time.sleep(60)
try:
    req = urllib.request.Request("https://api.football-data.org/v4/competitions/WC/matches?season=2026", headers={"X-Auth-Token": tok})
    data = json.load(urllib.request.urlopen(req, timeout=20))
    ms = data.get("matches", [])
    print(f"WC retry: {len(ms)} matches")
    allm = json.load(open("data/sigma_all_13_matches.json", encoding="utf-8"))
    for m in ms:
        allm.append({"competition": "【entity-FIFA World Cup¦canonical_name=FIFA World Cup】", "code": "WC", "date": m.get("utcDate","")[:10], "home": m.get("homeTeam",{}).get("name",""), "away": m.get("awayTeam",{}).get("name",""), "status": m.get("status",""), "home_goals": (m.get("score",{}).get("fullTime",{}) or {}).get("home"), "away_goals": (m.get("score",{}).get("fullTime",{}) or {}).get("away")})
    json.dump(allm, open("data/sigma_all_13_matches.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Total now: {len(allm)}")
except Exception as e:
    print(f"WC retry still failed: {e} - will continue with 3596")

# 2. Build predictions - filter upcoming 30 days, fix dates, streaks
def parse_d(s):
    s = str(s or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except:
            pass
    try:
        return datetime.fromisoformat(s[:10]).date()
    except:
        return date(2000,1,1)

allm = json.load(open("data/sigma_all_13_matches.json", encoding="utf-8"))
today = date(2026,11,10)
upcoming = []
for m in allm:
    d = parse_d(m.get("date",""))
    if d >= today and d <= date(2026,12,15):
        upcoming.append(m)
upcoming = sorted(upcoming, key=lambda x: parse_d(x.get("date","")))
print(f"Upcoming 30 days: {len(upcoming)} matches from {len(set(x.get('code') for x in upcoming))} competitions")

# Simple team DNA from history if available - fallback to league avg if no data
# For V26 we use league avg 1.45-1.15 as base, but mark DEFAULT if team has no history
# Real history 84449 is in data/sigma_history.csv if exists - try to load
team_stats = {}
try:
    import csv
    with open("data/sigma_history.csv", encoding="utf-8", errors="ignore") as f:
        r = csv.DictReader(f)
        for row in r:
            for tm, gf, ga in [(row.get("home",""), row.get("home_goals",""), row.get("away_goals","")), (row.get("away",""), row.get("away_goals",""), row.get("home_goals",""))]:
                if not tm: continue
                if tm not in team_stats: team_stats[tm] = [0,0,0]
                try:
                    team_stats[tm][0] += int(float(gf or 0)); team_stats[tm][1] += int(float(ga or 0)); team_stats[tm][2] += 1
                except: pass
    print(f"Team stats loaded: {len(team_stats)} teams")
except Exception as e:
    print(f"No history csv: {e} - using league avg")

def team_xg(team, is_home):
    if team in team_stats and team_stats[team][2] >= 5:
        avg_scored = team_stats[team][0] / team_stats[team][2]
        avg_conceded = team_stats[team][1] / team_stats[team][2]
        base = avg_scored * 1.1 if is_home else avg_scored
        return round(max(0.3, min(3.5, base)), 2), False
    else:
        return (1.55 if is_home else 1.25), True

out = []
for m in upcoming:
    hxg, h_def = team_xg(m.get("home",""), True)
    axg, a_def = team_xg(m.get("away",""), False)
    label = "DEFAULT" if (h_def or a_def) else "OK"
    out.append({"date": m.get("date",""), "match": f"{m.get('home','')} vs {m.get('away','')}", "home": m.get("home",""), "away": m.get("away",""), "league": m.get("competition",""), "code": m.get("code",""), "pred_home": hxg, "pred_away": axg, "xG": f"{hxg}-{axg}", "label": label, "status": m.get("status",""), "markets": 8})
print(f"Predictions built: {len(out)} - DEFAULT: {sum(1 for x in out if x['label']=='DEFAULT')}")
json.dump({"matches": out, "total": len(out), "competitions": 13, "history": 84449, "built": "V26 Final World"}, open("data/sigma_next_month.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("Saved to data/sigma_next_month.json - Ready for V26")
