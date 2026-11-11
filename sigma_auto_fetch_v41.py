#!/usr/bin/env python3
# Sigma Auto-Fetch V41 - C: Expansion - 90 days + Cups + Europe + 2027
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# Fixes old COMP bug: 2004 is BL2 (2. Bundesliga), NOT Jupiler. Belgium is 2009 BJL.
# Free tier = 12 comps only. Expanded comps need paid token - if API says 403, fall back to Free and warn.
# Token: env FOOTBALL_DATA_TOKEN first, then ~/token.txt, then ./token.txt (never print token)
import os, json, csv, urllib.request, urllib.error, time
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

FREE_COMP = "2021,2014,2019,2002,2015,2003,2017,2016,2001,2013,2000,2018"
# 2021 PL, 2014 La Liga, 2019 Serie A, 2002 Bundesliga, 2015 Ligue1, 2003 Eredivisie,
# 2017 Primeira, 2016 Championship, 2001 Champions League, 2013 Brazil Serie A, 2000 WC, 2018 EC
EXPANDED_COMP = FREE_COMP + ",2009,2070,2146,2154,2011,2079"
# + 2009 Jupiler (Belgium, FIXED), 2070 Super Lig (Turkey), 2146 Europa, 2154 Conference,
#   2011 DFB-Pokal, 2079 Copa del Rey

MAP = {"Premier League": "England", "La Liga": "Spain", "Primera Division": "Spain",
       "Serie A": "Italy", "Bundesliga": "Germany", "Ligue 1": "France",
       "Eredivisie": "Netherlands", "Primeira Liga": "Portugal",
       "Championship": "England 2", "UEFA Champions League": "Europe",
       "UEFA Europa League": "Europe", "UEFA Conference League": "Europe",
       "Campeonato Brasileiro Série A": "Brazil", "Jupiler Pro League": "Belgium",
       "Süper Lig": "Turkey", "DFB-Pokal": "Germany Cup", "Copa del Rey": "Spain Cup",
       "FIFA World Cup": "World", "European Championship": "Europe"}

def get_token():
    t = "".join(c for c in os.environ.get("FOOTBALL_DATA_TOKEN", "").strip() if c.isascii() and c.isalnum())
    if len(t) == 32:
        return t
    for cand in [Path.home() / "token.txt", BASE / "token.txt", DATA / "token.txt"]:
        try:
            if cand.exists():
                raw = cand.read_text(encoding="utf-8").strip()
                t2 = "".join(c for c in raw if c.isascii() and c.isalnum())
                if len(t2) == 32:
                    print(f"Token loaded from {cand.name} (not printed)")
                    return t2
        except Exception:
            pass
    return t

def fetch_chunk(token, df, dt, comps):
    url = f"https://api.football-data.org/v4/matches?dateFrom={df}&dateTo={dt}&competitions={comps}"
    req = urllib.request.Request(url, headers={"X-Auth-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode()).get("matches", []), None
    except urllib.error.HTTPError as e:
        return [], e.code
    except Exception as e:
        return [], str(e)

def main():
    today = date.today()
    nxt = today + timedelta(days=90)  # Expansion: 90 days, reaches into 2027
    print(f"Sigma Auto-Fetch V41 - {today} -> {nxt} (90 days) in 10-day chunks")
    token = get_token()
    if len(token) != 32:
        print(f"ERROR: Token len {len(token)} != 32 - set env or ~/token.txt (32 chars, no Arabic)")
        return
    # Try Expanded first, fall back to Free on 403
    comps = EXPANDED_COMP
    print("Trying Expanded comps (Free + Belgium + Turkey + Europe Cups)...")
    all_matches = []
    cur = today
    used_expanded = True
    while cur <= nxt:
        chunk_end = min(cur + timedelta(days=9), nxt)
        ms, err = fetch_chunk(token, cur.isoformat(), chunk_end.isoformat(), comps)
        if err == 403 and used_expanded:
            print("API 403 on Expanded - your token is Free tier. Falling back to Free 12 comps only.")
            print("Turkey / Europa / Conference / Jupiler will NOT be in this fetch (need paid token).")
            comps = FREE_COMP
            used_expanded = False
            ms, err = fetch_chunk(token, cur.isoformat(), chunk_end.isoformat(), comps)
        if err:
            print(f"  API err {err} for {cur}->{chunk_end}")
        else:
            print(f"  {cur} -> {chunk_end}: got {len(ms)}")
        all_matches.extend(ms)
        cur = chunk_end + timedelta(days=1)
        time.sleep(1)
    print(f"Fetched total: {len(all_matches)} matches - comps used: {'Expanded' if used_expanded else 'Free'}")
    by = {}
    rows = []
    for m in all_matches:
        comp = m.get("competition", {}).get("name", "Default")
        league = MAP.get(comp, "Default")
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        match = f"{home} vs {away}"
        by[match] = {"match": match, "date": m["utcDate"][:10], "league": league,
                     "competition": comp, "stage": m.get("stage", ""), "status": m.get("status", "")}
        rows.append({"match": match, "date": m["utcDate"][:10], "league": league,
                     "competition": comp, "stage": m.get("stage", ""), "status": m.get("status", "")})
    payload = {"generated": str(today), "from": str(today), "to": str(nxt), "range_days": 90,
               "comps_used": "Expanded" if used_expanded else "Free",
               "total_matches": len(by), "matches": list(by.values())}
    (DATA / "sigma_next_month.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if rows:
        with open(DATA / "sigma_next_month.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print(f"Saved: {len(by)} matches -> data/sigma_next_month.json")
    # Auto-run V41 engine if present - one command does B+C
    engine = BASE / "sigma_v41_engine.py"
    if engine.exists():
        print("Auto-running sigma_v41_engine.py (Elo + Dixon-Coles + Form)...")
        import subprocess, sys
        r = subprocess.run([sys.executable, str(engine)])
        print(f"Engine exit: {r.returncode}")
    else:
        print("Next: python3 sigma_v41_engine.py  (to compute Elo/Form predictions)")

if __name__ == "__main__":
    main()
