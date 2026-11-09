#!/usr/bin/env python3
# Sigma Forecaster - Merged Version
# Sigma - Mahmoud Emad
# Self-Evolving Forecaster + Sigma Safety Standard V2
# Uses ONLY stdlib (csv) - works in Termux without pandas/sklearn
# V2 Lessons: BTTS weight 100 -> 70, Late 76-90 weight 26% -> 30%, Weak home +15%

import csv
import os
import statistics
from pathlib import Path

BASE = Path(__file__).parent
DATA_FILE = BASE / "data" / "sigma_real_verified.csv"
if not DATA_FILE.exists():
    alt = BASE / "sigma_real_verified.csv"
    if alt.exists():
        DATA_FILE = alt

SIGMA_V2 = {
    "btts_weight": 70,
    "late_weight_76_90": 30,
    "weak_home_bonus": 15,
    "safety_rule": "1 goal safer than 2 | Any team safer than specific team | Asian Over 1 refund safer than BTTS",
}

def load_data(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                ph, pa = int(r["predicted_home"]), int(r["predicted_away"])
                rh, ra = int(r["real_home"]), int(r["real_away"])
            except:
                continue
            rows.append({
                "match": r["match"],
                "predicted": (ph, pa),
                "real": (rh, ra),
                "bet": r.get("bet",""),
                "bet_result": r.get("bet_result",""),
            })
    return rows

def evaluate(rows):
    total_diff = []
    btts_diff = []
    exact = 0
    correct = 0
    for r in rows:
        ph, pa = r["predicted"]
        rh, ra = r["real"]
        total_diff.append(abs((ph+pa)-(rh+ra)))
        pred_btts = 1 if ph>0 and pa>0 else 0
        real_btts = 1 if rh>0 and ra>0 else 0
        btts_diff.append(abs(pred_btts-real_btts))
        if ph==rh and pa==ra:
            exact += 1
        if r["bet_result"]=="correct":
            correct += 1
    n = len(rows)
    return {
        "n": n,
        "hit_rate": correct/n*100 if n else 0,
        "correct": correct,
        "exact_rate": exact/n*100 if n else 0,
        "exact": exact,
        "mae_total": statistics.mean(total_diff) if total_diff else 0,
        "mae_btts": statistics.mean(btts_diff) if btts_diff else 0,
        "avg_real_goals": statistics.mean([r["real"][0]+r["real"][1] for r in rows]) if rows else 0,
        "avg_pred_goals": statistics.mean([r["predicted"][0]+r["predicted"][1] for r in rows]) if rows else 0,
    }

def main():
    print("="*55)
    print("Sigma Forecaster - Mahmoud Emad - V2")
    print("="*55)
    print(f"Data: {DATA_FILE}")
    print(f"BTTS weight: {SIGMA_V2['btts_weight']} | Late 76-90: {SIGMA_V2['late_weight_76_90']}% | Weak home: +{SIGMA_V2['weak_home_bonus']}%")
    print(f"Safety: {SIGMA_V2['safety_rule']}")
    print("-"*55)
    if not DATA_FILE.exists():
        print("ERROR: data file not found!")
        print("Copy sigma_real_verified.csv to data/ folder")
        print("Expected: sigma-final/data/sigma_real_verified.csv")
        return
    rows = load_data(DATA_FILE)
    m = evaluate(rows)
    print(f"Matches: {m['n']}")
    print(f"Hit rate: {m['hit_rate']:.1f}% ({m['correct']}/{m['n']})")
    print(f"Exact score: {m['exact_rate']:.1f}% ({m['exact']}/{m['n']})")
    print(f"MAE total goals: {m['mae_total']:.2f}")
    print(f"MAE BTTS: {m['mae_btts']:.2f}")
    print(f"Avg goals: Real {m['avg_real_goals']:.2f} vs Predicted {m['avg_pred_goals']:.2f}")
    print("-"*55)
    print("Sigma Learned V2:")
    print("1. BTTS weight 100 -> 70 (Brentford/Como failed)")
    print("2. Late 76-90 weight 26% -> 30% (90+2, 90+6, 90+4)")
    print("3. Weak home +15% (Sunderland 1-0 Chelsea)")
    print("4. Exact score is NOT the goal - focus on safety")
    print("5. Early goal exception - pressing team can score early")
    print("="*55)
    print("Signature Prediction and Forecast: Sigma - Mahmoud Emad")

if __name__ == "__main__":
    main()
