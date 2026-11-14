#!/usr/bin/env python3
# Sigma Learn From Past - Continuous learning loop.
# Rule (Mahmoud Emad): "Any event that passes, analyze it and learn from it."
#  - Every PASSED event (date < today) with a VERIFIED real score is stored in
#    data/sigma_history.csv and learned from (Elo/xG/patterns via the engine).
#  - A passed event with NO verified score is NEVER invented: it goes to
#    data/sigma_passed_unverified.json/.csv (tracked, not learned, not scored).
#  - Predictions are NEVER learned as results. OLD_BACKTEST predictions are
#    backfilled (predicted==real for 23/39) so ONLY their real scores go to
#    history; their predictions are NOT counted as Sigma accuracy.
#  - TEMPLATE rows (sigma_year_2026.csv "TEMPLATE - Add ... here") are placeholders,
#    NOT matches: always skipped.
#  - Fake history (V54: Man Utd vs Villa 2-1 on 2026-10-01) is quarantined, never learned.
#  - Web results are added ONLY when explicitly verified by web search in this turn
#    (currently: England vs Croatia 2026-11-12 2-1). No auto-web-invention.
#  Idempotent: re-running adds nothing twice. Run before the engine every time.
import csv, json, shutil
from pathlib import Path
from datetime import date
from collections import defaultdict, Counter

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
TODAY = date.today()
TODAY_S = str(TODAY)

CANON = {"palace": "Crystal Palace", "crystal palace": "Crystal Palace",
 "man utd": "Man Utd", "manchester united": "Man Utd", "man united": "Man Utd",
 "villa": "Aston Villa", "aston villa": "Aston Villa",
 "brugge": "Club Brugge", "club brugge": "Club Brugge",
 "barca": "Barcelona", "barcelona": "Barcelona", "real": "Real Madrid", "real madrid": "Real Madrid",
 "atletico": "Atletico", "atletico madrid": "Atletico",
 "man city": "Man City", "manchester city": "Man City",
 "trabzon": "Trabzonspor", "trabzonspor": "Trabzonspor",
 "al ahly": "Al Ahly", "zamalek": "Zamalek", "al hilal": "Al Hilal", "al nassr": "Al Nassr"}

def canon_team(n):
    if not n: return ""
    s = str(n).strip()
    low = s.lower()
    if low.endswith(" fc"): low = low[:-3].strip()
    return CANON.get(low, s)

def is_numeric_name(s):
    try: float(str(s).strip()); return True
    except Exception: return False

def outcome(hg, ag):
    return "1" if hg > ag else ("X" if hg == ag else "2")

def parse_int(v):
    try:
        if v is None or str(v).strip() == "": return None
        return int(float(str(v).strip()))
    except Exception: return None

def split_match(m):
    if not m or " vs " not in str(m): return None, None
    h, a = str(m).split(" vs ", 1)
    return canon_team(h.strip()), canon_team(a.strip())

# ---------------- Verified results collection (real scores ONLY) ----------------
# Each entry: date, home, away, hg, ag, league, source, era, pred_h, pred_a, bet, bet_result, notes
verified = []
def add_verified(d, h, a, hg, ag, league, source, era, pred_h=None, pred_a=None, bet="", bet_result="", notes=""):
    if not d or not h or not a or hg is None or ag is None: return
    if is_numeric_name(h) or is_numeric_name(a): return
    d = str(d)[:10]
    verified.append({"date": d, "home": h, "away": a, "hg": hg, "ag": ag,
                     "league": league or "Default", "source": source, "era": era,
                     "pred_h": pred_h, "pred_a": pred_a, "bet": bet or "", "bet_result": bet_result or "", "notes": notes or ""})

# 1. VERIFIED14 - authoritative predictions + scores.
#    NOTE: data/sigma_real_verified.csv has NO date column (all rows are 2026-11-08),
#    while sigma_real_verified.csv at top level HAS dates. DATA predictions are
#    authoritative (they match unified evaluation 10/14 = 71.4%), so we use DATA
#    predictions + BASE dates (lookup by canon match).
date_by_match = {}
_base_ver = BASE / "sigma_real_verified.csv"
if _base_ver.exists():
    for _r in csv.DictReader(open(_base_ver, encoding="utf-8")):
        _h, _a = split_match(_r.get("match", ""))
        if _h and _a and _r.get("date"):
            date_by_match[(_h.lower(), _a.lower())] = str(_r.get("date", ""))[:10]
for cand in [DATA / "sigma_real_verified.csv", BASE / "sigma_real_verified.csv"]:
    if cand.exists():
        for r in csv.DictReader(open(cand, encoding="utf-8")):
            h, a = split_match(r.get("match", ""))
            d = (r.get("date", "") or "").strip()[:10]
            if not d:
                d = date_by_match.get((h.lower(), a.lower()), "")
            add_verified(d, h, a,
                         parse_int(r.get("real_home")), parse_int(r.get("real_away")),
                         r.get("league", "Default"), f"{cand.name}:verified14", "VERIFIED14",
                         parse_int(r.get("predicted_home")), parse_int(r.get("predicted_away")),
                         r.get("bet", ""), r.get("bet_result", ""), r.get("notes", ""))
        break

# 2. sigma_year_2026.csv - real scores only (predictions NOT used: they differ from verified14 for some rows).
#    TEMPLATE rows skipped. Pending (no real score) skipped - they are future, not passed results.
y26 = BASE / "sigma_year_2026.csv"
if y26.exists():
    for r in csv.DictReader(open(y26, encoding="utf-8")):
        m = (r.get("match") or "").strip()
        if m.upper().startswith("TEMPLATE"): continue
        rh, ra = parse_int(r.get("real_home")), parse_int(r.get("real_away"))
        if rh is None or ra is None: continue  # pending forecast, not a result
        h, a = split_match(m)
        add_verified(r.get("date", "")[:10], h, a, rh, ra,
                     r.get("league", "Default"), "sigma_year_2026.csv:real-score", "YEAR2026",
                     None, None, r.get("bet", ""), r.get("bet_result", ""), r.get("notes", ""))

# 3. sigma_old_new_fed.csv - real scores ONLY. Predictions NEVER evaluated (backfilled).
fed = BASE / "sigma_old_new_fed.csv"
if fed.exists():
    for r in csv.DictReader(open(fed, encoding="utf-8")):
        rh, ra = parse_int(r.get("real_home")), parse_int(r.get("real_away"))
        if rh is None or ra is None: continue
        h, a = split_match(r.get("match", ""))
        era = (r.get("era") or "OLD_BACKTEST").strip()
        add_verified(r.get("date", "")[:10], h, a, rh, ra,
                     r.get("league", "Default"), f"sigma_old_new_fed.csv:{era}", era,
                     None, None, r.get("bet", ""), r.get("bet_result", ""), r.get("notes", ""))

# 4. WEB-VERIFIED (explicit, verified by web search 2026-11-14 - NOT invented):
#    England 2-1 Croatia, 12 Nov 2026, Wembley, UEFA Nations League Group A3.
#    Sources: Sportradar "Winner: England, 2-1", Gulf News "2-1 victory", Sportsmole "2-1 win".
#    Scorers: Rogers 24', Sucic ~60', Kane pen 64'. England to QFs, 12 pts from 5.
add_verified("2026-11-12", "England", "Croatia", 2, 1, "UNL",
             "web: Sportradar + Gulf News + Sportsmole (verified 2026-11-14)", "WEB_VERIFIED",
             None, None, "", "", "Rogers 24, Sucic ~60, Kane pen 64 - England to Nations League QFs")

# 5. DAILY REPORT (sigma_daily_report.json) - results the user already confirmed in Termux.
#    These are PASSED events with real scores from the user's own V72 daily report.
#    They are learned even if their date == TODAY in the container (13 Nov), because
#    the user already saw them finish on 14 Nov. NEVER invent - only parse "actual".
#    Format: {"version":"V72","date":"2026-11-14","results_13_nov":[{"match":"Netherlands vs Greece","prediction":"1","actual":"7-0","result":"correct"},...]}
#    Prediction mapping for eval: "1"->1-0, "2"->0-1, "X"->1-1, "NO SAFE BET"/"ABSTAIN"->None (abstain, not a miss).
import re as _re
_MONTH = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12,
          "january":1,"february":2,"march":3,"april":4,"june":6,"july":7,"august":8,"september":9,"october":10,"november":11,"december":12}
for _cand in [DATA / "sigma_daily_report.json", BASE / "sigma_daily_report.json"]:
    if not _cand.exists():
        continue
    try:
        _rep = json.load(open(_cand, encoding="utf-8"))
    except Exception:
        continue
    _ver = str(_rep.get("version", "")).strip() or "V72"
    _era = f"DAILY_{_ver}"
    _rep_date = str(_rep.get("date", "") or "")[:10]
    _rep_year = _rep_date[:4] if len(_rep_date) >= 4 and _rep_date[:4].isdigit() else "2026"
    # Collect (date, items) from every results_* key + plain "results" key
    _daily_groups = []
    for _k, _v in _rep.items():
        if not isinstance(_v, list) or not _v:
            continue
        _d = ""
        if _k == "results":
            _d = ""  # per-item date or report-date-1
        elif _k.startswith("results_"):
            _rest = _k[len("results_"):]
            _m1 = _re.match(r"(\d{4})_(\d{1,2})_(\d{1,2})$", _rest)
            _m2 = _re.match(r"(\d{1,2})_([a-z]+)$", _rest, _re.I)
            if _m1:
                _d = f"{_m1.group(1)}-{int(_m1.group(2)):02d}-{int(_m1.group(3)):02d}"
            elif _m2 and _m2.group(2).lower() in _MONTH:
                _d = f"{_rep_year}-{_MONTH[_m2.group(2).lower()]:02d}-{int(_m2.group(1)):02d}"
            else:
                continue
        else:
            continue
        _daily_groups.append((_d, _v))
    for _d, _items in _daily_groups:
        for _it in _items:
            try:
                if not isinstance(_it, dict):
                    continue
                _h, _a = split_match(_it.get("match", ""))
                if not _h or not _a:
                    continue
                _actual = str(_it.get("actual", "") or "")
                _mm = _re.search(r"(\d+)\s*-\s*(\d+)", _actual)
                if not _mm:
                    continue
                _hg, _ag = int(_mm.group(1)), int(_mm.group(2))
                _dd = (str(_it.get("date", "") or "")[:10] or _d or _rep_date)
                _pred_raw = str(_it.get("prediction", "") or "").strip().upper()
                if _pred_raw in ("1", "HOME", "HOME WIN"):
                    _ph, _pa = 1, 0
                elif _pred_raw in ("2", "AWAY", "AWAY WIN"):
                    _ph, _pa = 0, 1
                elif _pred_raw in ("X", "DRAW"):
                    _ph, _pa = 1, 1
                else:
                    _ph, _pa = None, None  # NO SAFE BET / ABSTAIN / empty -> abstain, not a miss
                add_verified(_dd, _h, _a, _hg, _ag, "International",
                             f"sigma_daily_report.json:{_ver}", _era,
                             _ph, _pa, str(_it.get("prediction", "") or ""),
                             str(_it.get("result", "") or ""), f"Daily report {_ver} - actual {_actual}")
            except Exception:
                continue
    break  # use first daily report found (DATA wins)

# Dedup verified by (date, home.lower, away.lower) - keep first (VERIFIED14 wins, it was added first).
ver_by_key = {}
for v in verified:
    k = (v["date"], v["home"].lower(), v["away"].lower())
    if k not in ver_by_key:
        ver_by_key[k] = v
verified_unique = list(ver_by_key.values())

def main():
    print(f"Sigma Learn From Past - Today {TODAY_S}")
    print(f"Verified real-score rows collected: {len(verified)} -> unique {len(verified_unique)}")
    # ---------------- History: load, quarantine fake, merge verified ----------------
    hist_path = DATA / "sigma_history.csv"
    existing = []
    if hist_path.exists():
        for r in csv.DictReader(open(hist_path, encoding="utf-8")):
            try:
                if r.get("status") and r["status"] != "FINISHED": continue
                h = canon_team(r.get("home") or "")
                a = canon_team(r.get("away") or "")
                if not h or not a or is_numeric_name(h) or is_numeric_name(a): continue
                hg = parse_int(r.get("home_goals")); ag = parse_int(r.get("away_goals"))
                if hg is None or ag is None: continue
                existing.append({"date": str(r.get("date") or "")[:10], "home": h, "away": a,
                                 "hg": hg, "ag": ag, "league": r.get("league") or "Default",
                                 "source": r.get("source") or "existing"})
            except Exception: continue
    print(f"Existing history rows: {len(existing)}")
    quarantined = []
    conflicts = []
    hist_by_key = {}
    for row in existing:
        k = (row["date"], row["home"].lower(), row["away"].lower())
        # V54 fake: Man Utd vs Villa 2-1 on 2026-10-01 - quarantined, never learned.
        if k == ("2026-10-01", "man utd", "aston villa"):
            quarantined.append({**row, "reason": "V54 fake: History is 1 match duplicated 50x with wrong score/date. Real: Man Utd vs Aston Villa 4-4 on 8 Nov 2026 (in verified)."})
            continue
        hist_by_key[k] = {**row, "era": "EXISTING"}
    # Merge verified into history
    added = []
    for v in sorted(verified_unique, key=lambda x: x["date"]):
        k = (v["date"], v["home"].lower(), v["away"].lower())
        if k in hist_by_key:
            old = hist_by_key[k]
            # Re-runs: existing rows load as EXISTING - restore authoritative era/source from verified.
            if old["hg"] == v["hg"] and old["ag"] == v["ag"]:
                if old.get("era") == "EXISTING":
                    old["era"] = v["era"]; old["source"] = v["source"]
            if old["hg"] != v["hg"] or old["ag"] != v["ag"]:
                conflicts.append({"key": k, "history_score": f"{old['hg']}-{old['ag']}", "verified_score": f"{v['hg']}-{v['ag']}",
                                  "action": "Verified wins, old row quarantined"})
                quarantined.append({**old, "reason": f"Score conflict: history {old['hg']}-{old['ag']} vs verified {v['hg']}-{v['ag']} - verified wins."})
                hist_by_key[k] = {"date": v["date"], "home": v["home"], "away": v["away"], "hg": v["hg"], "ag": v["ag"],
                                  "league": v["league"], "source": v["source"], "era": v["era"]}
                added.append({"date": v["date"], "match": f"{v['home']} vs {v['away']}", "score": f"{v['hg']}-{v['ag']}",
                              "era": v["era"], "source": v["source"], "note": "corrected conflict"})
            continue
        hist_by_key[k] = {"date": v["date"], "home": v["home"], "away": v["away"], "hg": v["hg"], "ag": v["ag"],
                          "league": v["league"], "source": v["source"], "era": v["era"]}
        added.append({"date": v["date"], "match": f"{v['home']} vs {v['away']}", "score": f"{v['hg']}-{v['ag']}",
                      "era": v["era"], "source": v["source"], "note": ""})
    final_history = sorted(hist_by_key.values(), key=lambda x: (x["date"], x["home"].lower(), x["away"].lower()))
    # Backup + write history
    if hist_path.exists():
        shutil.copy(hist_path, DATA / f"sigma_history.before_learn_{TODAY_S}.csv")
    with open(hist_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "home", "away", "home_goals", "away_goals", "league", "status", "source"])
        w.writeheader()
        for r in final_history:
            w.writerow({"date": r["date"], "home": r["home"], "away": r["away"],
                        "home_goals": r["hg"], "away_goals": r["ag"], "league": r["league"],
                        "status": "FINISHED", "source": r.get("source", "verified")})
    print(f"History: {len(existing)} -> {len(final_history)} (added {len(added)}, quarantined {len(quarantined)}, conflicts {len(conflicts)})")
    for a in added:
        print(f"  + {a['date']} {a['match']} {a['score']} [{a['era']}] {a['source']}")
    for q in quarantined:
        print(f"  QUARANTINE: {q['date']} {q['home']} vs {q['away']} {q['hg']}-{q['ag']} - {q['reason']}")

    # ---------------- Passed fixtures: learned vs passed-without-verified ----------------
    fixtures = []
    # Manual
    man = DATA / "sigma_manual_fixtures.csv"
    if man.exists():
        for r in csv.DictReader(open(man, encoding="utf-8")):
            fixtures.append({"date": str(r.get("date") or "")[:10], "home": canon_team(r.get("home_team") or ""),
                             "away": canon_team(r.get("away_team") or ""), "league": r.get("league", ""),
                             "competition": r.get("competition", ""), "source": "sigma_manual_fixtures.csv"})
    # Universal
    uni = DATA / "sigma_universal_fixtures.json"
    if uni.exists():
        try:
            d = json.load(open(uni, encoding="utf-8"))
            for mm in (d.get("matches", []) if isinstance(d, dict) else d):
                fixtures.append({"date": str(mm.get("date") or "")[:10], "home": canon_team(mm.get("home_team") or mm.get("home") or ""),
                                 "away": canon_team(mm.get("away_team") or mm.get("away") or ""), "league": mm.get("league", ""),
                                 "competition": mm.get("competition", ""), "source": "sigma_universal_fixtures.json"})
        except Exception: pass
    # Next month
    nm = DATA / "sigma_next_month.json"
    if nm.exists():
        try:
            d = json.load(open(nm, encoding="utf-8"))
            for mm in (d.get("matches", []) if isinstance(d, dict) else []):
                h, a = split_match(mm.get("match", ""))
                fixtures.append({"date": str(mm.get("date") or "")[:10], "home": h or "", "away": a or "",
                                 "league": mm.get("league", ""), "competition": mm.get("competition", ""), "source": "sigma_next_month.json"})
        except Exception: pass
    # Year 2026 pending (no real score, not TEMPLATE) - future fixtures to watch
    if y26.exists():
        for r in csv.DictReader(open(y26, encoding="utf-8")):
            m = (r.get("match") or "").strip()
            if m.upper().startswith("TEMPLATE"): continue
            if parse_int(r.get("real_home")) is not None: continue
            h, a = split_match(m)
            fixtures.append({"date": str(r.get("date") or "")[:10], "home": h or "", "away": a or "",
                             "league": r.get("league", ""), "competition": "", "source": "sigma_year_2026.csv:pending"})
    # Dedup fixtures by (date, home, away)
    fix_by_key = {}
    for fx in fixtures:
        if not fx["date"] or not fx["home"] or not fx["away"]: continue
        fix_by_key[(fx["date"], fx["home"].lower(), fx["away"].lower())] = fx
    passed_learned = []
    passed_unverified = []
    future_fixtures = []
    for k, fx in sorted(fix_by_key.items()):
        d = fx["date"]
        if d < TODAY_S:
            if k in hist_by_key:
                hr = hist_by_key[k]
                passed_learned.append({**fx, "score": f"{hr['hg']}-{hr['ag']}", "status": "LEARNED", "where": "history"})
            else:
                passed_unverified.append({**fx, "status": "PASSED_WITHOUT_VERIFIED_RESULT",
                    "reason": f"Passed on {d} but no verified result in any source - NOT stored as score, NOT learned, NOT invented."})
        else:
            future_fixtures.append(fx)
    # Write passed_unverified
    pu_path = DATA / "sigma_passed_unverified.json"
    pu_data = {"generated": TODAY_S, "today": TODAY_S,
               "rule": "Passed events with no verified result are tracked here, NEVER invented.",
               "total": len(passed_unverified), "matches": passed_unverified,
               "learned_total": len(passed_learned), "learned": passed_learned}
    pu_path.write_text(json.dumps(pu_data, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(DATA / "sigma_passed_unverified.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "home", "away", "league", "competition", "source", "status", "reason"])
        w.writeheader()
        for r in passed_unverified:
            w.writerow({"date": r["date"], "home": r["home"], "away": r["away"], "league": r["league"],
                        "competition": r["competition"], "source": r["source"], "status": r["status"], "reason": r["reason"]})
    print(f"Passed fixtures: learned {len(passed_learned)}, without verified result {len(passed_unverified)}, future {len(future_fixtures)}")
    for r in passed_learned: print(f"  LEARNED: {r['date']} {r['home']} vs {r['away']} {r['score']}")
    for r in passed_unverified: print(f"  UNVERIFIED: {r['date']} {r['home']} vs {r['away']} - {r['reason']}")

    # ---------------- Pattern learning from final history ----------------
    def patterns(rows):
        n = len(rows)
        if n == 0: return {"n": 0}
        goals = [r["hg"] + r["ag"] for r in rows]
        home_w = sum(1 for r in rows if r["hg"] > r["ag"])
        draw = sum(1 for r in rows if r["hg"] == r["ag"])
        away_w = sum(1 for r in rows if r["hg"] < r["ag"])
        btts = sum(1 for r in rows if r["hg"] > 0 and r["ag"] > 0)
        over25 = sum(1 for r in rows if r["hg"] + r["ag"] >= 3)
        over15 = sum(1 for r in rows if r["hg"] + r["ag"] >= 2)
        return {"n": n, "avg_goals": round(sum(goals) / n, 2),
                "home_win_pct": round(home_w / n * 100, 1), "draw_pct": round(draw / n * 100, 1), "away_win_pct": round(away_w / n * 100, 1),
                "btts_pct": round(btts / n * 100, 1), "over15_pct": round(over15 / n * 100, 1), "over25_pct": round(over25 / n * 100, 1)}
    by_era = defaultdict(list)
    for r in final_history:
        by_era[r.get("era", "EXISTING")].append(r)
    era_patterns = {e: patterns(rs) for e, rs in sorted(by_era.items())}
    # VERIFIED14 + WEB + NEW_2026 are the "trusted" eras (not OLD_BACKTEST, whose predictions were backfilled)
    trusted = [r for r in final_history if r.get("era") in ("VERIFIED14", "YEAR2026", "WEB_VERIFIED", "NEW_2026") or str(r.get("era", "")).startswith("DAILY_")]
    # Per-team stats
    team = defaultdict(lambda: {"n": 0, "scored": 0, "conceded": 0, "home_n": 0, "home_scored": 0, "home_conceded": 0,
                                "away_n": 0, "away_scored": 0, "away_conceded": 0, "results": []})
    for r in sorted(final_history, key=lambda x: x["date"]):
        for side, tm, sc, co in (("home", r["home"], r["hg"], r["ag"]), ("away", r["away"], r["ag"], r["hg"])):
            t = team[tm]; t["n"] += 1; t["scored"] += sc; t["conceded"] += co
            if side == "home": t["home_n"] += 1; t["home_scored"] += sc; t["home_conceded"] += co
            else: t["away_n"] += 1; t["away_scored"] += sc; t["away_conceded"] += co
            t["results"].append("W" if sc > co else ("D" if sc == co else "L"))
    team_stats = {}
    for tm, t in sorted(team.items()):
        team_stats[tm] = {"n": t["n"], "scored_avg": round(t["scored"] / max(1, t["n"]), 2),
                          "conceded_avg": round(t["conceded"] / max(1, t["n"]), 2),
                          "home_scored_avg": round(t["home_scored"] / max(1, t["home_n"]), 2),
                          "away_scored_avg": round(t["away_scored"] / max(1, t["away_n"]), 2),
                          "home_conceded_avg": round(t["home_conceded"] / max(1, t["home_n"]), 2),
                          "away_conceded_avg": round(t["away_conceded"] / max(1, t["away_n"]), 2),
                          "form_last5": "".join(t["results"][-5:]),
                          "btts_note": "computed from history"}
    # ---------------- Prediction evaluation - VERIFIED14 ONLY ----------------
    pred_eval = []
    for v in sorted([x for x in verified_unique if x["era"] == "VERIFIED14"], key=lambda x: x["date"]):
        if v["pred_h"] is None or v["pred_a"] is None: continue
        pred_eval.append({"date": v["date"], "match": f"{v['home']} vs {v['away']}",
                          "predicted": f"{v['pred_h']}-{v['pred_a']}", "real": f"{v['hg']}-{v['ag']}",
                          "pred_outcome": outcome(v["pred_h"], v["pred_a"]), "real_outcome": outcome(v["hg"], v["ag"]),
                          "hit_1x2": outcome(v["pred_h"], v["pred_a"]) == outcome(v["hg"], v["ag"]),
                          "hit_exact": v["pred_h"] == v["hg"] and v["pred_a"] == v["ag"],
                          "bet": v["bet"], "bet_result": v["bet_result"], "notes": v["notes"]})
    # Daily report eval (DAILY_* only): predicted outcomes vs real, abstains counted separately (NOT misses).
    daily_eval_rows = []
    for v in sorted([x for x in verified_unique if str(x["era"]).startswith("DAILY_")], key=lambda x: x["date"]):
        if v["pred_h"] is None or v["pred_a"] is None:
            daily_eval_rows.append({"date": v["date"], "match": f"{v['home']} vs {v['away']}",
                                    "predicted": "ABSTAIN (NO SAFE BET)", "real": f"{v['hg']}-{v['ag']}",
                                    "result": "abstain-correct" if str(v["bet_result"]).lower().startswith("abstain") else "abstain"})
        else:
            daily_eval_rows.append({"date": v["date"], "match": f"{v['home']} vs {v['away']}",
                                    "predicted": f"{v['pred_h']}-{v['pred_a']} ({v['bet']})", "real": f"{v['hg']}-{v['ag']}",
                                    "hit_1x2": outcome(v["pred_h"], v["pred_a"]) == outcome(v["hg"], v["ag"]),
                                    "result": v["bet_result"]})
    daily_n_pred = sum(1 for r in daily_eval_rows if "hit_1x2" in r)
    daily_hit = sum(1 for r in daily_eval_rows if r.get("hit_1x2"))
    daily_n_abstain = sum(1 for r in daily_eval_rows if "hit_1x2" not in r)
    daily_eval = {"n_total": len(daily_eval_rows), "n_predicted": daily_n_pred, "hit_1x2": daily_hit,
                  "hit_1x2_pct": round(daily_hit / max(1, daily_n_pred) * 100, 1) if daily_n_pred else None,
                  "n_abstain": daily_n_abstain, "rows": daily_eval_rows}
    n_pred = len(pred_eval)
    hit_1x2 = sum(1 for r in pred_eval if r["hit_1x2"])
    hit_exact = sum(1 for r in pred_eval if r["hit_exact"])
    mae = round(sum(abs(int(r["predicted"].split("-")[0]) - int(r["real"].split("-")[0])) + abs(int(r["predicted"].split("-")[1]) - int(r["real"].split("-")[1])) for r in pred_eval) / max(1, n_pred), 2) if n_pred else None
    misses = [r for r in pred_eval if not r["hit_1x2"]]
    # DEFAULT template evaluation: old bulk predicted England vs Croatia as Away win (2), real Home win (1) -> DEFAULT miss.
    default_eval = {"match": "England vs Croatia", "date": "2026-11-12",
                    "old_default_prediction": "Away win (2), xG 1.45-1.97, probs 27.3/24.4/48.3",
                    "real": "England 2-1 Croatia (Home win)",
                    "hit": False,
                    "lesson": "DEFAULT template (1.45-1.97 for every team) fails on a real Nations League match. V44.1 refusal is correct: no history -> No confirmed data, not a template pick."}
    lessons = [
        "VERIFIED14 1X2 hit: {}/{} = {}% - use this, NOT OLD_BACKTEST 91.7% (backfilled predictions).".format(hit_1x2, n_pred, round(hit_1x2 / max(1, n_pred) * 100, 1)),
        "DAILY_V72 (13 Nov): {}/{} predicted correct + {} abstain-correct (Morocco NO SAFE BET, real 5-1). Abstain is a win, not a miss.".format(daily_hit, daily_n_pred, daily_n_abstain),
        "Upset lesson (Sunderland 1-0 Chelsea): weak-home upset - do not auto-pick favourite away.",
        "BTTS lesson (Brentford 0 away goals, Como 0 away goals): BTTS fails when away team blanks - check away scoring, not just averages.",
        "Draw lesson (Brugge 1-1 Anderlecht, Napoli 1-1 Lazio): draws are real - 1X2 must carry draw probability, not force a winner.",
        "Late-goal lesson (Man Utd 4-4 Villa: goals 90+2, 90+6; Benfica Pavlidis 90+4): late goals change Over/BTTS - do not settle early.",
        "DEFAULT lesson: template 1.45-1.97 predicted England-Croatia as Away win, real was Home win. Template = wrong. Refuse, don't invent.",
        "OLD_BACKTEST lesson: 24 old real scores are useful for HISTORY (Elo/xG/patterns) but their predictions were backfilled - never count them as Sigma accuracy.",
    ]
    # ---------------- What did learning unlock for FUTURE fixtures? ----------------
    team_n = {tm: st["n"] for tm, st in team_stats.items()}
    unlocked = []
    for fx in sorted(future_fixtures, key=lambda x: (x["date"], x["home"])):
        hn = team_n.get(fx["home"], 0); an = team_n.get(fx["away"], 0)
        unlocked.append({"date": fx["date"], "match": f"{fx['home']} vs {fx['away']}", "league": fx["league"],
                         "n_home": hn, "n_away": an,
                         "status_after_learning": "REAL (both n>=5)" if (hn >= 5 and an >= 5) else "No confirmed data (need >=5 each)",
                         "source": fx["source"]})
    # ---------------- Quarantine (corrected) ----------------
    quarantine_out = {"generated": TODAY_S, "source": "sigma_v54_real_complete.json quarantine, corrected by learner",
        "note": "England vs Croatia was listed as FAKE in V54 but web-verified 2-1 on 2026-11-12 (Sportradar/Gulf News/Sportsmole). It is CORRECTED: moved from fake to history. The other 6 manual fixtures stay quarantined (fake dates, future, no verified result).",
        "manual_fakes_remaining": 6, "manual_corrected": 1,
        "count_v54": 59, "count_total": 59,
        "breakdown": {"manual_fakes_remaining": 6, "manual_corrected_to_history": 1, "history_duplicate_rows": 49, "future_unverified": 3},
        "manual": [], "history": {"file": "data/sigma_history.csv", "total_rows_before": len(existing), "duplicate_rows": 49,
                                 "fake_row": "Man Utd vs Villa 2-1 on 2026-10-01 (quarantined, never learned)",
                                 "real_correction": "Man Utd vs Aston Villa 4-4 on 8 Nov 2026 - in history via verified14"},
        "future_unverified": [{"match": "Man Utd vs Villa", "date": "2026-11-22", "reason": "FAKE: Real Man Utd vs Villa was 8 Nov 2026 4-4, not 22 Nov"},
                              {"match": "Real vs Barca", "date": "2026-11-23", "reason": "FAKE: Real Clasico 25 Oct 2026, not 23 Nov"},
                              {"match": "Bayern vs Dortmund", "date": "2026-11-24", "reason": "UNVERIFIED: No verified source in workspace"}],
        "quarantined_history_rows": quarantined, "conflicts": conflicts}
    try:
        rc = json.load(open(BASE / "sigma_v54_real_complete.json", encoding="utf-8"))
        for r in (rc.get("quarantine", {}) or {}).get("manual", []) or []:
            if str(r.get("match", "")).strip().lower() == "england vs croatia" and str(r.get("date", ""))[:10] == "2026-11-12":
                quarantine_out["manual"].append({**r, "current_location": "history (CORRECTED - web-verified 2-1)", "as_prediction": False, "corrected": True})
            else:
                quarantine_out["manual"].append({**r, "current_location": "no-data (not a prediction)", "as_prediction": False, "corrected": False})
    except Exception as e:
        quarantine_out["manual_error"] = str(e)
    (DATA / "sigma_quarantine_fake_v54.json").write_text(json.dumps(quarantine_out, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "sigma_v54_quarantine_updated.json").write_text(json.dumps(quarantine_out, ensure_ascii=False, indent=2), encoding="utf-8")

    # Preserve original history_before across idempotent re-runs (first run 1 -> 41, re-runs 41 -> 41).
    _orig_before = len(existing)
    _prev_added_total = 0
    _prev_rep = DATA / "sigma_learning_report.json"
    if _prev_rep.exists():
        try:
            _pr = json.load(open(_prev_rep, encoding="utf-8"))
            if isinstance(_pr.get("history_before_original"), int):
                _orig_before = min(_orig_before, _pr["history_before_original"])
            elif isinstance(_pr.get("history_before"), int):
                _orig_before = min(_orig_before, _pr["history_before"])
            if isinstance(_pr.get("added_total"), int):
                _prev_added_total = _pr["added_total"]
        except Exception: pass
    report = {"generated": TODAY_S, "today": TODAY_S, "rule": "Any event that passes is analyzed and learned from. No invented scores.",
        "history_before": len(existing), "history_before_this_run": len(existing),
        "history_before_original": _orig_before, "history_after": len(final_history),
        "added_this_run": added, "added_this_run_count": len(added),
        "added": added, "added_count": len(added),
        "added_total": _prev_added_total + len(added),
        "quarantined": quarantined, "quarantined_count": len(quarantined),
        "conflicts": conflicts,
        "passed_learned": passed_learned, "passed_learned_count": len(passed_learned),
        "passed_unverified": passed_unverified, "passed_unverified_count": len(passed_unverified),
        "future_fixtures_count": len(future_fixtures),
        "patterns_all": patterns(final_history),
        "patterns_by_era": era_patterns,
        "patterns_trusted": patterns(trusted),
        "team_stats": team_stats,
        "daily_eval": daily_eval,
        "prediction_eval": {"source": "VERIFIED14 predictions from data/sigma_real_verified.csv ONLY (OLD_BACKTEST predictions excluded - backfilled)",
                            "n": n_pred, "hit_1x2": hit_1x2, "hit_1x2_pct": round(hit_1x2 / max(1, n_pred) * 100, 1),
                            "hit_exact": hit_exact, "hit_exact_pct": round(hit_exact / max(1, n_pred) * 100, 1),
                            "mae_goals_per_match": mae, "details": pred_eval, "misses": misses},
        "default_template_eval": default_eval,
        "lessons": lessons,
        "unlocked_future": unlocked,
        "skipped": {"part1_part2_csv": "Arabic market price data (not football) - reviewed, NOT mixed into football history.",
                    "template_rows": "sigma_year_2026.csv TEMPLATE rows are placeholders - skipped, not matches.",
                    "bulk_predictions": "Bulk files contain PREDICTIONS, not results - evaluated (England-Croatia DEFAULT miss) but never learned as results."}}
    (DATA / "sigma_learning_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nLEARNING REPORT: data/sigma_learning_report.json")
    print(f"  Patterns ALL (n={report['patterns_all']['n']}): avg_goals {report['patterns_all']['avg_goals']}, Home {report['patterns_all']['home_win_pct']}% Draw {report['patterns_all']['draw_pct']}% Away {report['patterns_all']['away_win_pct']}%, BTTS {report['patterns_all']['btts_pct']}%, Over25 {report['patterns_all']['over25_pct']}%")
    print(f"  Trusted patterns (VERIFIED14+YEAR2026+WEB+NEW_2026, n={report['patterns_trusted']['n']}): {report['patterns_trusted']}")
    print(f"  VERIFIED14 predictions: 1X2 {hit_1x2}/{n_pred} = {report['prediction_eval']['hit_1x2_pct']}%, Exact {hit_exact}/{n_pred}, MAE {mae}")
    print(f"  Unlocked future fixtures:")
    for u in unlocked: print(f"    {u['date']} {u['match']} - home n={u['n_home']} away n={u['n_away']} -> {u['status_after_learning']}")
    print(f"  Quarantine written: data/sigma_quarantine_fake_v54.json (59 = 6 fakes + 1 corrected + 49 dup + 3 future unverified)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
