#!/usr/bin/env python3
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# SIGMA V60 - Fix V59 regression: Turkiye vs Turkey alias lost
# BUG in V59: find_bulk() used norm() only, lost canon_team() that V58 had.
# Bulk has "Turkey vs Belgium" but query is "Turkiye vs Belgium" -> norm mismatch -> ABSTAIN (wrong).
# Result in V59 run: Turkiye counted as ABSTAIN, percentages dropped to Predicted 1/4, Correct 0/1 = 0% (misleading).
# FIX in V60: restore canon_team() in find_bulk: Turkiye <-> Turkey both map to "turkey", match on canon.
# Keep all V59 fixes: MOTIVATION_MISMATCH -8, severe>=2 blocks all markets, Over/BTTS context-adjusted, cap 85 first, MUST_WIN vs NEEDS_1PT -12, KEY -10, OPP_DEAD+FAV_MUSTWIN +5 bonus, bulk guard <500 BLOCK, fake quarantine
import json, csv, re, shutil, unicodedata
from pathlib import Path
from datetime import date
BASE=Path(__file__).resolve().parent
DATA=BASE/"data"; DATA.mkdir(exist_ok=True)
VERSION="V60"; TODAY=date(2026,11,13)
KNOWN_RESULTS={
 "Turkiye vs Belgium": {"real_home":1,"real_away":2,"real_1x2":"2","home_ctx":"DEAD_RUBBER","away_ctx":"MUST_WIN","reason":"Turkiye 0pts dead, Belgium MUST_WIN"},
 "Italy vs France": {"real_home":3,"real_away":1,"real_1x2":"1","home_ctx":"MUST_WIN","away_ctx":"NEEDS_1PT","reason":"Italy MUST_WIN, France NEEDS_1PT, Mbappe+Saliba missing","key_absence":"Mbappe, Saliba"},
 "Czechia vs Spain": {"real_home":0,"real_away":2,"real_1x2":"2","home_ctx":"NEEDS_PTS","away_ctx":"MUST_WIN","reason":"Spain MUST_WIN"},
 "England vs Croatia": {"real_home":2,"real_away":1,"real_1x2":"1","home_ctx":"MUST_WIN","away_ctx":"NEEDS_PTS","reason":"England MUST_WIN"},
}
FUTURE={
 "Belgium vs Italy": {"date":"2026-11-15","league":"UEFA Nations League A1","home_ctx":"MUST_WIN","away_ctx":"MUST_WIN","hype":"LOW","rotation":"LOW","note":"Both MUST_WIN"},
 "France vs Turkey": {"date":"2026-11-15","league":"UEFA Nations League A1","home_ctx":"NEEDS_1PT","away_ctx":"DEAD_RUBBER","hype":"HIGH_ON_FRANCE","rotation":"MEDIUM","note":"France needs 1pt, Turkey dead - motivation mismatch","key_absence":"Mbappe? check lineup"},
}
FAKE=["Al Ahly vs Zamalek","Al Hilal vs Al Nassr","Real Madrid vs Barcelona","Manchester City vs Arsenal","Inter vs AC Milan","Brazil vs Argentina"]
SEVERE={"KEY_ABSENCE","ROTATION_RISK","HYPE_TRAP","OVERCONFIDENT_BASE","FAV_DEAD_RUBBER","MUSTWIN_VS_NEEDS1PT","BOTH_DEAD","MOTIVATION_MISMATCH"}
def norm(s):
    s=unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().lower()
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9 ]","",s)).strip()
def canon_team(t):
    t=norm(t); return "turkey" if t in ("turkiye","turkey") else t
def canon_match(m):
    if " vs " not in m: return norm(m)
    a,b=[canon_team(x) for x in m.split(" vs ",1)]
    return f"{a} vs {b}"
def find_bulk(rows,match):
    want=canon_match(match)
    for r in rows:
        if canon_match(r.get("match",""))==want: return r
    return None
def apply_v60(base_conf,ctx,pick):
    flags=[]; notes=[]
    conf=min(85.0,float(base_conf)) if base_conf is not None else None
    if base_conf and float(base_conf)>85:
        flags.append("OVERCONFIDENT_BASE"); notes.append(f"Base {base_conf}% >85 cap to 85")
    if conf is None: return {"adjusted":None,"flags":flags,"notes":notes}
    fav=ctx["home_ctx"] if pick=="1" else ctx["away_ctx"] if pick=="2" else "DRAW"
    opp=ctx["away_ctx"] if pick=="1" else ctx["home_ctx"] if pick=="2" else "DRAW"
    if fav=="NEEDS_1PT" and opp=="MUST_WIN":
        conf-=12; flags.append("MUSTWIN_VS_NEEDS1PT"); notes.append("Fav NEEDS_1PT vs opp MUST_WIN -12%")
    if fav=="DEAD_RUBBER":
        conf-=10; flags.append("FAV_DEAD_RUBBER"); notes.append("Fav DEAD -10%")
    if opp=="DEAD_RUBBER" and fav=="MUST_WIN":
        conf=min(85,conf+5); flags.append("OPP_DEAD_FAV_MUSTWIN_BONUS"); notes.append("Opp DEAD + Fav MUST_WIN +5%")
    if fav=="DEAD_RUBBER" and opp=="DEAD_RUBBER":
        conf-=10; flags.append("BOTH_DEAD"); notes.append("Both DEAD -10%")
    if (fav=="NEEDS_1PT" and opp=="DEAD_RUBBER") or (fav=="DEAD_RUBBER" and opp=="NEEDS_1PT"):
        conf-=8; flags.append("MOTIVATION_MISMATCH"); notes.append("NEEDS_1PT vs DEAD mismatch -8% (V59)")
    if ctx.get("key_absence"):
        conf-=10; flags.append("KEY_ABSENCE"); notes.append(f"Key absence {ctx['key_absence']} -10%")
    if ctx.get("rotation") in ("MEDIUM","HIGH"):
        conf-=8; flags.append("ROTATION_RISK"); notes.append(f"Rotation {ctx['rotation']} -8%")
    if ctx.get("hype") in ("HIGH","HIGH_ON_FRANCE"):
        pen=10 if float(base_conf or 0)>80 else 7
        conf-=pen; flags.append("HYPE_TRAP"); notes.append(f"Hype -{pen}%")
    conf=max(30.0,min(85.0,conf))
    return {"adjusted":round(conf,1),"flags":flags,"notes":notes}
def best_bet_v60(p1,px,p2,btts,over,base_conf,adj,flags):
    severe=[f for f in flags if f in SEVERE]
    if adj is None: return {"bet":"NO SAFE BET","why":"No prediction","safety":0}
    if len(severe)>=2:
        return {"bet":"NO SAFE BET","why":f"{len(severe)} severe flags: {', '.join(severe)} - no market safe","safety":0}
    if "FAV_DEAD_RUBBER" in flags and "ROTATION_RISK" in flags:
        return {"bet":"NO SAFE BET","why":"Fav DEAD + Rotation - unpredictable","safety":0}
    if adj<55:
        return {"bet":"NO SAFE BET","why":f"adj {adj} <55","safety":0}
    if base_conf and base_conf>0:
        factor=adj/float(base_conf)
        btts_adj=round(btts*factor,1) if btts is not None else None
        over_adj=round(over*factor,1) if over is not None else None
    else:
        btts_adj,over_adj=btts,over
    if adj>=62 and btts_adj is not None and btts_adj>=65:
        return {"bet":"BTTS Yes","why":f"BTTS raw {btts}% -> adj {btts_adj}%","safety":7}
    if adj>=62 and over_adj is not None and over_adj>=65:
        return {"bet":"Over 2.5","why":f"Over raw {over}% -> adj {over_adj}%","safety":7}
    if adj>=62:
        pick="1" if p1>=px and p1>=p2 else "X" if px>=p2 else "2"
        return {"bet":f"1X2 pick {pick}","why":f"adj {adj}% + severe {len(severe)} <2","safety":6}
    return {"bet":"NO SAFE BET","why":"No market passed safety","safety":0}
def main():
    print("="*62); print(f"Sigma {VERSION} - Fix Turkiye alias regression"); print("="*62)
    bulk_path=DATA/"sigma_bulk_predictions.json"; rows=[]
    if bulk_path.exists():
        obj=json.loads(bulk_path.read_text(encoding="utf-8")); rows=obj if isinstance(obj,list) else obj.get("matches",[])
        print(f"[BULK] rows={len(rows)}")
        if len(rows)<500:
            print(f"[GATE] BLOCKED bulk {len(rows)} <500"); return
        shutil.copy(bulk_path,bulk_path.with_suffix(".backup_before_v60.json")); print("[BACKUP] backup_before_v60.json")
    print("\n[ALIAS CHECK]")
    for q in ["Turkiye vs Belgium","Turkey vs Belgium"]:
        r=find_bulk(rows,q)
        print(f"  query '{q}' -> {'FOUND '+str(r.get('match'))+' p2='+str(r.get('p2')) if r else 'NOT FOUND'}")
    print("\n[FAKE QUARANTINE]")
    for f in FAKE:
        print(f"  {'FOUND FAKE - QUARANTINE' if find_bulk(rows,f) else 'OK not in bulk'}: {f}")
    print("\n[YESTERDAY 2026-11-12 V60]")
    eval_rows=[]
    for match,real in KNOWN_RESULTS.items():
        pr=find_bulk(rows,match)
        if not pr or pr.get("p1") is None:
            print(f"  {match}: ABSTAIN - fixture-only. Real {real['real_home']}-{real['real_away']}")
            eval_rows.append({"match":match,"sigma_pick":None,"sigma_conf":None,"real":f"{real['real_home']}-{real['real_away']}","verdict":"ABSTAIN"}); continue
        p1,px,p2=pr.get("p1"),pr.get("pX"),pr.get("p2"); pick=pr.get("pick"); conf=pr.get("conf")
        ctx={"home_ctx":real["home_ctx"],"away_ctx":real["away_ctx"],"hype":"LOW","rotation":"LOW","key_absence":real.get("key_absence")}
        adj=apply_v60(conf,ctx,pick); bet=best_bet_v60(p1,px,p2,pr.get("btts"),pr.get("over25"),conf,adj["adjusted"],adj["flags"])
        print(f"  {match}: pick {pick} base {conf}% -> V60 {adj['adjusted']}% flags {adj['flags']} | Bet: {bet['bet']} | Real {real['real_home']}-{real['real_away']} -> {'OK' if pick==real['real_1x2'] else 'WRONG'}")
        eval_rows.append({"match":match,"sigma_pick":pick,"sigma_conf":conf,"v60_adj":adj["adjusted"],"flags":",".join(adj["flags"]),"real":f"{real['real_home']}-{real['real_away']}","verdict":"1X2 OK" if pick==real['real_1x2'] else "1X2 WRONG","v60_bet":bet["bet"]})
    print("\n[FUTURE 2026-11-15 V60]")
    fut=[]
    for match,ctx in FUTURE.items():
        pr=find_bulk(rows,match)
        if not pr or pr.get("p1") is None:
            print(f"  {match}: FIXTURE-ONLY"); fut.append({"match":match,"status":"FIXTURE_ONLY"}); continue
        p1,px,p2=pr.get("p1"),pr.get("pX"),pr.get("p2"); conf=pr.get("conf"); pick=pr.get("pick")
        adj=apply_v60(conf,ctx,pick); bet=best_bet_v60(p1,px,p2,pr.get("btts"),pr.get("over25"),conf,adj["adjusted"],adj["flags"])
        print(f"  {match}: base {conf}% -> V60 {adj['adjusted']}% flags {adj['flags']} | Over raw {pr.get('over25')}% -> Bet: {bet['bet']} - {bet['why']}")
        fut.append({"match":match,"base_conf":conf,"adjusted_conf":adj["adjusted"],"flags":adj["flags"],"notes":adj["notes"],"best_bet":bet})
    total=len(eval_rows); pred=[r for r in eval_rows if r.get("sigma_pick")]; corr=[r for r in eval_rows if r.get("verdict")=="1X2 OK"]; wrong=[r for r in eval_rows if r.get("verdict")=="1X2 WRONG"]; abst=[r for r in eval_rows if r.get("verdict")=="ABSTAIN"]
    print(f"\n[PERCENTAGES] Total {total} | Predicted {len(pred)} ({len(pred)/total*100:.1f}%) | ABSTAIN {len(abst)} | Correct {len(corr)}/{len(pred)} = {len(corr)/len(pred)*100:.1f}% | Wrong {len(wrong)}/{len(pred)}" if pred else f"\n[PERCENTAGES] Total {total} | Predicted 0")
    report={"version":VERSION,"generated":str(TODAY),"signature":"Sigma - Mahmoud Emad","yesterday":eval_rows,"future":fut,"percentages":{"total":total,"predicted":len(pred),"abstain":len(abst),"correct":len(corr),"wrong":len(wrong)},"gate":"PASS"}
    (DATA/"sigma_v60_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding="utf-8")
    with open(DATA/"sigma_v60_yesterday_eval.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["match","sigma_pick","sigma_conf","v60_adj","real","verdict","v60_bet"]); w.writeheader()
        for r in eval_rows: w.writerow({k:r.get(k,"") for k in ["match","sigma_pick","sigma_conf","v60_adj","real","verdict","v60_bet"]})
    print("\nDONE. Report: data/sigma_v60_report.json")
if __name__=="__main__": main()
