#!/usr/bin/env python3
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# SIGMA V62 - Fix HIGH CONFIDENCE TRAP found in V61 screenshot
# Problem in V61 screenshot:
#  Norway vs Wales: base 82.0 -> adj 82.0 flags [] Bet 1X2 pick 1 safety 6
#  Algeria vs Togo: base 87.9 -> adj 85.0 flags [OVERCONFIDENT_BASE] Bet 1X2 pick 1 safety 6
# Both are 82-85% with 0-1 flags - same pattern as France vs Turkey 87.9% that was wrong.
# Also 87.9 appears in France vs Turkey AND Algeria vs Togo - duplicate base suspect.
# Fix:
#  1. HIGH_CONF_GATE: if adj >=80 -> NO SAFE BET - NEED LINEUP CHECK (rotation / key absence unknown)
#     Unless user confirms lineup: no rotation, no key absence, hype LOW.
#  2. DUPLICATE_BASE_CHECK: if same base_conf repeats 3+ times in report -> flag DUPLICATE_BASE_SUSPECT
#  3. Cap effective 1X2 confidence for display: adj capped 85, but safe bet needs adj 62-79, not 80+
import json, csv, re, shutil, unicodedata, collections
from pathlib import Path
from datetime import date
BASE=Path(__file__).resolve().parent; DATA=BASE/"data"; DATA.mkdir(exist_ok=True)
VERSION="V62"; TODAY=date(2026,11,13)
MATCHES={
 "Netherlands vs Greece": {"date":"2026-11-13","league":"UEFA Nations League A2","home_ctx":"NEEDS_PTS","away_ctx":"MUST_WIN","hype":"MEDIUM","rotation":"LOW","note":"Both unbeaten. Greece win guarantees 1st + QF."},
 "Serbia vs Germany": {"date":"2026-11-13","league":"UEFA Nations League A2","home_ctx":"NEEDS_PTS","away_ctx":"MUST_WIN","hype":"MEDIUM","rotation":"LOW","note":"Germany trails by 3, MUST_WIN."},
 "Egypt vs Malawi": {"date":"2026-11-13","league":"AFCON Qualifiers Group B","home_ctx":"MUST_WIN","away_ctx":"NEEDS_PTS","hype":"HIGH_ON_EGYPT","rotation":"LOW","note":"Egypt top Group B 4pts/2."},
 "Morocco vs Niger": {"date":"2026-11-13","league":"AFCON Qualifiers Group A","home_ctx":"MUST_WIN","away_ctx":"NEEDS_PTS","hype":"HIGH_ON_MOROCCO","rotation":"LOW","note":"Morocco perfect start Group A."},
 "Portugal vs Denmark": {"date":"2026-11-14","league":"UEFA Nations League A4","home_ctx":"MUST_WIN","away_ctx":"NEEDS_PTS","hype":"MEDIUM","rotation":"LOW","note":"A4 MD5 Braga."},
 "Norway vs Wales": {"date":"2026-11-14","league":"UEFA Nations League A4","home_ctx":"MUST_WIN","away_ctx":"NEEDS_PTS","hype":"LOW","rotation":"LOW","note":"A4 MD5 Oslo."},
 "Algeria vs Togo": {"date":"2026-11-14","league":"AFCON Qualifiers Group I","home_ctx":"MUST_WIN","away_ctx":"NEEDS_PTS","hype":"MEDIUM","rotation":"LOW","note":"AFCON Group I MD3."},
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
def apply_v62(base_conf,ctx,pick):
    flags=[]; conf=min(85.0,float(base_conf)) if base_conf is not None else None
    if base_conf and float(base_conf)>85: flags.append("OVERCONFIDENT_BASE")
    if conf is None: return {"adjusted":None,"flags":flags}
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
    conf=max(30.0,min(85.0,conf)); return {"adjusted":round(conf,1),"flags":flags}
def best_bet_v62(p1,px,p2,btts,over,base_conf,adj,flags):
    severe=[f for f in flags if f in SEVERE]
    if adj is None: return {"bet":"NO SAFE BET","why":"No prediction","safety":0}
    if len(severe)>=2: return {"bet":"NO SAFE BET","why":f"{len(severe)} severe: {', '.join(severe)} - no market safe","safety":0}
    # NEW V62 HIGH CONF GATE
    if adj>=80: return {"bet":"NO SAFE BET","why":f"HIGH CONF GATE - adj {adj}% >=80 needs lineup check (rotation / key absence unknown) - same trap as France 87.9%","safety":0}
    if adj<55: return {"bet":"NO SAFE BET","why":f"adj {adj} <55","safety":0}
    factor=adj/float(base_conf) if base_conf else 1
    btts_adj=round(btts*factor,1) if btts is not None else None; over_adj=round(over*factor,1) if over is not None else None
    if adj>=62 and btts_adj is not None and btts_adj>=65: return {"bet":"BTTS Yes","why":f"BTTS {btts}% -> adj {btts_adj}%","safety":7}
    if adj>=62 and over_adj is not None and over_adj>=65: return {"bet":"Over 2.5","why":f"Over {over}% -> adj {over_adj}%","safety":7}
    if adj>=62:
        pick="1" if p1>=px and p1>=p2 else "X" if px>=p2 else "2"; return {"bet":f"1X2 pick {pick}","why":f"adj {adj}% (safe range 62-79)","safety":6}
    return {"bet":"NO SAFE BET","why":"No market passed","safety":0}
def main():
    print("="*62); print(f"Sigma {VERSION} - Fix HIGH CONF TRAP (Norway 82% / Algeria 85% in V61)"); print("="*62)
    bp=DATA/"sigma_bulk_predictions.json"; rows=[]
    if bp.exists():
        obj=json.loads(bp.read_text(encoding="utf-8")); rows=obj if isinstance(obj,list) else obj.get("matches",[])
        print(f"[BULK] rows={len(rows)}")
        if len(rows)<500: print(f"[GATE] BLOCKED {len(rows)}"); return
        shutil.copy(bp,bp.with_suffix(".backup_before_v62.json")); print("[BACKUP] backup_before_v62.json")
    out=[]
    for match,ctx in MATCHES.items():
        pr=find_bulk(rows,match)
        if not pr or pr.get("p1") is None:
            print(f"  {match}: ABSTAIN - fixture-only"); out.append({"match":match,"date":ctx["date"],"status":"ABSTAIN"}); continue
        p1,px,p2=pr.get("p1"),pr.get("pX"),pr.get("p2"); conf=pr.get("conf"); pick=pr.get("pick")
        adj=apply_v62(conf,ctx,pick); bet=best_bet_v62(p1,px,p2,pr.get("btts"),pr.get("over25"),conf,adj["adjusted"],adj["flags"])
        print(f"  {match}: base {conf}% -> V62 {adj['adjusted']}% flags {adj['flags']} | Bet: {bet['bet']} - {bet['why']}")
        out.append({"match":match,"date":ctx["date"],"league":ctx["league"],"base_conf":conf,"adjusted_conf":adj["adjusted"],"flags":adj["flags"],"best_bet":bet})
    # Duplicate base check
    bases=[r["base_conf"] for r in out if "base_conf" in r]; dup=[k for k,c in collections.Counter(bases).items() if c>=2]
    if dup: print(f"\n[DUPLICATE_BASE_SUSPECT] Same base_conf repeats: {dup} - check V50 Elo calc, may be default value")
    else: print("\n[DUPLICATE_BASE] OK - no duplicate base")
    (DATA/"sigma_v62_report.json").write_text(json.dumps({"version":VERSION,"generated":str(TODAY),"signature":"Sigma - Mahmoud Emad","matches":out,"duplicate_base":dup,"gate":"PASS"},ensure_ascii=False,indent=1),encoding="utf-8")
    print("\nDONE. Report: data/sigma_v62_report.json")
if __name__=="__main__": main()
