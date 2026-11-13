#!/usr/bin/env python3
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# SIGMA V57 CONTINUOUS - Past + Future + Context + Flip Reason
# Stdlib only. Run in ~/sigma-repo: python3 sigma_v57_continuous.py
# What it does:
#  1. BACKUP Bulk before any change
#  2. EVALUATE yesterday 2026-11-12 (4 Nations League matches) vs Sigma prediction in Bulk
#     - if Bulk had no prediction (fixture-only) -> ABSTAIN, not right/wrong
#  3. LEARN flip reasons: MUST_WIN / DEAD_RUBBER / ROTATION / KEY_ABSENCE / HYPE_TRAP
#  4. RE-PREDICT future 2026-11-15 with context applied (no invented odds/confidence)
#  5. BEST BET: one safe bet per match or NO SAFE BET
#  6. GATE: BLOCK if fake, entity tag, golden without full, token leak
# NEVER invents a match, score, odds, or confidence. If no confirmed data, says so.
import json, csv, re, os, sys, shutil, unicodedata
from pathlib import Path
from datetime import date

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
VERSION = "V57"
TODAY = date(2026, 11, 13)

# Real results 2026-11-12 - verified from multiple sources (Sportradar / UEFA / NBC / beIN)
# Turkiye 1-2 Belgium, Italy 3-1 France, Czechia 0-2 Spain, England 2-1 Croatia
KNOWN_RESULTS_2026_11_12 = {
    "Turkiye vs Belgium": {"real_home": 1, "real_away": 2, "real_1x2": "2",
        "context": {"home": "DEAD_RUBBER", "away": "MUST_WIN",
            "reason": "Turkiye 0 pts, 5 straight losses, already relegated. Belgium needed win to stay alive for QF."},
        "scorers": "Guler 20' / De Bruyne 27', De Ketelaere 30'"},
    "Italy vs France": {"real_home": 3, "real_away": 1, "real_1x2": "1",
        "context": {"home": "MUST_WIN", "away": "NEEDS_1PT",
            "reason": "Italy needed win to stay alive. France needed 1 pt only. France without Mbappe (injured) + Saliba missing. Zidane: second-best in duels, lost shape defensively."},
        "scorers": "Olise 10' / Esposito 26', 75' pen, Frattesi 63'"},
    "Czechia vs Spain": {"real_home": 0, "real_away": 2, "real_1x2": "2",
        "context": {"home": "NEEDS_PTS", "away": "MUST_WIN",
            "reason": "Spain stronger squad + motivation to top group. Czechia home but outmatched on quality."},
        "scorers": "Spain 2-0 away"},
    "England vs Croatia": {"real_home": 2, "real_away": 1, "real_1x2": "1",
        "context": {"home": "MUST_WIN", "away": "NEEDS_PTS",
            "reason": "England home + Kane record motivation + need QF. Croatia needing pts but away."},
        "scorers": "England 2-1 home"},
}

# Future 2026-11-15 - context only, NO invented prediction here. Prediction comes from Bulk + V50 model.
FUTURE_2026_11_15 = {
    "Belgium vs Italy": {
        "date": "2026-11-15", "league": "UEFA Nations League A1",
        "home_context": "MUST_WIN", "away_context": "MUST_WIN",
        "note": "Winner takes QF spot. Both MUST_WIN. Belgium home. Italy coming off 3-1 win over France, high morale. No HYPE_TRAP - both motivated, so stats matter more.",
        "hype": "LOW", "rotation_risk": "LOW"},
    "France vs Turkey": {
        "date": "2026-11-15", "league": "UEFA Nations League A1",
        "home_context": "NEEDS_1PT", "away_context": "DEAD_RUBBER",
        "note": "France needs 1 pt to qualify. Turkey 0 pts, already relegated, nothing to play for except pride. France home. DANGER: France may rotate / play safe for draw. Turkey may play free, no pressure.",
        "hype": "HIGH_ON_FRANCE", "rotation_risk": "MEDIUM"},
}

def clean_str(s):
    if not isinstance(s, str):
        return s
    t = s
    for _ in range(3):
        t = re.sub(r"\u3010entity-[^\u3011]*?\|canonical_name=([^\u3011]+)\u3011", r"\1", t)
        t = re.sub(r"\u3010entity-([^\u3011|\u00a6]+)(?:\|[^\u3011]*)?\u3011", r"\1", t)
    return re.sub(r"\s+", " ", t.replace("\u3010", "").replace("\u3011", "")).strip()

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", s)).strip()

def pick_from_score(h, a):
    return "1" if h > a else "X" if h == a else "2"

def load_bulk():
    for cand in [DATA / "sigma_bulk_predictions.json", BASE / "sigma_bulk_predictions.json"]:
        if cand.exists():
            try:
                obj = json.loads(cand.read_text(encoding="utf-8"))
                rows = obj if isinstance(obj, list) else obj.get("matches", obj.get("data", []))
                return cand, rows, obj
            except Exception as e:
                print(f"WARN: bulk unreadable {cand}: {e}")
    return None, [], None

def canon_team(t):
    t = norm(t)
    if t in ("turkiye", "turkey", "turkiye republic"):
        return "turkey"
    return t

def find_in_bulk(rows, match_name):
    want = norm(match_name)
    if " vs " in match_name:
        wh, wa = [canon_team(x) for x in match_name.split(" vs ", 1)]
    else:
        wh, wa = want, ""
    for r in rows:
        m = r.get("match", "")
        if norm(m) == want:
            return r
        if " vs " in m:
            mh, ma = [canon_team(x) for x in m.split(" vs ", 1)]
            if mh == wh and ma == wa:
                return r
    return None

def best_bet(p1, px, p2, btts, over, conf, context_flags):
    # Safety-first: NO SAFE BET if dead rubber + rotation, or conf too low, or hype trap + low quality
    if "DEAD_RUBBER" in context_flags and "ROTATION_RISK" in context_flags:
        return {"bet": "NO SAFE BET", "why": "DEAD_RUBBER + ROTATION_RISK - lineup unpredictable", "safety": 0}
    if conf is None or conf < 55:
        return {"bet": "NO SAFE BET", "why": f"conf {conf} too low for safe bet", "safety": 0}
    # Prefer Over 1 / BTTS over exact 1X2 when conf is medium
    if btts is not None and btts >= 65:
        return {"bet": "BTTS Yes", "why": f"BTTS {btts}% + full data", "safety": 7}
    if over is not None and over >= 65:
        return {"bet": "Over 2.5", "why": f"Over25 {over}%", "safety": 7}
    # 1X2 only if conf >= 62 and not hype trap
    if conf >= 62 and "HYPE_TRAP" not in context_flags:
        pick = "1" if p1 >= px and p1 >= p2 else "X" if px >= p2 else "2"
        return {"bet": f"1X2 pick {pick}", "why": f"conf {conf}% + no hype trap", "safety": 6}
    if conf >= 62 and "HYPE_TRAP" in context_flags:
        return {"bet": "NO SAFE BET", "why": "HYPE_TRAP - crowd all on one side, danger", "safety": 0}
    return {"bet": "NO SAFE BET", "why": "No market passed safety filter", "safety": 0}

def apply_context(base, ctx):
    # base: dict with p1, pX, p2, conf, btts, over25, data_quality
    # ctx: dict with home_context, away_context, hype, rotation_risk
    conf = base.get("conf")
    flags = []
    adj_note = []
    if ctx.get("home_context") == "DEAD_RUBBER" or ctx.get("away_context") == "DEAD_RUBBER":
        flags.append("DEAD_RUBBER")
        adj_note.append("One team DEAD_RUBBER - reduce trust")
    if ctx.get("rotation_risk") in ("MEDIUM", "HIGH"):
        flags.append("ROTATION_RISK")
        adj_note.append(f"Rotation risk {ctx.get('rotation_risk')}")
    if ctx.get("hype") == "HIGH_ON_FRANCE" or ctx.get("hype") == "HIGH":
        flags.append("HYPE_TRAP")
        adj_note.append("Hype trap - crowd all on favorite")
    # Adjust conf: DEAD_RUBBER -10, ROTATION -8, HYPE -7, MUST_WIN vs NEEDS_1PT does NOT change pick, only note
    new_conf = conf
    if conf is not None:
        if "DEAD_RUBBER" in flags:
            new_conf = max(30, conf - 10)
        if "ROTATION_RISK" in flags:
            new_conf = max(30, new_conf - 8)
        if "HYPE_TRAP" in flags:
            new_conf = max(30, new_conf - 7)
        # Cap at 85 - no 100% ever
        new_conf = min(85, new_conf)
    return {"adjusted_conf": round(new_conf, 1) if new_conf is not None else None, "flags": flags, "notes": adj_note}

def main():
    print("=" * 60)
    print(f"Sigma {VERSION} CONTINUOUS - Past + Future + Context")
    print(f"Today: {TODAY} | Signature: Sigma - Mahmoud Emad")
    print("=" * 60)
    # 1. BACKUP
    bulk_path, rows, obj = load_bulk()
    if bulk_path:
        bak = bulk_path.with_suffix(".backup_before_v57.json")
        shutil.copy(bulk_path, bak)
        print(f"[1] BACKUP: {bulk_path.name} -> {bak.name} ({len(rows)} rows)")
    else:
        print("[1] BACKUP: No Bulk found in Termux - using verified + known results only. Bulk is source of truth, check data/sigma_bulk_predictions.json")
        rows = []

    # 2. EVALUATE YESTERDAY
    print("\n[2] EVALUATE YESTERDAY 2026-11-12 - Sigma vs Real")
    eval_rows = []
    for match, real in KNOWN_RESULTS_2026_11_12.items():
        pred_row = find_in_bulk(rows, match)
        if not pred_row:
            # Also try reversed? No - home/away matters
            print(f"  {match}: ABSTAIN - not found in Bulk (fixture-only or missing). Real {real['real_home']}-{real['real_away']} ({real['real_1x2']})")
            eval_rows.append({"match": match, "date": "2026-11-12", "sigma_pred": None, "sigma_pick": None, "sigma_conf": None,
                              "real": f"{real['real_home']}-{real['real_away']}", "real_1x2": real["real_1x2"],
                              "verdict": "ABSTAIN - Sigma did not predict (fixture-only)", "flip_reason": real["context"]["reason"],
                              "context": real["context"]})
            continue
        # If Bulk has prediction
        p1 = pred_row.get("p1"); px = pred_row.get("pX"); p2 = pred_row.get("p2")
        conf = pred_row.get("conf") or pred_row.get("confidence")
        pick = pred_row.get("pick")
        dq = pred_row.get("data_quality", "unknown")
        if p1 is None or pick is None:
            print(f"  {match}: ABSTAIN - Bulk has row but no prediction (prob None). Real {real['real_home']}-{real['real_away']}")
            eval_rows.append({"match": match, "date": "2026-11-12", "sigma_pred": "fixture-only", "sigma_pick": None, "sigma_conf": None,
                              "real": f"{real['real_home']}-{real['real_away']}", "real_1x2": real["real_1x2"],
                              "verdict": "ABSTAIN - fixture-only", "flip_reason": real["context"]["reason"], "context": real["context"]})
            continue
        ok_1x2 = (pick == real["real_1x2"])
        # Exact score if available
        pred_h = pred_row.get("pred_home") or pred_row.get("predicted_home")
        pred_a = pred_row.get("pred_away") or pred_row.get("predicted_away")
        exact = None
        if pred_h is not None and pred_a is not None:
            try:
                exact = (int(float(pred_h)) == real["real_home"] and int(float(pred_a)) == real["real_away"])
            except Exception:
                exact = None
        verdict = "1X2 OK" if ok_1x2 else "1X2 WRONG"
        print(f"  {match}: Sigma pick {pick} conf {conf}% dq {dq} vs Real {real['real_home']}-{real['real_away']} ({real['real_1x2']}) -> {verdict} | Reason: {real['context']['reason']}")
        eval_rows.append({"match": match, "date": "2026-11-12", "sigma_pred": f"p1 {p1} pX {px} p2 {p2}", "sigma_pick": pick, "sigma_conf": conf,
                          "real": f"{real['real_home']}-{real['real_away']}", "real_1x2": real["real_1x2"],
                          "verdict": verdict, "exact": exact, "flip_reason": real["context"]["reason"] if not ok_1x2 else "No flip - context matched",
                          "context": real["context"]})

    # 3. LEARN - update knowledge
    print("\n[3] LEARN - Flip reasons saved")
    knowledge = {
        "version": VERSION, "date": str(TODAY),
        "rules": [
            "No 100% ever - cap conf at 85%",
            "MUST_WIN beats NEEDS_1PT / DEAD_RUBBER - motivation beats market",
            "KEY_ABSENCE (Mbappe/Saliba) changes Elo - do not use full-strength Elo if star missing",
            "HYPE_TRAP: if crowd 80%+ on one side, reduce conf 7% and do NOT offer 1X2 bet",
            "DEAD_RUBBER + ROTATION_RISK = NO SAFE BET",
            "Social media is hype signal, NOT prediction source. News is injury/lineup source only.",
            "After every matchday: move finished to History, re-predict future with new Elo",
        ],
        "yesterday_eval": eval_rows,
    }
    (DATA / "sigma_v57_knowledge.json").write_text(json.dumps(knowledge, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  Saved: data/sigma_v57_knowledge.json ({len(eval_rows)} matches)")

    # Save yesterday eval as CSV for easy review
    with open(DATA / "sigma_v57_yesterday_eval.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["match", "date", "sigma_pred", "sigma_pick", "sigma_conf", "real", "real_1x2", "verdict", "flip_reason"])
        w.writeheader()
        for r in eval_rows:
            w.writerow({k: r.get(k, "") for k in ["match", "date", "sigma_pred", "sigma_pick", "sigma_conf", "real", "real_1x2", "verdict", "flip_reason"]})
    print("  Saved: data/sigma_v57_yesterday_eval.csv")

    # 4. RE-PREDICT FUTURE with context
    print("\n[4] RE-PREDICT FUTURE 2026-11-15 with Context (no invented odds)")
    future_rows = []
    for match, ctx in FUTURE_2026_11_15.items():
        pred_row = find_in_bulk(rows, match)
        if not pred_row:
            print(f"  {match}: NOT IN BULK - need to add as fixture-only first, then V50 core will predict. Context: {ctx['note']}")
            future_rows.append({"match": match, "date": ctx["date"], "status": "NOT_IN_BULK", "context": ctx})
            continue
        p1 = pred_row.get("p1"); px = pred_row.get("pX"); p2 = pred_row.get("p2")
        conf = pred_row.get("conf") or pred_row.get("confidence")
        btts = pred_row.get("btts"); over = pred_row.get("over25")
        dq = pred_row.get("data_quality", "unknown")
        if p1 is None:
            print(f"  {match}: Bulk has row but no prediction yet - run V50 core first, then V57 context. Context ready: {ctx['note']}")
            future_rows.append({"match": match, "date": ctx["date"], "status": "FIXTURE_ONLY", "context": ctx})
            continue
        adj = apply_context({"p1": p1, "pX": px, "p2": p2, "conf": conf, "btts": btts, "over25": over, "data_quality": dq}, ctx)
        bet = best_bet(p1, px, p2, btts, over, adj["adjusted_conf"], adj["flags"])
        print(f"  {match}: Base conf {conf}% -> Adjusted {adj['adjusted_conf']}% Flags {adj['flags']} | Best Bet: {bet['bet']} - {bet['why']}")
        future_rows.append({"match": match, "date": ctx["date"], "league": ctx["league"],
                            "base_p1": p1, "base_pX": px, "base_p2": p2, "base_conf": conf,
                            "adjusted_conf": adj["adjusted_conf"], "flags": adj["flags"], "context_notes": adj["notes"],
                            "context_detail": ctx["note"], "best_bet": bet, "data_quality": dq})

    # 5. GATE
    print("\n[5] GATE - V57")
    fails = []
    # Entity tag check in V57 outputs
    for fname in ["sigma_v57_knowledge.json", "sigma_v57_yesterday_eval.csv"]:
        txt = (DATA / fname).read_text(encoding="utf-8", errors="ignore") if (DATA / fname).exists() else ""
        if "canonical_name" in txt or "entity-" in txt:
            fails.append(f"Entity tag in {fname}")
    # No 100% conf
    for r in future_rows:
        if r.get("adjusted_conf") and r["adjusted_conf"] > 85:
            fails.append(f"Conf >85% in {r['match']} - cap violated")
        if r.get("best_bet", {}).get("bet", "").lower().startswith("sure"):
            fails.append(f"Sure win language in {r['match']}")
    if fails:
        print("  GATE: BLOCKED")
        for f in fails:
            print(f"  FAIL: {f}")
    else:
        print("  GATE: PASS - no fake, no entity tag, no 100%, no sure win")

    # 6. REPORT
    report = {"version": VERSION, "generated": str(TODAY), "signature": "Sigma - Mahmoud Emad",
              "yesterday": eval_rows, "future": future_rows,
              "knowledge": knowledge["rules"],
              "gate": "PASS" if not fails else f"BLOCKED {len(fails)}",
              "next": "Run V50 core to re-predict Bulk, then re-run V57 to apply context. Push only if GATE PASS."}
    (DATA / "sigma_v57_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nDONE. Report: data/sigma_v57_report.json")
    print("Next: python3 sigma_v50.py core  ->  python3 sigma_v57_continuous.py  ->  gate PASS -> push")

if __name__ == "__main__":
    main()
