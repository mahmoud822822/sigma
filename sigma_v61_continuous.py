#!/usr/bin/env python3
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# SIGMA V61 - 13-14 Nov 2026 - Same V60 logic, new matches
# Context from web (UEFA + AFCON): see notes below, no invented bulk numbers.
# 13 Nov A2: Netherlands vs Greece - both unbeaten, Greece win guarantees 1st + QF. Germany trails leaders by 3, Serbia trip is MUST_WIN for Germany.
# 13 Nov AFCON: Egypt vs Malawi - Egypt top Group B 4pts/2, level Angola ahead GD. Morocco vs Niger - Morocco perfect start Group A, double-header 13+17 Nov.
# 14 Nov A4: Portugal vs Denmark (Braga), Norway vs Wales (Oslo). 14 Nov AFCON: Algeria vs Togo Group I MD3.
# If bulk has no p1 -> ABSTAIN (fixture-only), NEVER invent.
import json, csv, re, shutil, unicodedata
from pathlib import Path
from datetime import date
BASE=Path(__file__).resolve().parent; DATA=BASE/"data"; DATA.mkdir(exist_ok=True)
VERSION="V61"; TODAY=date(2026,11,13)
MATCHES={
 "Netherlands vs Greece": {"date":"2026-11-13","league":"UEFA Nations League A2","home_ctx":"NEEDS_PTS","away_ctx":"MUST_WIN","hype":"MEDIUM","rotation":"LOW","note":"Both unbeaten. Greece win guarantees 1st + QF. Netherlands home."},
 "Serbia vs Germany": {"date":"2026-11-13","league":"UEFA Nations League A2","home_ctx":"NEEDS_PTS","away_ctx":"MUST_WIN","hype":"MEDIUM","rotation":"LOW","note":"Germany trails leaders by 3, trip to Serbia is MUST_WIN for Germany."},
 "Egypt vs Malawi": {"date":"2026-11-13","league":"AFCON Qualifiers Group B","home_ctx":"MUST_WIN","away_ctx":"NEEDS_PTS","hype":"HIGH_ON_EGYPT","rotation":"LOW","note":"Egypt top Group B 4pts/2, level Angola ahead GD. Home Cairo. New era after Hossam Hassan exit."},
 "Morocco vs Niger": {"date":"2026-11-13","league":"AFCON Qualifiers Group A","home_ctx":"MUST_WIN","away_ctx":"NEEDS_PTS","hype":"HIGH_ON_MOROCCO","rotation":"LOW","note":"Morocco perfect start Group A, double-header 13+17 Nov."},
 "Portugal vs Denmark": {"date":"2026-11-14","league":"UEFA Nations League A4","home_ctx":"MUST_WIN","away_ctx":"NEEDS_PTS","hype":"MEDIUM","rotation":"LOW","note":"A4 MD5 Braga. Portugal home, Denmark needs pts."},
 "Norway vs Wales": {"date":"2026-11-14","league":"UEFA Nations League A4","home_ctx":"MUST_WIN","away_ctx":"NEEDS_PTS","hype":"LOW","rotation":"LOW","note":"A4 MD5 Oslo."},
 "Algeria vs Togo": {"date":"2026-11-14","league":"AFCON Qualifiers Group I","home_ctx":"MUST_WIN","away_ctx":"NEEDS_PTS","hype":"MEDIUM","rotation":"LOW","note":"AFCON Qualifiers Group I MD3."},
}
SEVERE={"KEY_ABSENCE","ROTATION_RISK","HYPE_TRAP","OVERCONFIDENT_BASE","FAV_DEAD_RUBBER","MUSTWIN_VS_NEEDS1PT","BOTH_DEAD","MOTIVATION_MISMATCH"}
def norm(s):
    s=unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().lower()
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9 ]","",s)).strip()
def canon_team(t):
    t=norm(t); return "turkey" if t in ("turkiye","turkey") else t
def canon_match(m):
    if " vs " not in m: return norm(m)
    a,b=[canon_team(x) for x in m.split(" vs ",1)]; return f"{a} vs {b}"
def find_bulk(rows,match):
    want=canon_match(match)
    for r in rows:
        if canon_match(r.get("match",""))==want: return r
    return None
def apply_v60(base_conf,ctx,pick):
    flags=[]; notes=[]
    conf=min(85.0,float(base_conf)) if base_conf is not None else None
    if base_conf and float(base_conf)>85: flags.append("OVERCONFIDENT_BASE"); notes.append(f"Base {base_conf}% >85 cap")
    if conf is None: return {"adjusted":None,"flags":flags,"notes":notes}
    fav=ctx["home_ctx"] if pick=="1" else ctx["away_ctx"] if pick=="2" else "DRAW"
    opp=ctx["away_ctx"] if pick=="1" else ctx["home_ctx"] if pick=="2" else "DRAW"
    if fav=="NEEDS_1PT" and opp=="MUST_WIN": conf-=12; flags.append("MUSTWIN_VS_NEEDS1PT")
    if fav=="DEAD_RUBBER": conf-=10; flags.append("FAV_DEAD_RUBBER")
    if opp=="DEAD_RUBBER" and fav=="MUST_WIN": conf=min(85,conf+5); flags.append("OPP_DEAD_FAV_MUSTWIN_BONUS")
    if fav=="DEAD_RUBBER" and opp=="DEAD_RUBBER": conf-=10; flags.append("BOTH_DEAD")
    if (fav=="NEEDS_1PT" and opp=="DEAD_RUBBER") or (fav=="DEAD_RUBBER" and opp=="NEEDS_1PT"): conf-=8; flags.append("MOTIVATION_MISMATCH")
    if ctx.get("key_absence"): conf-=10; flags.append("KEY_ABSENCE")
    if ctx.get("rotation") in ("MEDIUM","HIGH"): conf-=8; flags.append("ROTATION_RISK")
    if ctx.get("hype") in ("HIGH","HIGH_ON_EGYPT","HIGH_ON_MOROCCO","HIGH_ON_FRANCE"): 
        pen=10 if float(base_conf or 0)>80 else 7; conf-=pen; flags.append("HYPE_TRAP")
    conf=max(30.0,min(85.0,conf)); return {"adjusted":round(conf,1),"flags":flags,"notes":notes}
def best_bet(p1,px,p2,btts,over,base_conf,adj,flags):
    severe=[f for f in flags if f in SEVERE]
    if adj is None: return {"bet":"NO SAFE BET","why":"No prediction","safety":0}
    if len(severe)>=2: return {"bet":"NO SAFE BET","why":f"{len(severe)} severe: {', '.join(severe)} - no market safe","safety":0}
    if adj<55: return {"bet":"NO SAFE BET","why":f"adj {adj} <55","safety":0}
    factor=adj/float(base_conf) if base_conf else 1
    btts_adj=round(btts*factor,1) if btts is not None else None; over_adj=round(over*factor,1) if over is not None else None
    if adj>=62 and btts_adj is not None and btts_adj>=65: return {"bet":"BTTS Yes","why":f"BTTS {btts}% -> adj {btts_adj}%","safety":7}
    if adj>=62 and over_adj is not None and over_adj>=65: return {"bet":"Over 2.5","why":f"Over {over}% -> adj {over_adj}%","safety":7}
    if adj>=62:
        pick="1" if p1>=px and p1>=p2 else "X" if px>=p2 else "2"; return {"bet":f"1X2 pick {pick}","why":f"adj {adj}%","safety":6}
    return {"bet":"NO SAFE BET","why":"No market passed","safety":0}
def main():
    print("="*62); print(f"Sigma {VERSION} - 13-14 Nov - V60 logic, no invented numbers"); print("="*62)
    bp=DATA/"sigma_bulk_predictions.json"; rows=[]
    if bp.exists():
        obj=json.loads(bp.read_text(encoding="utf-8")); rows=obj if isinstance(obj,list) else obj.get("matches",[])
        print(f"[BULK] rows={len(rows)}")
        if len(rows)<500: print(f"[GATE] BLOCKED bulk {len(rows)} <500"); return
        shutil.copy(bp,bp.with_suffix(".backup_before_v61.json")); print("[BACKUP] backup_before_v61.json")
    out=[]
    for match,ctx in MATCHES.items():
        pr=find_bulk(rows,match)
        if not pr or pr.get("p1") is None:
            print(f"  {match} ({ctx['date']}): ABSTAIN - fixture-only in Bulk. Context: {ctx['note']}")
            out.append({"match":match,"date":ctx["date"],"league":ctx["league"],"status":"ABSTAIN","context":ctx["note"]}); continue
        p1,px,p2=pr.get("p1"),pr.get("pX"),pr.get("p2"); conf=pr.get("conf"); pick=pr.get("pick")
        adj=apply_v60(conf,ctx,pick); bet=best_bet(p1,px,p2,pr.get("btts"),pr.get("over25"),conf,adj["adjusted"],adj["flags"])
        print(f"  {match} ({ctx['date']}): base {conf}% -> V61 {adj['adjusted']}% flags {adj['flags']} | Bet: {bet['bet']} - {bet['why']} | {ctx['note']}")
        out.append({"match":match,"date":ctx["date"],"league":ctx["league"],"base_conf":conf,"adjusted_conf":adj["adjusted"],"flags":adj["flags"],"best_bet":bet,"context":ctx["note"]})
    (DATA/"sigma_v61_report.json").write_text(json.dumps({"version":VERSION,"generated":str(TODAY),"signature":"Sigma - Mahmoud Emad","matches":out,"gate":"PASS"},ensure_ascii=False,indent=1),encoding="utf-8")
    with open(DATA/"sigma_v61_1314_eval.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["match","date","base_conf","adjusted_conf","flags","best_bet"]); w.writeheader()
        for r in out: w.writerow({"match":r["match"],"date":r["date"],"base_conf":r.get("base_conf",""),"adjusted_conf":r.get("adjusted_conf",""),"flags":",".join(r.get("flags",[])),"best_bet":r.get("best_bet",{}).get("bet") if isinstance(r.get("best_bet"),dict) else r.get("status","")})
    print("\nDONE. Report: data/sigma_v61_report.json")
if __name__=="__main__": main()
