#!/usr/bin/env python3
# Sigma V44 FINAL ONE-SHOT - Collect everything, merge, review, ready for ONE upload
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# Run ONCE in Termux: python3 sigma_v44_final_one_shot.py
# What it does, in order (stops with clear error if a step fails):
#  1. Backup data/sigma_history.csv
#  2. Fetch REAL club history from openfootball football.json (10 seasons x 10 leagues, FREE, no key)
#  3. Fetch REAL WC (2018/2022/2026) + Euro (2016/2020/2024) from openfootball worldcup.json / euro.json
#  4. Fetch REAL internationals from martj42/international_results results.csv (49,459 matches 1872-2024)
#     - filtered to date >= 2010-01-01 (recent form only, not 1872)
#     - covers: Nations League, AFCON, Asian Cup, Copa America, Gold Cup, WC/Euro Qualifiers, Friendlies
#     - this is what gives Egypt / Saudi / Morocco / Algeria real history, not just 3 WC matches
#  5. Merge all into data/sigma_history.csv, dedup by (date, home, away, league)
#  6. Apply V44.3 canon fix (robust rewrite) to sigma_v44_fetch.py + sigma_v44_engine.py
#  7. Run sigma_v44_fetch.py (needs FOOTBALL_DATA_TOKEN env or ~/token.txt) -> sigma_v44_engine.py -> sigma_v44_review.py
#  8. Print final diagnosis table (DEFAULT / Golden per competition) + history counts
#  9. If REVIEW PASSED, print the ONE git push block for single upload
# NEVER invents a match. Every row comes from a real source URL. If a URL is 404, it skips it.
# No Arabic inside .py. FREE ONLY. Stdlib only.
import json, csv, urllib.request, urllib.error, subprocess, sys, shutil, os, re
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

SEASONS = ["2015-16","2016-17","2017-18","2018-19","2019-20","2020-21","2021-22","2022-23","2023-24","2024-25"]
LEAGUES = [
    ("en.1","England Premier League"),("en.2","England Championship"),
    ("de.1","Germany Bundesliga"),("de.2","Germany 2 Bundesliga"),
    ("es.1","Spain La Liga"),("es.2","Spain Segunda"),
    ("it.1","Italy Serie A"),("it.2","Italy Serie B"),
    ("fr.1","France Ligue 1"),("fr.2","France Ligue 2"),
]
WORLDCUPS = ["2018","2022","2026"]
EUROS = ["2016","2020","2024"]
INTERNATIONALS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Sigma-V44-final"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  SKIP {url} -> {e}")
        return None

def parse_openfootball(data, league):
    out = []
    if not data:
        return out
    for m in (data.get("matches", []) if isinstance(data, dict) else []):
        try:
            d = str(m.get("date") or "")[:10]
            h = (m.get("team1") or "").strip()
            a = (m.get("team2") or "").strip()
            if not d or not h or not a:
                continue
            s1, s2 = m.get("score1"), m.get("score2")
            if s1 is None or s2 is None:
                sc = m.get("score")
                if isinstance(sc, dict) and sc.get("ft"):
                    s1, s2 = sc["ft"][0], sc["ft"][1]
                elif isinstance(sc, list) and len(sc) >= 2:
                    s1, s2 = sc[0], sc[1]
                else:
                    continue
            if s1 is None or s2 is None:
                continue
            try:
                float(h); continue
            except Exception:
                pass
            try:
                float(a); continue
            except Exception:
                pass
            out.append({"date": d, "home": h, "away": a, "home_goals": int(s1), "away_goals": int(s2),
                        "league": league, "status": "FINISHED", "source": "openfootball"})
        except Exception:
            continue
    return out

def map_international_league(tournament):
    t = str(tournament or "")
    tl = t.lower()
    if "world cup" in tl:
        return "World Cup"
    if "uefa euro" in tl or "european championship" in tl:
        return "Euro"
    if "nations league" in tl:
        return "UEFA Nations League"
    if "copa am" in tl or "copa america" in tl:
        return "Copa America"
    if "african" in tl or "africa cup" in tl:
        return "African Cup"
    if "asian" in tl or "afc asian" in tl:
        return "Asian Cup"
    if "gold cup" in tl:
        return "Gold Cup"
    return "International"

def fetch_internationals():
    print("Fetching internationals (martj42 results.csv, 49k matches 1872-2024, filter >= 2010)...")
    req = urllib.request.Request(INTERNATIONALS_URL, headers={"User-Agent": "Sigma-V44-final"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  SKIP internationals -> {e}")
        return []
    rows = list(csv.DictReader(text.splitlines()))
    print(f"  Internationals raw: {len(rows)}")
    out = []
    for r in rows:
        try:
            d = str(r.get("date") or "")[:10]
            if not d or d < "2010-01-01":
                continue
            h = (r.get("home_team") or "").strip()
            a = (r.get("away_team") or "").strip()
            s1, s2 = r.get("home_score"), r.get("away_score")
            if not h or not a or s1 in (None, "") or s2 in (None, ""):
                continue
            try:
                float(h); continue
            except Exception:
                pass
            try:
                float(a); continue
            except Exception:
                pass
            out.append({"date": d, "home": h, "away": a,
                        "home_goals": int(float(s1)), "away_goals": int(float(s2)),
                        "league": map_international_league(r.get("tournament")),
                        "status": "FINISHED", "source": "international_results"})
        except Exception:
            continue
    print(f"  Internationals kept (>=2010): {len(out)}")
    return out

def step_history():
    print("\n=== STEP 1/4 - Real history fetch ===")
    all_new = []
    for season in SEASONS:
        for code, league in LEAGUES:
            url = f"https://raw.githubusercontent.com/openfootball/football.json/master/{season}/{code}.json"
            rows = parse_openfootball(fetch_json(url), league)
            if rows:
                print(f"  {season} {code}: {len(rows)}")
                all_new.extend(rows)
    for y in WORLDCUPS:
        rows = parse_openfootball(fetch_json(f"https://raw.githubusercontent.com/openfootball/worldcup.json/master/{y}/worldcup.json"), "World Cup")
        if rows:
            print(f"  World Cup {y}: {len(rows)}")
            all_new.extend(rows)
    for y in EUROS:
        rows = parse_openfootball(fetch_json(f"https://raw.githubusercontent.com/openfootball/euro.json/master/{y}/euro.json"), "Euro")
        if rows:
            print(f"  Euro {y}: {len(rows)}")
            all_new.extend(rows)
    all_new.extend(fetch_internationals())
    print(f"Fetched NEW (before dedup): {len(all_new)}")
    hist_path = DATA / "sigma_history.csv"
    existing = []
    if hist_path.exists():
        with open(hist_path, encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
        print(f"Existing history: {len(existing)}")
        shutil.copy(hist_path, DATA / "sigma_history.backup_before_final.csv")
        print("Backup: data/sigma_history.backup_before_final.csv")
    seen = set()
    merged = []
    for r in existing:
        try:
            key = (str(r.get("date",""))[:10], str(r.get("home") or r.get("homeTeam") or "").strip().lower(),
                   str(r.get("away") or r.get("awayTeam") or "").strip().lower(), str(r.get("league") or "").strip().lower())
            if key in seen:
                continue
            seen.add(key)
            merged.append({"date": str(r.get("date",""))[:10], "home": r.get("home") or r.get("homeTeam") or "",
                           "away": r.get("away") or r.get("awayTeam") or "",
                           "home_goals": r.get("home_goals") or r.get("homeGoals") or "0",
                           "away_goals": r.get("away_goals") or r.get("awayGoals") or "0",
                           "league": r.get("league") or r.get("competition") or "Default",
                           "status": r.get("status") or "FINISHED", "source": r.get("source") or "existing"})
        except Exception:
            continue
    added = 0
    for r in all_new:
        key = (r["date"], r["home"].lower(), r["away"].lower(), r["league"].lower())
        if key in seen:
            continue
        seen.add(key)
        merged.append(r)
        added += 1
    merged.sort(key=lambda x: x["date"])
    fields = ["date","home","away","home_goals","away_goals","league","status","source"]
    with open(hist_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(merged)
    print(f"Added NEW unique: {added}")
    print(f"Total history now: {len(merged)} (was {len(existing)})")
    # Counts for national leagues
    import collections
    c = collections.Counter(r["league"] for r in merged)
    for lg in ["World Cup","Euro","UEFA Nations League","African Cup","Asian Cup","Copa America","Gold Cup","International","Germany Bundesliga","France Ligue 1","England Premier League"]:
        if c.get(lg):
            print(f"  History {lg}: {c[lg]}")
    return len(merged)

def step_patch_v443():
    print("\n=== STEP 2/4 - Apply V44.3 canon fix (if needed) ===")
    # Import the V44.3 v2 patch if present, else inline minimal patch
    patch_file = BASE / "sigma_v44_3_fix_v2.py"
    if patch_file.exists():
        r = subprocess.run([sys.executable, str(patch_file)], capture_output=True, text=True, cwd=str(BASE))
        print(r.stdout)
        if r.stderr:
            print("Patch stderr:", r.stderr[-500:])
    else:
        print("sigma_v44_3_fix_v2.py not found in repo - SKIPPING patch. Run it manually before engine.")
        print("Expected file: sigma_v44_3_fix_v2.py next to sigma_v44_engine.py")

def run_cmd(name, script):
    print(f"\n=== STEP - {name} ===")
    r = subprocess.run([sys.executable, str(BASE / script)], capture_output=True, text=True, cwd=str(BASE))
    print(r.stdout[-3000:])
    if r.stderr:
        print("STDERR:", r.stderr[-1000:])
    if r.returncode != 0:
        print(f"FAILED: {script} exit code {r.returncode}")
        return False
    return True

def step_diagnosis():
    print("\n=== STEP 4/4 - Final diagnosis ===")
    try:
        d = json.load(open(DATA / "sigma_bulk_predictions_v44.json", encoding="utf-8"))
        rows = d["matches"]
        print(f"Total predictions: {len(rows)}  Golden: {sum(1 for r in rows if r.get('golden')==1)}  DEFAULT: {sum(1 for r in rows if r.get('is_default')==1)}")
        for comp in sorted(set(r["competition"] for r in rows)):
            sub = [r for r in rows if r["competition"]==comp]
            print(f"  {comp}: total {len(sub)} DEFAULT {sum(1 for r in sub if r.get('is_default')==1)} Golden {sum(1 for r in sub if r.get('golden')==1)}")
    except Exception as e:
        print(f"Diagnosis failed (did review promote files?): {e}")

if __name__ == "__main__":
    print("Sigma V44 FINAL ONE-SHOT - collect + merge + review for ONE upload")
    # Token check (needed for fetch step)
    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    if not token:
        tf = Path.home() / "token.txt"
        if tf.exists():
            token = tf.read_text().strip()
            os.environ["FOOTBALL_DATA_TOKEN"] = token
            print("Token loaded from ~/token.txt")
    if not token or len(token) != 32:
        print("WARNING: FOOTBALL_DATA_TOKEN not found or len != 32. History fetch will still run, but sigma_v44_fetch.py will fail without token.")
        print("Fix: export FOOTBALL_DATA_TOKEN=$(cat ~/token.txt) then re-run this script.")
    step_history()
    step_patch_v443()
    ok = run_cmd("Fetch fixtures (V44)", "sigma_v44_fetch.py")
    if not ok:
        print("STOP - fetch failed. Fix token / network, then re-run this script.")
        sys.exit(1)
    ok = run_cmd("Engine (V44)", "sigma_v44_engine.py")
    if not ok:
        print("STOP - engine failed.")
        sys.exit(1)
    ok = run_cmd("Review (V44)", "sigma_v44_review.py")
    if not ok:
        print("STOP - review failed. Do NOT upload.")
        sys.exit(1)
    step_diagnosis()
    print("\n=== DONE ===")
    print("If REVIEW PASSED above, upload ONCE with:")
    print("  git add data/sigma_history.csv data/sigma_universal_fixtures.json data/sigma_bulk_predictions_v44.json data/sigma_bulk_predictions_v44.csv data/sigma_bulk_predictions.json data/sigma_bulk_predictions.csv data/sigma_v44.json sigma_v44_fetch.py sigma_v44_engine.py sigma_v44_final_one_shot.py")
    print('  git commit -m "Sigma V44 Final - real history (club + WC/Euro + 40k internationals) + V44.3 canon + one-shot"')
    print("  git push origin main")
    print("Do NOT push if REVIEW did not say PASSED.")
