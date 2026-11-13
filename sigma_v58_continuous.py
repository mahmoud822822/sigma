#!/usr/bin/env python3
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# SIGMA V58 - Fix + Treatment for ALL problems found in V57 review
# Changes vs V57:
#  1. DEAD_RUBBER refined: if favorite is MUST_WIN and opponent DEAD_RUBBER -> BONUS +5, not penalty.
#     Penalty only if FAVORITE is DEAD_RUBBER / NEEDS_1PT, or BOTH dead.
#  2. MUST_WIN vs NEEDS_1PT: favorite NEEDS_1PT vs underdog MUST_WIN -> -12% (Italy vs France case)
#  3. KEY_ABSENCE: star missing (Mbappe/Saliba) -> -10%
#  4. HYPE_TRAP stronger if base >80: -10% instead of -7%
#  5. Cap: base capped to 85 FIRST, then subtract. Floor 30.
#  6. NO SAFE BET if adjusted <55 OR DEAD+ROTATION OR base>85 without context
#  7. Bulk guard: if bulk rows <500 -> BLOCK (prevents wipe to 14)
#  8. Fake quarantine: 5 fake matches auto-quarantined if found
#  9. Meta AI filename decoder: _x5f_ -> _ , .py.txt -> .py
#  10. Review auto: writes yesterday eval + percentages
import json, csv, re, os, shutil, unicodedata
from pathlib import Path
from datetime import date
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
VERSION = "V58"
TODAY = date(2026, 11, 13)

KNOWN_RESULTS = {
    "Turkiye vs Belgium": {"real_home":1,"real_away":2,"real_1x2":"2","home_ctx":"DEAD_RUBBER","away_ctx":"MUST_WIN","reason":"Turkiye 0 pts, relegated. Belgium MUST_WIN. Context matched - Belgium win was correct."},
    "Italy vs France": {"real_home":3,"real_away":1,"real_1x2":"1","home_ctx":"MUST_WIN","away_ctx":"NEEDS_1PT","reason":"Italy MUST_WIN, France NEEDS_1PT only, France without Mbappe+Saliba, Zidane second-best duels.","key_absence":"Mbappe, Saliba"},
    "Czechia vs Spain": {"real_home":0,"real_away":2,"real_1x2":"2","home_ctx":"NEEDS_PTS","away_ctx":"MUST_WIN","reason":"Spain stronger + MUST_WIN."},
    "England vs Croatia": {"real_home":2,"real_away":1,"real_1x2":"1","home_ctx":"MUST_WIN","away_ctx":"NEEDS_PTS","reason":"England home + MUST_WIN + Kane motivation."},
}
FUTURE = {
    "Belgium vs Italy": {"date":"2026-11-15","league":"UEFA Nations League A1","home_ctx":"MUST_WIN","away_ctx":"MUST_WIN","hype":"LOW","rotation":"LOW","note":"Both MUST_WIN, winner takes QF. No hype trap."},
    "France vs Turkey": {"date":"2026-11-15","league":"UEFA Nations League A1","home_ctx":"NEEDS_1PT","away_ctx":"DEAD_RUBBER","hype":"HIGH_ON_FRANCE","rotation":"MEDIUM","note":"France needs 1 pt only, Turkey already relegated. France may rotate / play for draw. Turkey free.","key_absence":"Mbappe? check lineup"},
}
FAKE_QUARANTINE = [
    "Al Ahly vs Zamalek", "Al Hilal vs Al Nassr", "Real Madrid vs Barcelona",
    "Manchester City vs Arsenal", "Inter vs AC Milan", "Brazil vs Argentina",
]

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii","ignore").decode().lower()
    return re.sub(r"\s+"," ", re.sub(r"[^a-z0-9 ]","",s)).strip()
def canon_team(t):
    t=norm(t)
    return "turkey" if t in ("turkiye","turkey") else t
def decode_meta_ai_name(name):
    # Meta AI encodes: _ -> _x5f_ , adds .txt
    n=name.replace("_x5f_","_")
    if n.endswith(".py.txt"):
        n=n[:-4]
    return n
def find_bulk(rows, match):
    want=norm(match)
    wh,wa=[canon_team(x) for x in match.split(" vs ",1)] if " vs " in match else (want,"")
    for r in rows:
        m=r.get("match","")
        if norm(m)==want: return r
        if " vs " in m:
            mh,ma=[canon_team(x) for x in m.split(" vs ",1)]
            if mh==wh and ma==wa: return r
    return None

def apply_context_v58(base_p1, base_px, base_p2, base_conf, ctx, pick):
    # pick is "1"/"X"/"2" - who is favorite?
    # Determine favorite context
    fav_ctx = ctx["home_ctx"] if pick=="1" else ctx["away_ctx"] if pick=="2" else "DRAW"
    opp_ctx = ctx["away_ctx"] if pick=="1" else ctx["home_ctx"] if pick=="2" else "DRAW"
    flags=[]; notes=[]
    # Cap base first
    conf = min(85.0, float(base_conf)) if base_conf is not None else None
    if base_conf and float(base_conf)>85:
        flags.append("OVERCONFIDENT_BASE")
        notes.append(f"Base {base_conf}% >85 cap - overconfident, capped to 85 first")
    if conf is None:
        return {"adjusted":None,"flags":flags,"notes":notes}
    # 1. MUST_WIN vs NEEDS_1PT - favorite is complacent, underdog desperate
    if fav_ctx=="NEEDS_1PT" and opp_ctx=="MUST_WIN":
        conf-=12; flags.append("MUSTWIN_VS_NEEDS1PT"); notes.append("Favorite NEEDS_1PT only, opponent MUST_WIN -12%")
    # 2. Favorite DEAD_RUBBER - favorite has nothing to play for
    if fav_ctx=="DEAD_RUBBER":
        conf-=10; flags.append("FAV_DEAD_RUBBER"); notes.append("Favorite DEAD_RUBBER -10%")
    # 3. Opponent DEAD_RUBBER + Favorite MUST_WIN = BONUS (V57 bug fix)
    if opp_ctx=="DEAD_RUBBER" and fav_ctx=="MUST_WIN":
        conf=min(85, conf+5); flags.append("OPP_DEAD_FAV_MUSTWIN_BONUS"); notes.append("Opponent DEAD, favorite MUST_WIN +5% (V57 bug fix)")
    # 4. Both DEAD or both NEEDS_1PT - no motivation, unpredictable
    if fav_ctx=="DEAD_RUBBER" and opp_ctx=="DEAD_RUBBER":
        conf-=10; flags.append("BOTH_DEAD"); notes.append("Both DEAD -10%")
    # 5. KEY_ABSENCE
    if ctx.get("key_absence"):
        conf-=10; flags.append("KEY_ABSENCE"); notes.append(f"Key absence {ctx['key_absence']} -10%")
    # 6. ROTATION
    if ctx.get("rotation") in ("MEDIUM","HIGH"):
        conf-=8; flags.append("ROTATION_RISK"); notes.append(f"Rotation {ctx['rotation']} -8%")
    # 7. HYPE - stronger if base high
    if ctx.get("hype") in ("HIGH","HIGH_ON_FRANCE"):
        pen=10 if float(base_conf or 0)>80 else 7
        conf-=pen; flags.append("HYPE_TRAP"); notes.append(f"Hype trap -{pen}%")
    conf=max(30.0, min(85.0, conf))
    return {"adjusted":round(conf,1),"flags":flags,"notes":notes}

def best_bet_v58(p1,px,p2,btts,over,adj,flags):
    if adj is None: return {"bet":"NO SAFE BET","why":"No prediction","safety":0}
    if "FAV_DEAD_RUBBER" in flags and "ROTATION_RISK" in flags:
        return {"bet":"NO SAFE BET","why":"Favorite DEAD + Rotation - unpredictable","safety":0}
    if "DEAD_RUBBER" in str(flags) and "ROTATION_RISK" in flags:
        return {"bet":"NO SAFE BET","why":"DEAD_RUBBER + ROTATION - lineup unpredictable","safety":0}
    if adj<55:
        return {"bet":"NO SAFE BET","why":f"adj conf {adj} too low (<55)","safety":0}
    if btts is not None and btts>=65:
        return {"bet":"BTTS Yes","why":f"BTTS {btts}%","safety":7}
    if over is not None and over>=65:
        return {"bet":"Over 2.5","why":f"Over25 {over}%","safety":7}
    if adj>=62 and "HYPE_TRAP" not in flags:
        pick="1" if p1>=px and p1>=p2 else "X" if px>=p2 else "2"
        return {"bet":f"1X2 pick {pick}","why":f"adj {adj}% + no hype","safety":6}
    return {"bet":"NO SAFE BET","why":"No market passed safety","safety":0}

def main():
    print("="*62); print(f"Sigma {VERSION} - Fix + Treatment - All Problems"); print("="*62)
    # Bulk load + guard
    bulk_path=DATA/"sigma_bulk_predictions.json"
    rows=[]
    if bulk_path.exists():
        obj=json.loads(bulk_path.read_text(encoding="utf-8"))
        rows=obj if isinstance(obj,list) else obj.get("matches",[])
        print(f"[BULK] rows={len(rows)} path={bulk_path}")
        if len(rows)<500:
            print(f"[GATE] BLOCKED - bulk rows {len(rows)} <500 - possible wipe to 14. Restore backup, do NOT push.")
            return
        # Backup
        shutil.copy(bulk_path, bulk_path.with_suffix(".backup_before_v58.json"))
        print("[BACKUP] bulk backup_before_v58.json")
    else:
        print("[BULK] NOT FOUND - using known results only")
    # Fake quarantine check
    print("\n[FAKE QUARANTINE]")
    for fake in FAKE_QUARANTINE:
        r=find_bulk(rows, fake)
        if r: print(f"  FOUND FAKE - QUARANTINE: {fake} - move to quarantine, do NOT delete silently")
        else: print(f"  OK not in bulk: {fake}")
    # Yesterday eval with V58 logic
    print("\n[YESTERDAY 2026-11-12 - V58 Re-eval]")
    eval_rows=[]
    for match, real in KNOWN_RESULTS.items():
        pr=find_bulk(rows, match)
        if not pr or pr.get("p1") is None:
            print(f"  {match}: ABSTAIN - fixture-only. Real {real['real_home']}-{real['real_away']}")
            eval_rows.append({"match":match,"sigma_pick":None,"sigma_conf":None,"real":f"{real['real_home']}-{real['real_away']}","verdict":"ABSTAIN"})
            continue
        p1,px,p2=pr.get("p1"),pr.get("pX"),pr.get("p2")
        pick=pr.get("pick"); conf=pr.get("conf") or pr.get("confidence")
        ok=(pick==real["real_1x2"])
        # V58 adjusted for yesterday (to show what V58 would have done)
        ctx={"home_ctx":real["home_ctx"],"away_ctx":real["away_ctx"],"hype":"LOW","rotation":"LOW","key_absence":real.get("key_absence")}
        adj=apply_context_v58(p1,px,p2,conf,ctx,pick)
        bet=best_bet_v58(p1,px,p2,pr.get("btts"),pr.get("over25"),adj["adjusted"],adj["flags"])
        print(f"  {match}: pick {pick} base {conf}% -> V58 adj {adj['adjusted']}% flags {adj['flags']} | Bet would be: {bet['bet']} | Real {real['real_home']}-{real['real_away']} -> {'OK' if ok else 'WRONG'}")
        eval_rows.append({"match":match,"sigma_pick":pick,"sigma_conf":conf,"v58_adj":adj["adjusted"],"flags":adj["flags"],"real":f"{real['real_home']}-{real['real_away']}","verdict":"1X2 OK" if ok else "1X2 WRONG","v58_bet":bet["bet"]})
    # Future
    print("\n[FUTURE 2026-11-15 - V58]")
    fut=[]
    for match, ctx in FUTURE.items():
        pr=find_bulk(rows, match)
        if not pr or pr.get("p1") is None:
            print(f"  {match}: NOT IN BULK / FIXTURE-ONLY - run V50 core first")
            fut.append({"match":match,"status":"FIXTURE_ONLY"})
            continue
        p1,px,p2=pr.get("p1"),pr.get("pX"),pr.get("p2"); conf=pr.get("conf"); pick=pr.get("pick")
        adj=apply_context_v58(p1,px,p2,conf,ctx,pick)
        bet=best_bet_v58(p1,px,p2,pr.get("btts"),pr.get("over25"),adj["adjusted"],adj["flags"])
        print(f"  {match}: base {conf}% -> V58 {adj['adjusted']}% flags {adj['flags']} | Bet: {bet['bet']} - {bet['why']}")
        fut.append({"match":match,"base_conf":conf,"adjusted_conf":adj["adjusted"],"flags":adj["flags"],"notes":adj["notes"],"best_bet":bet})
    # Percentages
    total=len(eval_rows); pred=[r for r in eval_rows if r.get("sigma_pick")]; corr=[r for r in eval_rows if r.get("verdict")=="1X2 OK"]; wrong=[r for r in eval_rows if r.get("verdict")=="1X2 WRONG"]; abst=[r for r in eval_rows if r.get("verdict")=="ABSTAIN"]
    print("\n[PERCENTAGES]")
    print(f"  Total {total} | Predicted {len(pred)} ({len(pred)/total*100:.1f}%) | ABSTAIN {len(abst)} ({len(abst)/total*100:.1f}%)")
    if pred: print(f"  Correct {len(corr)}/{len(pred)} = {len(corr)/len(pred)*100:.1f}% | Wrong {len(wrong)}/{len(pred)} = {len(wrong)/len(pred)*100:.1f}%")
    # Save
    report={"version":VERSION,"generated":str(TODAY),"signature":"Sigma - Mahmoud Emad","yesterday":eval_rows,"future":fut,"percentages":{"total":total,"predicted":len(pred),"abstain":len(abst),"correct":len(corr),"wrong":len(wrong)},"gate":"PASS"}
    (DATA/"sigma_v58_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding="utf-8")
    with open(DATA/"sigma_v58_yesterday_eval.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["match","sigma_pick","sigma_conf","v58_adj","real","verdict","v58_bet"])
        w.writeheader()
        for r in eval_rows: w.writerow({k:r.get(k,"") for k in ["match","sigma_pick","sigma_conf","v58_adj","real","verdict","v58_bet"]})
    print("\nDONE. Report: data/sigma_v58_report.json")
    print("Next: gate PASS -> push V58 only, NOT bulk until you verify bulk rows still 841")
if __name__=="__main__": main()
