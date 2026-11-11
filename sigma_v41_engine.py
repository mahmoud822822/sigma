#!/usr/bin/env python3
# Sigma V41 Engine - B: Elo + Dixon-Coles + Form last-5 + Per-League Calibration
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# Uses ONLY stdlib - works in Termux. No invented teams/lineups.
# Reads: data/sigma_history.csv, sigma_real_verified.csv, data/sigma_next_month.json
# Writes: data/sigma_bulk_predictions.csv + data/sigma_v41.json
import csv, json, math, os
from datetime import date
from collections import defaultdict
from pathlib import Path

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
        return n
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
            out = []
            seen = set()
            for r in rows:
                try:
                    if r.get("status") and r["status"] != "FINISHED":
                        continue
                    h = canon_team(r.get("home") or r.get("homeTeam") or "")
                    a = canon_team(r.get("away") or r.get("awayTeam") or "")
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
                                "ag": int(r["real_away"]), "league": r.get("league", "Default"),
                                "ph": int(r["predicted_home"]), "pa": int(r["predicted_away"])})
                except Exception:
                    continue
            return out
    return []

def load_future():
    for cand in [DATA / "sigma_next_month.json", BASE / "sigma_next_month.json"]:
        if cand.exists():
            data = json.load(open(cand, encoding="utf-8"))
            items = data if isinstance(data, list) else data.get("matches", data.get("data", []))
            out = []
            for mm in items:
                try:
                    if isinstance(mm.get("match"), str) and " vs " in mm["match"]:
                        h, a = mm["match"].split(" vs ")
                    else:
                        h = mm.get("homeTeam") or mm.get("home") or "?"
                        a = mm.get("awayTeam") or mm.get("away") or "?"
                        if isinstance(h, dict):
                            h = h.get("name", "?")
                        if isinstance(a, dict):
                            a = a.get("name", "?")
                    out.append({"date": str(mm.get("date") or mm.get("utcDate") or "")[:10],
                                "home": canon_team(str(h).strip()), "away": canon_team(str(a).strip()),
                                "league": mm.get("league") or mm.get("competition") or "Default",
                                "competition": mm.get("competition") or mm.get("league") or "Default"})
                except Exception:
                    continue
            return out
    return []

class TeamState:
    def __init__(self):
        self.elo = 1500.0
        self.n = 0
        self.scored = 0
        self.conceded = 0
        self.home_scored = 0
        self.home_conceded = 0
        self.home_n = 0
        self.away_scored = 0
        self.away_conceded = 0
        self.away_n = 0
        self.form = []  # last 5: W/D/L, most recent last

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

def league_avg_for(league_stats, league):
    ls = league_stats.get(league) or league_stats["Default"]
    if ls["n"] < 20:
        ls = league_stats["Default"]
    if ls["n"] == 0:
        return (1.55, 1.25, 1.35)
    hg = ls["home_goals"] / ls["n"]
    ag = ls["away_goals"] / ls["n"]
    return (hg, ag, (hg + ag) / 2.0)

def predict_match(states, league_stats, home, away, league):
    hs = states.get(home)
    aws = states.get(away)
    lh_home, lh_away, _ = league_avg_for(league_stats, league)
    # Shrinkage: n/(n+8) - small sample pulls to league avg
    def attack(s, is_home):
        if not s or s["n"] == 0:
            return 1.0
        base_avg = lh_home if is_home else lh_away
        if base_avg == 0:
            return 1.0
        if is_home and s["home_n"] >= 3:
            raw = (s["home_scored"] / max(1, s["home_n"])) / base_avg
            w = s["home_n"] / (s["home_n"] + 8.0)
        elif not is_home and s["away_n"] >= 3:
            raw = (s["away_scored"] / max(1, s["away_n"])) / base_avg
            w = s["away_n"] / (s["away_n"] + 8.0)
        else:
            raw = (s["scored"] / max(1, s["n"])) / ((lh_home + lh_away) / 2.0)
            w = s["n"] / (s["n"] + 8.0)
        return 1.0 + w * (raw - 1.0)
    def defence(s, is_home):
        if not s or s["n"] == 0:
            return 1.0
        base_avg = lh_away if is_home else lh_home
        if base_avg == 0:
            return 1.0
        if is_home and s["home_n"] >= 3:
            raw = (s["home_conceded"] / max(1, s["home_n"])) / base_avg
            w = s["home_n"] / (s["home_n"] + 8.0)
        elif not is_home and s["away_n"] >= 3:
            raw = (s["away_conceded"] / max(1, s["away_n"])) / base_avg
            w = s["away_n"] / (s["away_n"] + 8.0)
        else:
            raw = (s["conceded"] / max(1, s["n"])) / ((lh_home + lh_away) / 2.0)
            w = s["n"] / (s["n"] + 8.0)
        return 1.0 + w * (raw - 1.0)
    # Elo factor, capped - never lets one team explode
    elo_h = hs["elo"] if hs else 1500.0
    elo_a = aws["elo"] if aws else 1500.0
    elo_diff = elo_h - elo_a
    elo_factor_h = max(0.85, min(1.18, math.exp(elo_diff / 600.0)))
    elo_factor_a = max(0.85, min(1.18, math.exp(-elo_diff / 600.0)))
    # Form factor: points in last 5, 0-15 -> 0.92 to 1.08
    def form_factor(s):
        if not s or not s["form"]:
            return 1.0
        pts = sum(3 if x == "W" else 1 if x == "D" else 0 for x in s["form"])
        return 0.92 + (pts / 15.0) * 0.16
    lam_h = lh_home * attack(hs, True) * defence(aws, False) * elo_factor_h * form_factor(hs)
    lam_a = lh_away * attack(aws, False) * defence(hs, True) * elo_factor_a * form_factor(aws)
    lam_h = max(0.2, min(3.5, lam_h))
    lam_a = max(0.2, min(3.5, lam_a))
    # Dixon-Coles: rho = -0.13, tau for low scores
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
    mat = {}
    total = 0.0
    for x in range(7):
        for y in range(7):
            p = poisson(lam_h, x) * poisson(lam_a, y) * tau(x, y)
            mat[(x, y)] = max(0.0, p)
            total += mat[(x, y)]
    for k in mat:
        mat[k] /= total
    hw = sum(p for (x, y), p in mat.items() if x > y)
    d = sum(p for (x, y), p in mat.items() if x == y)
    aw = sum(p for (x, y), p in mat.items() if x < y)
    btts = sum(p for (x, y), p in mat.items() if x > 0 and y > 0)
    over25 = sum(p for (x, y), p in mat.items() if x + y >= 3)
    top = sorted(mat.items(), key=lambda z: z[1], reverse=True)[:3]
    top3 = " / ".join([f"{x}-{y} {p*100:.1f}%" for (x, y), p in top])
    conf_raw = max(hw, d, aw) * 100.0
    # Sigma 2.0: conf + xG gap + home edge, capped 5-85
    xg_gap = abs(lam_h - lam_a)
    sigma20 = conf_raw + xg_gap * 4.0
    if max(hw, d, aw) == hw and lam_h > lam_a:
        sigma20 += 3.0
    sigma20 = max(5.0, min(85.0, sigma20))
    conf = max(5.0, min(85.0, conf_raw))
    n = min(hs["n"] if hs else 0, aws["n"] if aws else 0)
    grade = "A" if n >= 30 else "B" if n >= 15 else "C" if n >= 5 else "D"
    pick = "1" if hw >= d and hw >= aw else "X" if d >= aw else "2"
    return {"xG_home": round(lam_h, 2), "xG_away": round(lam_a, 2),
            "1": round(hw * 100, 1), "X": round(d * 100, 1), "2": round(aw * 100, 1),
            "BTTS": round(btts * 100, 1), "Over25": round(over25 * 100, 1),
            "conf": round(conf, 1), "sigma20": round(sigma20, 1), "grade": grade,
            "pick": pick, "top3": top3, "n": n,
            "elo_home": round(elo_h, 1), "elo_away": round(elo_a, 1),
            "form_home": "".join(hs["form"]) if hs else "",
            "form_away": "".join(aws["form"]) if aws else ""}

def main():
    print("Sigma V41 Engine - Elo + Dixon-Coles + Form + Calibration")
    history = load_history()
    verified = load_verified()
    future = load_future()
    print(f"History: {len(history)}  Verified: {len(verified)}  Future: {len(future)}")
    # Build states from history + verified (chronological)
    states = defaultdict(lambda: {"elo": 1500.0, "n": 0, "scored": 0, "conceded": 0,
                                  "home_scored": 0, "home_conceded": 0, "home_n": 0,
                                  "away_scored": 0, "away_conceded": 0, "away_n": 0, "form": []})
    league_stats = defaultdict(lambda: {"n": 0, "goals": 0, "home_goals": 0, "away_goals": 0,
                                         "home_win": 0, "btts": 0, "over25": 0})
    league_stats["Default"] = {"n": 0, "goals": 0, "home_goals": 0, "away_goals": 0, "home_win": 0, "btts": 0, "over25": 0}
    combined = sorted(history + verified, key=lambda x: x["date"])
    # Backtest: walk-forward on last 500 history matches, honest (predict before update)
    backtest_n = 0
    backtest_hit = 0
    backtest_brier = 0.0
    backtest_logloss = 0.0
    # First, train on all but last 500, then walk last 500
    cutoff_idx = max(0, len(combined) - 500)
    for i, g in enumerate(combined):
        if i >= cutoff_idx and g in history:
            # Predict before learning this match
            pred = predict_match(states, league_stats, g["home"], g["away"], g["league"])
            real = "1" if g["hg"] > g["ag"] else "X" if g["hg"] == g["ag"] else "2"
            if pred["pick"] == real:
                backtest_hit += 1
            probs = {"1": pred["1"] / 100.0, "X": pred["X"] / 100.0, "2": pred["2"] / 100.0}
            brier = sum((probs[k] - (1.0 if k == real else 0.0)) ** 2 for k in probs)
            backtest_brier += brier
            backtest_logloss += -math.log(max(0.01, probs[real]))
            backtest_n += 1
        update_state(states, league_stats, g["home"], g["away"], g["hg"], g["ag"])
        # Also update per-league stats (not just Default) - approximate: add to that league too
        ls = league_stats[g["league"]]
        ls["n"] += 1
        ls["home_goals"] += g["hg"]
        ls["away_goals"] += g["ag"]
        ls["goals"] += g["hg"] + g["ag"]
    print(f"Backtest walk-forward last {backtest_n}: Hit {backtest_hit}/{backtest_n} = {backtest_hit/max(1,backtest_n)*100:.1f}%  Brier {backtest_brier/max(1,backtest_n):.4f}  LogLoss {backtest_logloss/max(1,backtest_n):.4f}")
    # Predict future
    out = []
    for f in future:
        p = predict_match(states, league_stats, f["home"], f["away"], f["league"])
        out.append({"date": f["date"], "match": f"{f['home']} vs {f['away']}", "league": f["league"],
                    "competition": f.get("competition", f["league"]),
                    "xG": f"{p['xG_home']}-{p['xG_away']}", "xG_home": p["xG_home"], "xG_away": p["xG_away"],
                    "1": p["1"], "X": p["X"], "2": p["2"], "BTTS": p["BTTS"], "Over25": p["Over25"],
                    "conf": p["conf"], "sigma20": p["sigma20"], "grade": p["grade"], "pick": p["pick"],
                    "top3": p["top3"], "n": p["n"], "elo_home": p["elo_home"], "elo_away": p["elo_away"],
                    "form_home": p["form_home"], "form_away": p["form_away"],
                    "tier": "Gold" if p["sigma20"] >= 70 else "Balanced" if p["sigma20"] >= 55 else "Risky"})
    out_sorted = sorted(out, key=lambda x: x["sigma20"], reverse=True)
    # Save bulk CSV
    fields = ["date", "match", "league", "competition", "xG", "xG_home", "xG_away", "1", "X", "2", "BTTS", "Over25", "conf", "sigma20", "grade", "pick", "top3", "n", "elo_home", "elo_away", "form_home", "form_away", "tier"]
    with open(DATA / "sigma_bulk_predictions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_sorted)
    # Save JSON for site
    top_elo = sorted([(t, s["elo"]) for t, s in states.items()], key=lambda x: x[1], reverse=True)[:10]
    per_league = {}
    for lg, ls in league_stats.items():
        if ls["n"] >= 20:
            per_league[lg] = {"n": ls["n"], "avg_goals": round(ls["goals"] / ls["n"], 2),
                              "home_win_pct": round(ls["home_win"] / ls["n"] * 100, 1),
                              "btts_pct": round(ls["btts"] / ls["n"] * 100, 1),
                              "over25_pct": round(ls["over25"] / ls["n"] * 100, 1)}
    snap = {"generated": str(date.today()) if hasattr(date, "today") else "",
            "engine": "Sigma V41 - Elo + Dixon-Coles + Form + Calibration",
            "history": len(history), "verified": len(verified), "future": len(out), "teams": len(states),
            "backtest": {"n": backtest_n, "hit": backtest_hit,
                         "hit_rate": round(backtest_hit / max(1, backtest_n) * 100, 1),
                         "brier": round(backtest_brier / max(1, backtest_n), 4),
                         "logloss": round(backtest_logloss / max(1, backtest_n), 4)},
            "per_league": per_league,
            "top_elo": [{"team": t, "elo": round(e, 1)} for t, e in top_elo]}
    (DATA / "sigma_v41.json").write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {len(out_sorted)} predictions -> data/sigma_bulk_predictions.csv")
    print(f"Saved: data/sigma_v41.json - Teams {len(states)} Top Elo: {top_elo[:3]}")
    print("Top 5 Sigma 2.0:")
    for o in out_sorted[:5]:
        print(f"  {o['date']} {o['match']}  {o['xG']}  Sigma20 {o['sigma20']}%  Pick {o['pick']}  Elo {o['elo_home']} vs {o['elo_away']}  Form {o['form_home']} vs {o['form_away']}")

if __name__ == "__main__":
    main()
