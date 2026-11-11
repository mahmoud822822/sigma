#!/usr/bin/env python3
# Sigma V44 Universal Fetch - FREE ONLY, no payment
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# Layers (all free):
#  1) football-data.org Free 12 (token, 10 req/min) + test EL (2146) + UCL-Conference (2154) ONE BY ONE
#     - old V41 tried them in ONE bulk call, so one 403 killed all. V44 tests each alone.
#  2) OpenLigaDB - NO KEY, free - Nations League A (nla/5978, 48 fixtures) + DFB-Pokal (dfb/4945) + 2. Bundesliga
#  3) Open files - if user drops CSV/JSON in data/: data/open_matchday.csv or data/openfootball_*.json (75 comps, football.json)
#  4) MANUAL - data/sigma_manual_fixtures.csv - ANY match in the world, user adds it. This guarantees "any activity".
# Output: data/sigma_universal_fixtures.json - unified format for V44 engine.
# Unified fields: date, home_team, away_team, match, league, competition, competition_type, stage, group,
#                 source (AUTO/OPEN/MANUAL), source_detail, country
import os, json, csv, urllib.request, urllib.error, time
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

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

def canon(n):
    if not n:
        return ""
    s = str(n).strip()
    low = s.lower()
    if low.endswith(" fc"):
        s = s[:-3].strip()
        low = s.lower()
    mapping = {"man utd": "Man Utd", "manchester united": "Man Utd", "man united": "Man Utd",
               "man city": "Man City", "manchester city": "Man City", "barca": "Barcelona",
               "real": "Real Madrid", "real madrid": "Real Madrid", "atletico": "Atletico",
               "atletico madrid": "Atletico", "crystal palace": "Crystal Palace", "palace": "Crystal Palace",
               "villa": "Aston Villa", "aston villa": "Aston Villa", "brugge": "Club Brugge"}
    return mapping.get(low, s)

def is_numeric_name(s):
    try:
        float(str(s).strip())
        return True
    except Exception:
        return False

def norm_match(date_s, home, away, league, competition, ctype, stage, group, source, detail, country=""):
    h, a = canon(home), canon(away)
    if not h or not a or is_numeric_name(h) or is_numeric_name(a):
        return None
    d = str(date_s or "")[:10]
    if len(d) != 10 or d[4] != "-":
        return None
    return {"date": d, "home_team": h, "away_team": a, "match": f"{h} vs {a}",
            "league": league or competition or "Default", "competition": competition or league or "Default",
            "competition_type": ctype or "LEAGUE", "stage": stage or "", "group": group or "",
            "source": source, "source_detail": detail, "country": country or ""}

# ---------- Layer 1: football-data.org ----------
FD_MAP = {
    2021: ("PL", "Premier League", "LEAGUE", "England"),
    2014: ("PD", "La Liga", "LEAGUE", "Spain"),
    2019: ("SA", "Serie A", "LEAGUE", "Italy"),
    2002: ("BL1", "Bundesliga", "LEAGUE", "Germany"),
    2015: ("FL1", "Ligue 1", "LEAGUE", "France"),
    2003: ("DED", "Eredivisie", "LEAGUE", "Netherlands"),
    2017: ("PPL", "Primeira Liga", "LEAGUE", "Portugal"),
    2016: ("ELC", "Championship", "LEAGUE", "England"),
    2001: ("CL", "UEFA Champions League", "CUP", "Europe"),
    2013: ("BSA", "Campeonato Brasileiro Série A", "LEAGUE", "Brazil"),
    2000: ("WC", "FIFA World Cup", "NATIONAL", "World"),
    2018: ("EC", "European Championship", "NATIONAL", "Europe"),
    2146: ("EL", "UEFA Europa League", "CUP", "Europe"),
    2154: ("UCL", "UEFA Conference League", "CUP", "Europe"),
}
FREE_IDS = [2021, 2014, 2019, 2002, 2015, 2003, 2017, 2016, 2001, 2013, 2000, 2018]
TEST_IDS = [2146, 2154]  # tested one by one in V44, not bulk

def fetch_fd(token, days=90):
    out = []
    if len(token) != 32:
        print("Layer 1 SKIP: no valid 32-char token (set FOOTBALL_DATA_TOKEN or ~/token.txt)")
        return out, {"status": "no_token"}
    today = date.today()
    nxt = today + timedelta(days=days)
    report = {}
    for cid in FREE_IDS + TEST_IDS:
        code, comp_name, ctype, country = FD_MAP[cid]
        got = 0
        cur = today
        blocked = False
        while cur <= nxt:
            chunk_end = min(cur + timedelta(days=9), nxt)
            url = f"https://api.football-data.org/v4/matches?dateFrom={cur.isoformat()}&dateTo={chunk_end.isoformat()}&competitions={cid}"
            req = urllib.request.Request(url, headers={"X-Auth-Token": token})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    ms = json.loads(r.read().decode()).get("matches", [])
                for m in ms:
                    nm = norm_match(m.get("utcDate", "")[:10], m.get("homeTeam", {}).get("name", ""),
                                    m.get("awayTeam", {}).get("name", ""), code, comp_name, ctype,
                                    m.get("stage", ""), m.get("group", ""), "AUTO", f"football-data.org:{code}", country)
                    if nm:
                        out.append(nm)
                        got += 1
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    blocked = True
                    print(f"  FD {code} ({comp_name}): 403 - not on your free plan, skipped (no payment, no crash)")
                    break
                print(f"  FD {code}: HTTP {e.code}, skipped chunk")
            except Exception as e:
                print(f"  FD {code}: {e}, skipped chunk")
            cur = chunk_end + timedelta(days=1)
            time.sleep(1)
        report[code] = {"competition": comp_name, "got": got, "blocked_403": blocked}
        print(f"  FD {code} {comp_name}: {got} matches {'(403 blocked)' if blocked else ''}")
    return out, report

# ---------- Layer 2: OpenLigaDB (no key) ----------
def fetch_openliga():
    out = []
    # (shortcut, season, league label, competition, type)
    jobs = [
        ("nla", "2026", "UNL", "UEFA Nations League", "NATIONAL"),
        ("dfb", "2026", "DFB", "DFB-Pokal", "CUP"),
        ("bl2", "2026", "BL2", "2. Bundesliga", "LEAGUE"),
        ("bl1", "2026", "BL1", "Bundesliga", "LEAGUE"),
    ]
    for shortcut, season, league, comp, ctype in jobs:
        url = f"https://www.openligadb.de/api/getmatchdata/{shortcut}/{season}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Sigma-V44"})
            with urllib.request.urlopen(req, timeout=30) as r:
                arr = json.loads(r.read().decode())
            got = 0
            for m in arr:
                # OpenLigaDB: matchDateTime, team1.teamName, team2.teamName, group.groupName, leagueName
                h = (m.get("team1") or {}).get("teamName", "")
                a = (m.get("team2") or {}).get("teamName", "")
                grp = (m.get("group") or {}).get("groupName", "")
                nm = norm_match(str(m.get("matchDateTime", ""))[:10], h, a, league, comp, ctype,
                                grp, grp, "OPEN", f"openligadb:{shortcut}", "Europe" if league == "UNL" else "Germany")
                if nm:
                    out.append(nm)
                    got += 1
            print(f"  OpenLigaDB {shortcut} ({comp}): {got} matches")
        except Exception as e:
            print(f"  OpenLigaDB {shortcut} ({comp}): failed ({e}) - skipped, no crash")
    return out

# ---------- Layer 3: open files dropped in data/ ----------
def load_open_files():
    out = []
    # open-matchday CSV: user drops data/open_matchday.csv (any columns, we map by exact names)
    for cand in [DATA / "open_matchday.csv", DATA / "openfootball.csv"]:
        if not cand.exists():
            continue
        try:
            rows = list(csv.DictReader(open(cand, encoding="utf-8")))
            got = 0
            for r in rows:
                h = r.get("home_team") or r.get("home") or r.get("Home") or ""
                a = r.get("away_team") or r.get("away") or r.get("Away") or ""
                d = r.get("date") or r.get("Date") or ""
                league = r.get("league") or r.get("competition") or "OPEN"
                comp = r.get("competition") or league
                nm = norm_match(d, h, a, league, comp, r.get("competition_type") or "LEAGUE",
                                r.get("stage") or "", r.get("group") or "", "OPEN", f"file:{cand.name}")
                if nm:
                    out.append(nm)
                    got += 1
            print(f"  Open file {cand.name}: {got} matches")
        except Exception as e:
            print(f"  Open file {cand.name}: failed ({e})")
    return out

# ---------- Layer 4: MANUAL - any match in the world ----------
MANUAL_TEMPLATE = """date,home_team,away_team,league,competition,competition_type,stage,group,notes
2026-11-12,England,Croatia,UNL,UEFA Nations League,NATIONAL,Group Stage,Group C,Example - England vs Croatia
2026-11-15,Al Ahly,Zamalek,EGY,Egyptian Premier League,LEAGUE,,,Example - Egyptian League
2026-11-16,Al Hilal,Al Nassr,SAU,Saudi Pro League,LEAGUE,,,Example - Saudi League
"""

def ensure_manual_template():
    p = DATA / "sigma_manual_fixtures.csv"
    if not p.exists():
        p.write_text(MANUAL_TEMPLATE, encoding="utf-8")
        print(f"  Manual template created: data/sigma_manual_fixtures.csv (edit it, add ANY match)")
    return p

def load_manual():
    out = []
    p = ensure_manual_template()
    try:
        rows = list(csv.DictReader(open(p, encoding="utf-8")))
        for r in rows:
            # Skip example rows if user didn't edit? No - keep them, they are real fixtures user can delete.
            # Skip empty rows
            if not (r.get("home_team") or "").strip() or not (r.get("away_team") or "").strip():
                continue
            nm = norm_match(r.get("date"), r.get("home_team"), r.get("away_team"),
                            r.get("league") or "MANUAL", r.get("competition") or r.get("league") or "Manual",
                            (r.get("competition_type") or "LEAGUE").upper(),
                            r.get("stage") or "", r.get("group") or "", "MANUAL", "sigma_manual_fixtures.csv",
                            r.get("country") or "")
            if nm:
                out.append(nm)
        print(f"  Manual: {len(out)} matches from sigma_manual_fixtures.csv")
    except Exception as e:
        print(f"  Manual: failed ({e})")
    return out

def main():
    today = date.today()
    print("Sigma V44 Universal Fetch - FREE ONLY (no payment)")
    print(f"Today: {today}")
    token = get_token()
    all_rows, seen = [], set()
    stats = {}
    # Layer 1
    fd_rows, fd_report = fetch_fd(token, days=90)
    # Layer 2
    open_rows = fetch_openliga()
    # Layer 3
    file_rows = load_open_files()
    # Layer 4
    manual_rows = load_manual()
    # Merge with dedup: MANUAL wins over OPEN wins over AUTO (manual is user intent)
    # Order: AUTO first, then OPEN overwrites, then MANUAL overwrites
    merged = {}
    for r in fd_rows + open_rows + file_rows + manual_rows:
        key = (r["date"], r["home_team"].lower(), r["away_team"].lower())
        # If duplicate, keep MANUAL > OPEN > AUTO
        if key in merged:
            rank = {"AUTO": 0, "OPEN": 1, "MANUAL": 2}
            if rank.get(r["source"], 0) <= rank.get(merged[key]["source"], 0):
                continue
        merged[key] = r
    all_rows = sorted(merged.values(), key=lambda x: (x["date"], x["competition"], x["home_team"]))
    by_source = {}
    by_comp = {}
    for r in all_rows:
        by_source[r["source"]] = by_source.get(r["source"], 0) + 1
        by_comp[r["competition"]] = by_comp.get(r["competition"], 0) + 1
    payload = {"generated": str(today), "engine": "Sigma V44 Universal Fetch",
               "total": len(all_rows), "by_source": by_source, "by_competition": by_comp,
               "fd_report": fd_report, "matches": all_rows}
    (DATA / "sigma_universal_fixtures.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    # Also keep old file for V43 engine fallback: next_month format
    legacy = {"generated": str(today), "total_matches": len(all_rows),
              "matches": [{"match": r["match"], "date": r["date"], "league": r["league"],
                           "competition": r["competition"], "stage": r["stage"], "status": ""} for r in all_rows]}
    (DATA / "sigma_next_month.json").write_text(json.dumps(legacy, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: {len(all_rows)} unique fixtures -> data/sigma_universal_fixtures.json")
    print(f"By source: {by_source}")
    print(f"By competition: {by_comp}")
    print("Next: python3 sigma_v44_engine.py")
    print("To add ANY match: edit data/sigma_manual_fixtures.csv, then re-run this + engine.")

if __name__ == "__main__":
    main()
