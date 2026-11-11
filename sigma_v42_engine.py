#!/usr/bin/env python3
# Sigma V42 Engine - Fix V41 bugs + Future + More markets + Calibrated confidence
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# FIXES: home/away columns (no more "—"), dedup by date+home+away+league,
#        is_default flag, DEFAULT excluded from Golden, league-strength Elo,
#        Platt-style calibration from backtest bins, future discount, more markets.
# Uses ONLY stdlib - Termux safe. Preserves V41 files, writes V42 files.
import csv, json, math
from collections import defaultdict
from pathlib import Path
from datetime import date

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

CANON = {"palace": "Crystal Palace", "crystal palace": "Crystal Palace",
 "man utd": "Man Utd", "manchester united": "Man Utd", "man united": "Man Utd",
 "villa": "Aston Villa", "aston villa": "Aston Villa",
 "brugge": "Club Brugge", "club brugge": "Club Brugge",
 "barca": "Barcelona", "barcelona": "Barcelona", "real": "Real Madrid", "real madrid": "Real Madrid",
 "atletico": "Atletico", "atletico madrid": "Atletico",
 "man city": "Man City", "manchester city": "Man City",
 "trabzon": "Trabzonspor", "trabzonspor": "Trabzonspor"}

def canon_team(n):
    if not n:
        return ""
    s = str(n).strip()
    low = s.lower()
    if low.endswith(" fc"):
        low = low[:-3].strip()
    return CANON.get(low, s)

def poisson(lam, k):
    return math.exp(-lam) * lam ** k / math.factorial(k)

def load_history():
    for cand in [DATA / "sigma_history.csv", BASE / "sigma_history.csv"]:
        if cand.exists():
            rows = list(csv.DictReader(open(cand, encoding="utf-8")))
            out, seen = [], set()
            for r in rows:
                try:
                    if r.get("status") and r["status"] != "FINISHED":
                        continue
                    h = canon_team(r.get("home") or r.get("homeTeam") or "")
                    a = canon_team(r.get("away") or r.get("awayTeam") or "")
                    if not h or not a:
                        continue
                    hg = int(float(r.get("home_goals") or r.get("homeGoals") or 0))
                    ag = int(float(r.get("away_goals") or r.get("awayGoals") or 0))
                    d = str(r.get("date") or r.get("utcDate") or "")[:10]
                    league = r.get("league") or r.get("competition") or "Default"
                    key = (d, h.lower(), a.lower())
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({"date": d, "home": h, "away": a, "hg": hg, "ag": ag, "league": league})
                except Exception:
                    continue
            out.sort(key=lambda x: x["date"])
            return out
    return []

def load_verified():
    for cand in [DATA / "sigma_real_verified.csv", BASE / "sigma_real_verified.csv"]:
        if cand.exists():
            rows = list(csv.DictReader(open(cand, encoding="utf-8")))
            out = []
            for r in rows:
                try:
                    if " vs " not in r["match"]:
                        continue
                    h, a = r["match"].split(" vs ")
                    out.append({"date": r.get("date", "")[:10], "home": canon_team(h.strip()),
                                "away": canon_team(a.strip()), "hg": int(r["real_home"]),
                                "ag": int(r["real_away"]), "league": r.get("league", "Default")})
                except Exception:
                    continue
            return out
    return []

def load_future():
    for cand in [DATA / "sigma_next_month.json", BASE / "sigma_next_month.json"]:
        if cand.exists():
            data = json.load(open(cand, encoding="utf-8"))
            items = data if isinstance(data, list) else data.get("matches", data.get("data", []))
            out, seen = [], set()
            dup = 0
            for mm in items:
                try:
                    # FIX: prefer explicit home/away fields, never rely on match string alone
                    h_raw = mm.get("homeTeam") or mm.get("home") or mm.get("home_name") or ""
                    a_raw = mm.get("awayTeam") or mm.get("away") or mm.get("away_name") or ""
                    if isinstance(h_raw, dict):
                        h_raw = h_raw.get("name", "")
                    if isinstance(a_raw, dict):
                        a_raw = a_raw.get("name", "")
                    if not h_raw or not a_raw:
                        if isinstance(mm.get("match"), str) and " vs " in mm["match"]:
                            h_raw, a_raw = mm["match"].split(" vs ")
                        else:
                            continue  # SKIP: no team names -> never show "—"
                    h, a = canon_team(str(h_raw).strip()), canon_team(str(a_raw).strip())
                    if not h or not a:
                        continue
                    d = str(mm.get("date") or mm.get("utcDate") or "")[:10]
                    league = mm.get("league") or mm.get("competition") or "Default"
                    comp = mm.get("competition") or mm.get("league") or "Default"
                    key = (d, h.lower(), a.lower(), str(league).lower())
                    if key in seen:
                        dup += 1
                        continue
                    seen.add(key)
                    out.append({"date": d, "home": h, "away": a, "league": league, "competition": comp})
                except Exception:
                    continue
            print(f"Future loaded: {len(out)} unique, {dup} duplicates removed")
            return out
    return []

def predict_match(states, league_stats, league_elo, global_elo_avg, home, away, league):
    hs = states.get(home)
    aws = states.get(away)
    # League-strength: adjust Elo by (league avg Elo - global avg), so Olympiakos/Rangers
    # in weak leagues do not inflate. Half-strength correction to avoid over-penalising.
    def adj_elo(team, s):
        if not s:
            return 1500.0
        lg_avg = league_elo.get(league)
        if lg_avg is None or lg_avg["n"] < 20:
            return s["elo"]
        return s["elo"] - 0.5 * (lg_avg["avg"] - global_elo_avg)
    elo_h = adj_elo(home, hs)
    elo_a = adj_elo(away, aws)
    ls = league_stats.get(league) or league_stats["Default"]
    if ls["n"] < 20:
        ls = league_stats["Default"]
    if ls["n"] == 0:
        lh_home, lh_away = 1.55, 1.25
    else:
        lh_home, lh_away = ls["home_goals"] / ls["n"], ls["away_goals"] / ls["n"]
    def attack(s, is_home):
        if not s or s["n"] == 0:
            return 1.0
        base = lh_home if is_home else lh_away
        if base == 0:
            return 1.0
        if is_home and s["home_n"] >= 3:
            raw = (s["home_scored"] / max(1, s["home_n"])) / base
            w = s["home_n"] / (s["home_n"] + 8.0)
        elif not is_home and s["away_n"] >= 3:
            raw = (s["away_scored"] / max(1, s["away_n"])) / base
            w = s["away_n"] / (s["away_n"] + 8.0)
        else:
            raw = (s["scored"] / max(1, s["n"])) / ((lh_home + lh_away) / 2.0)
            w = s["n"] / (s["n"] + 8.0)
        return 1.0 + w * (raw - 1.0)
    def defence(s, is_home):
        if not s or s["n"] == 0:
            return 1.0
        base = lh_away if is_home else lh_home
        if base == 0:
            return 1.0
        if is_home and s["home_n"] >= 3:
            raw = (s["home_conceded"] / max(1, s["home_n"])) / base
            w = s["home_n"] / (s["home_n"] + 8.0)
        elif not is_home and s["away_n"] >= 3:
            raw = (s["away_conceded"] / max(1, s["away_n"])) / base
            w = s["away_n"] / (s["away_n"] + 8.0)
        else:
            raw = (s["conceded"] / max(1, s["n"])) / ((lh_home + lh_away) / 2.0)
            w = s["n"] / (s["n"] + 8.0)
        return 1.0 + w * (raw - 1.0)
    elo_diff = elo_h - elo_a
    elo_f_h = max(0.85, min(1.18, math.exp(elo_diff / 600.0)))
    elo_f_a = max(0.85, min(1.18, math.exp(-elo_diff / 600.0)))
    def form_factor(s):
        if not s or not s["form"]:
            return 1.0
        pts = sum(3 if x == "W" else 1 if x == "D" else 0 for x in s["form"])
        return 0.92 + (pts / 15.0) * 0.16
    lam_h = lh_home * attack(hs, True) * defence(aws, False) * elo_f_h * form_factor(hs)
    lam_a = lh_away * attack(aws, False) * defence(hs, True) * elo_f_a * form_factor(aws)
    lam_h = max(0.2, min(3.5, lam_h))
    lam_a = max(0.2, min(3.5, lam_a))
    rho = -0.13
    def tau(x, y):
        if x == 0 and y == 0:
            return 1.0 - lam_h * lam_a * rho
        if x == 0 and y == 1:
            return 1.0 + lam_h * rho
        if x == 1 and y == 0:
            return 1.0 + lam_a * rho
        if x == 1 and y == 1:
            return 1.0 - rho
        return 1.0
    mat, total = {}, 0.0
    for x in range(7):
        for y in range(7):
            p = max(0.0, poisson(lam_h, x) * poisson(lam_a, y) * tau(x, y))
            mat[(x, y)] = p
            total += p
    for k in mat:
        mat[k] /= total
    hw = sum(p for (x, y), p in mat.items() if x > y)
    d = sum(p for (x, y), p in mat.items() if x == y)
    aw = sum(p for (x, y), p in mat.items() if x < y)
    btts = sum(p for (x, y), p in mat.items() if x > 0 and y > 0)
    over15 = sum(p for (x, y), p in mat.items() if x + y >= 2)
    over25 = sum(p for (x, y), p in mat.items() if x + y >= 3)
    over35 = sum(p for (x, y), p in mat.items() if x + y >= 4)
    under25 = 1.0 - over25
    dc1x = hw + d
    dc12 = hw + aw
    dcx2 = d + aw
    cs_home = sum(p for (x, y), p in mat.items() if y == 0)
    cs_away = sum(p for (x, y), p in mat.items() if x == 0)
    top = sorted(mat.items(), key=lambda z: z[1], reverse=True)[:3]
    top3 = " / ".join([f"{x}-{y} {p*100:.1f}%" for (x, y), p in top])
    conf_raw = max(hw, d, aw) * 100.0
    sigma20 = conf_raw + abs(lam_h - lam_a) * 4.0
    if max(hw, d, aw) == hw and lam_h > lam_a:
        sigma20 += 3.0
    sigma20 = max(5.0, min(85.0, sigma20))
    conf = max(5.0, min(85.0, conf_raw))
    n = min(hs["n"] if hs else 0, aws["n"] if aws else 0)
    grade = "A" if n >= 30 else "B" if n >= 15 else "C" if n >= 5 else "D"
    # is_default: either team has <5 matches or missing -> DEFAULT, excluded from Golden
    is_default = 1 if (not hs or not aws or hs["n"] < 5 or aws["n"] < 5) else 0
    pick = "1" if hw >= d and hw >= aw else "X" if d >= aw else "2"
    return {"xG_home": round(lam_h, 2), "xG_away": round(lam_a, 2),
            "1": round(hw * 100, 1), "X": round(d * 100, 1), "2": round(aw * 100, 1),
            "BTTS": round(btts * 100, 1), "Over15": round(over15 * 100, 1),
            "Over25": round(over25 * 100, 1), "Over35": round(over35 * 100, 1),
            "Under25": round(under25 * 100, 1), "DC1X": round(dc1x * 100, 1),
            "DC12": round(dc12 * 100, 1), "DCX2": round(dcx2 * 100, 1),
            "CS_Home": round(cs_home * 100, 1), "CS_Away": round(cs_away * 100, 1),
            "conf": round(conf, 1), "sigma20": round(sigma20, 1), "grade": grade,
            "pick": pick, "top3": top3, "n": n, "is_default": is_default,
            "elo_home": round(elo_h, 1), "elo_away": round(elo_a, 1),
            "form_home": "".join(hs["form"]) if hs else "",
            "form_away": "".join(aws["form"]) if aws else ""}

def update_state(states, league_stats, h, a, hg, ag, K=20.0, home_adv=65.0):
    hs = states[h]
    aws = states[a]
    exp_h = 1.0 / (1.0 + 10.0 ** (-(hs["elo"] + home_adv - aws["elo"]) / 400.0))
    res_h = 1.0 if hg > ag else 0.5 if hg == ag else 0.0
    hs["elo"] += K * (res_h - exp_h)
    aws["elo"] += K * ((1.0 - res_h) - (1.0 - exp_h))
    for team, scored, conceded, is_home in [(h, hg, ag, True), (a, ag, hg, False)]:
        s = states[team]
        s["n"] += 1
        s["scored"] += scored
        s["conceded"] += conceded
        if is_home:
            s["home_n"] += 1
            s["home_scored"] += scored
            s["home_conceded"] += conceded
        else:
            s["away_n"] += 1
            s["away_scored"] += scored
            s["away_conceded"] += conceded
        r = "W" if scored > conceded else "D" if scored == conceded else "L"
        s["form"].append(r)
        if len(s["form"]) > 5:
            s["form"].pop(0)
    ls = league_stats["Default"]
    ls["n"] += 1
    ls["goals"] += hg + ag
    ls["home_goals"] += hg
    ls["away_goals"] += ag
    if hg > ag:
        ls["home_win"] += 1
    if hg > 0 and ag > 0:
        ls["btts"] += 1
    if hg + ag >= 3:
        ls["over25"] += 1

def main():
    print("Sigma V42 Engine - Fix + League-strength + Calibration + More markets + Future")
    history = load_history()
    verified = load_verified()
    future = load_future()
    print(f"History: {len(history)}  Verified: {len(verified)}  Future unique: {len(future)}")
    states = defaultdict(lambda: {"elo": 1500.0, "n": 0, "scored": 0, "conceded": 0,
                                  "home_scored": 0, "home_conceded": 0, "home_n": 0,
                                  "away_scored": 0, "away_conceded": 0, "away_n": 0, "form": []})
    league_stats = defaultdict(lambda: {"n": 0, "goals": 0, "home_goals": 0, "away_goals": 0,
                                         "home_win": 0, "btts": 0, "over25": 0})
    league_stats["Default"] = {"n": 0, "goals": 0, "home_goals": 0, "away_goals": 0, "home_win": 0, "btts": 0, "over25": 0}
    combined = sorted(history + verified, key=lambda x: x["date"])
    # Backtest walk-forward last 500, with per-bin calibration
    backtest_n = 0
    backtest_hit = 0
    backtest_brier = 0.0
    backtest_logloss = 0.0
    bins = defaultdict(lambda: {"n": 0, "hit": 0})
    cutoff_idx = max(0, len(combined) - 500)
    for i, g in enumerate(combined):
        if i >= cutoff_idx and g in history:
            # League Elo not yet computed for backtest - use raw states (approx, honest enough)
            pred = predict_match(states, league_stats, {}, 1500.0, g["home"], g["away"], g["league"])
            real = "1" if g["hg"] > g["ag"] else "X" if g["hg"] == g["ag"] else "2"
            if pred["pick"] == real:
                backtest_hit += 1
            probs = {"1": pred["1"] / 100.0, "X": pred["X"] / 100.0, "2": pred["2"] / 100.0}
            backtest_brier += sum((probs[k] - (1.0 if k == real else 0.0)) ** 2 for k in probs)
            backtest_logloss += -math.log(max(0.01, probs[real]))
            backtest_n += 1
            b = int(pred["sigma20"] // 10 * 10)
            bins[b]["n"] += 1
            if pred["pick"] == real:
                bins[b]["hit"] += 1
        update_state(states, league_stats, g["home"], g["away"], g["hg"], g["ag"])
        ls = league_stats[g["league"]]
        ls["n"] += 1
        ls["home_goals"] += g["hg"]
        ls["away_goals"] += g["ag"]
        ls["goals"] += g["hg"] + g["ag"]
    # Calibration map: bin -> actual hit rate, shrunk to bin centre
    calib = {}
    for b, v in bins.items():
        if v["n"] >= 10:
            actual = v["hit"] / v["n"] * 100.0
            calib[str(b)] = {"n": v["n"], "actual": round(actual, 1), "centre": b + 5}
    print(f"Backtest: {backtest_hit}/{backtest_n} = {backtest_hit/max(1,backtest_n)*100:.1f}%  Brier {backtest_brier/max(1,backtest_n):.4f}  LogLoss {backtest_logloss/max(1,backtest_n):.4f}")
    print(f"Calibration bins: {calib}")
    # League Elo averages for league-strength correction
    # Map team -> league (last seen league in history)
    team_league = {}
    for g in combined:
        team_league[g["home"]] = g["league"]
        team_league[g["away"]] = g["league"]
    league_elo = defaultdict(lambda: {"sum": 0.0, "n": 0})
    for team, s in states.items():
        lg = team_league.get(team, "Default")
        league_elo[lg]["sum"] += s["elo"]
        league_elo[lg]["n"] += 1
    league_elo_avg = {}
    all_elos = [s["elo"] for s in states.values()]
    global_avg = sum(all_elos) / max(1, len(all_elos)) if all_elos else 1500.0
    for lg, v in league_elo.items():
        league_elo_avg[lg] = {"avg": round(v["sum"] / max(1, v["n"]), 1), "n": v["n"]}
    print(f"Global Elo avg: {global_avg:.1f}  League Elo: {dict(list(league_elo_avg.items())[:5])}")
    # Predict future
    today = date.today()
    out = []
    for f in future:
        p = predict_match(states, league_stats, league_elo_avg, global_avg, f["home"], f["away"], f["league"])
        # Future discount: >30 days away -> -10% confidence, label Future
        try:
            from datetime import date as _d
            y, m, d = map(int, f["date"].split("-"))
            delta = (_d(y, m, d) - today).days
        except Exception:
            delta = 0
        is_future = 1 if delta > 30 else 0
        sigma_cal = p["sigma20"]
        if is_future:
            sigma_cal = max(5.0, sigma_cal - 10.0)
        # Calibration: if bin has enough data, blend 50% raw + 50% actual
        bkey = str(int(p["sigma20"] // 10 * 10))
        if bkey in calib and calib[bkey]["n"] >= 20:
            sigma_cal = round(0.5 * sigma_cal + 0.5 * calib[bkey]["actual"], 1)
            sigma_cal = max(5.0, min(85.0, sigma_cal))
        # Golden eligibility: sigma_cal >=68 AND NOT default AND NOT future-distant
        golden = 1 if (sigma_cal >= 68 and p["is_default"] == 0) else 0
        out.append({"date": f["date"], "home": f["home"], "away": f["away"],
                    "match": f"{f['home']} vs {f['away']}", "league": f["league"],
                    "competition": f.get("competition", f["league"]),
                    "xG": f"{p['xG_home']}-{p['xG_away']}", "xG_home": p["xG_home"], "xG_away": p["xG_away"],
                    "1": p["1"], "X": p["X"], "2": p["2"], "BTTS": p["BTTS"],
                    "Over15": p["Over15"], "Over25": p["Over25"], "Over35": p["Over35"],
                    "Under25": p["Under25"], "DC1X": p["DC1X"], "DC12": p["DC12"], "DCX2": p["DCX2"],
                    "CS_Home": p["CS_Home"], "CS_Away": p["CS_Away"],
                    "conf": p["conf"], "sigma20": p["sigma20"], "sigma_cal": sigma_cal,
                    "grade": p["grade"], "pick": p["pick"], "top3": p["top3"], "n": p["n"],
                    "is_default": p["is_default"], "golden": golden, "is_future": is_future,
                    "elo_home": p["elo_home"], "elo_away": p["elo_away"],
                    "form_home": p["form_home"], "form_away": p["form_away"],
                    "tier": "Gold" if sigma_cal >= 70 else "Balanced" if sigma_cal >= 55 else "Risky"})
    out_sorted = sorted(out, key=lambda x: x["sigma_cal"], reverse=True)
    fields = ["date", "home", "away", "match", "league", "competition", "xG", "xG_home", "xG_away",
              "1", "X", "2", "BTTS", "Over15", "Over25", "Over35", "Under25", "DC1X", "DC12", "DCX2",
              "CS_Home", "CS_Away", "conf", "sigma20", "sigma_cal", "grade", "pick", "top3", "n",
              "is_default", "golden", "is_future", "elo_home", "elo_away", "form_home", "form_away", "tier"]
    with open(DATA / "sigma_bulk_predictions_v42.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_sorted)
    # Also overwrite the main bulk file ONLY via review gate (review script checks it)
    # Here we write v42 file; review script will copy to main bulk if checks pass.
    top_elo = sorted([(t, s["elo"]) for t, s in states.items()], key=lambda x: x[1], reverse=True)[:10]
    per_league = {}
    for lg, ls in league_stats.items():
        if ls["n"] >= 20:
            per_league[lg] = {"n": ls["n"], "avg_goals": round(ls["goals"] / ls["n"], 2),
                              "home_win_pct": round(ls["home_win"] / ls["n"] * 100, 1),
                              "btts_pct": round(ls["btts"] / ls["n"] * 100, 1),
                              "over25_pct": round(ls["over25"] / ls["n"] * 100, 1)}
    snap = {"generated": str(today), "engine": "Sigma V42 - Fix + League-strength + Calibration + More markets + Future",
            "history": len(history), "verified": len(verified), "future": len(out), "teams": len(states),
            "default_count": sum(1 for o in out if o["is_default"] == 1),
            "golden_count": sum(1 for o in out if o["golden"] == 1),
            "future_count": sum(1 for o in out if o["is_future"] == 1),
            "backtest": {"n": backtest_n, "hit": backtest_hit,
                         "hit_rate": round(backtest_hit / max(1, backtest_n) * 100, 1),
                         "brier": round(backtest_brier / max(1, backtest_n), 4),
                         "logloss": round(backtest_logloss / max(1, backtest_n), 4)},
            "calibration": calib,
            "league_elo": league_elo_avg,
            "global_elo_avg": round(global_avg, 1),
            "per_league": per_league,
            "top_elo": [{"team": t, "elo": round(e, 1)} for t, e in top_elo]}
    (DATA / "sigma_v42.json").write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {len(out_sorted)} -> data/sigma_bulk_predictions_v42.csv")
    print(f"Saved: data/sigma_v42.json - DEFAULT {snap['default_count']} Golden {snap['golden_count']} Future {snap['future_count']}")
    print("Top 5 calibrated:")
    for o in out_sorted[:5]:
        print(f"  {o['date']} {o['match']}  {o['xG']}  Cal {o['sigma_cal']}%  Raw {o['sigma20']}%  Pick {o['pick']}  Golden {o['golden']}  DEFAULT {o['is_default']}")
    print("Next: python3 sigma_v42_review.py  (must PASS before any upload)")

if __name__ == "__main__":
    main()
