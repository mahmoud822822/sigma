#!/usr/bin/env python3
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# SIGMA V64 - Close Loop 12 Nov (CONFIRMED) + 13-14 Nov (WAITING)
# Fix V63 gap: V63 only looked at 13-14 Nov and left 12 Nov open.
# 12 Nov results are CONFIRMED from user's Termux screenshots V58/V60 eval:
#  Turkiye vs Belgium 1-2, Italy vs France 3-1, Czechia vs Spain 0-2, England vs Croatia 2-1
# 13-14 Nov are still SCHEDULED (verified via web search 13 Nov afternoon) -> stay null, NO INVENTED DATA.
import json, re, shutil, unicodedata
from pathlib import Path
from datetime import date
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
VERSION = "V64"
TODAY = date(2026, 11, 13)
# 12 Nov - V60 predictions (from Termux screenshots)
PRED_12 = {
    "Turkiye vs Belgium": {"date":"2026-11-12","base":80.1,"adj":85.0,"pick":"2","bet":"1X2 pick 2","flags":["OPP_DEAD_FAV_MUSTWIN_BONUS"]},
    "Italy vs France": {"date":"2026-11-12","base":53.4,"adj":31.4,"pick":"2","bet":"NO SAFE BET","flags":["MUSTWIN_VS_NEEDS1PT","KEY_ABSENCE"]},
    "Czechia vs Spain": {"date":"2026-11-12","base":None,"adj":None,"pick":None,"bet":"ABSTAIN - fixture-only","flags":[]},
    "England vs Croatia": {"date":"2026-11-12","base":None,"adj":None,"pick":None,"bet":"ABSTAIN - fixture-only","flags":[]},
}
# 13-14 Nov - V62 predictions (from Termux V62 run)
PRED_1314 = {
    "Netherlands vs Greece": {"date":"2026-11-13","base":68.5,"adj":68.5,"pick":"1","bet":"1X2 pick 1","flags":[]},
    "Serbia vs Germany": {"date":"2026-11-13","base":71.2,"adj":71.2,"pick":"2","bet":"1X2 pick 2","flags":[]},
    "Egypt vs Malawi": {"date":"2026-11-13","base":71.7,"adj":64.7,"pick":"1","bet":"1X2 pick 1","flags":["HYPE_TRAP"]},
    "Morocco vs Niger": {"date":"2026-11-13","base":94.3,"adj":75.0,"pick":"1","bet":"NO SAFE BET","flags":["OVERCONFIDENT_BASE","HYPE_TRAP"]},
    "Portugal vs Denmark": {"date":"2026-11-14","base":72.4,"adj":72.4,"pick":"1","bet":"1X2 pick 1","flags":[]},
    "Norway vs Wales": {"date":"2026-11-14","base":82.0,"adj":82.0,"pick":"1","bet":"NO SAFE BET","flags":["HIGH_CONF_GATE"]},
    "Algeria vs Togo": {"date":"2026-11-14","base":87.9,"adj":85.0,"pick":"1","bet":"NO SAFE BET","flags":["OVERCONFIDENT_BASE","HIGH_CONF_GATE"]},
}
ALL_PRED = {**PRED_12, **PRED_1314}
# Confirmed 12 Nov real scores - DO NOT CHANGE, from V58/V60 Termux eval
CONFIRMED_12 = {
    "Turkiye vs Belgium": {"real_home":1,"real_away":2,"source":"CONFIRMED Termux V58/V60 eval 12 Nov - Real 1-2"},
    "Italy vs France": {"real_home":3,"real_away":1,"source":"CONFIRMED Termux V58/V60 eval 12 Nov - Real 3-1"},
    "Czechia vs Spain": {"real_home":0,"real_away":2,"source":"CONFIRMED Termux V58 eval 12 Nov - Real 0-2 - fixture-only, not in Bulk"},
    "England vs Croatia": {"real_home":2,"real_away":1,"source":"CONFIRMED Termux V58 eval 12 Nov - Real 2-1 - fixture-only, not in Bulk"},
}
def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii","ignore").decode().lower()
    return re.sub(r"\s+"," ", re.sub(r"[^a-z0-9 ]","",s)).strip()
def canon_team(t):
    t=norm(t)
    return "turkey" if t in ("turkiye","turkey") else t
def find_bulk(rows, match):
    want=norm(match)
    try: wh,wa=[canon_team(x) for x in match.split(" vs ",1)]
    except: return None
    for r in rows:
        m=r.get("match","")
        if norm(m)==want: return r
        if " vs " in m:
            mh,ma=[canon_team(x) for x in m.split(" vs ",1)]
            if mh==wh and ma==wa: return r
    return None
def real_1x2(h,a):
    if h is None or a is None: return None
    return "1" if h>a else "2" if a>h else "X"
def elo_update(eh,ea,sh):
    exp_h=1/(1+10**((ea-eh)/400)); exp_a=1-exp_h
    return round(eh+20*(sh-exp_h),1), round(ea+20*((1-sh)-exp_a),1)
def main():
    print("="*62); print(f"Sigma {VERSION} - Close 12 Nov CONFIRMED + 13-14 Nov WAITING"); print("="*62)
    bulk_path=DATA/"sigma_bulk_predictions.json"
    rows=[]
    if bulk_path.exists():
        obj=json.loads(bulk_path.read_text(encoding="utf-8"))
        rows=obj if isinstance(obj,list) else obj.get("matches",[])
        print(f"[BULK] rows={len(rows)}")
        if len(rows)<500:
            print(f"[GATE] BLOCKED - bulk {len(rows)} <500"); return
        shutil.copy(bulk_path, bulk_path.with_suffix(".backup_before_v64.json"))
        print("[BACKUP] backup_before_v64.json")
    confs=[r.get("conf") for r in rows if r.get("conf") is not None]
    dup87=sum(1 for c in confs if c is not None and abs(float(c)-87.9)<0.01)
    print(f"[V50 CHECK] OK - 87.9 appears {dup87} time(s)" if dup87<3 else f"[V50 CHECK] WARNING DUPLICATE 87.9 x{dup87}")
    res_path=DATA/"sigma_v64_results.json"
    if not res_path.exists():
        template={}
        for m in ALL_PRED:
            if m in CONFIRMED_12: template[m]=dict(CONFIRMED_12[m])
            else: template[m]={"real_home":None,"real_away":None,"source":"13-14 Nov still SCHEDULED 13 Nov afternoon - DO NOT invent - fill after FT"}
        res_path.write_text(json.dumps(template,ensure_ascii=False,indent=1),encoding="utf-8")
        print(f"\n[RESULTS] NOT FOUND - created {res_path} with 12 Nov CONFIRMED + 13-14 WAITING")
    results=json.loads(res_path.read_text(encoding="utf-8"))
    # Ensure 12 Nov confirmed are present even if user edited file
    for m,v in CONFIRMED_12.items():
        if results.get(m,{}).get("real_home") is None:
            print(f"[FIX] {m} was null in file, restoring CONFIRMED {v['real_home']}-{v['real_away']}")
            results[m]=dict(v)
    print(f"[RESULTS] loaded {len(results)} entries")
    evaluated=[]; remaining=list(rows); moved=[]
    for match,pred in ALL_PRED.items():
        r=results.get(match,{})
        rh,ra=r.get("real_home"), r.get("real_away")
        if rh is None or ra is None:
            print(f"  {match}: ABSTAIN - NO CONFIRMED DATA yet - V bet was {pred['bet']}")
            evaluated.append({"match":match,"date":pred["date"],"pred_pick":pred["pick"],"pred_adj":pred["adj"],"pred_bet":pred["bet"],"real":None,"verdict":"ABSTAIN - NO CONFIRMED DATA"})
            continue
        real=real_1x2(rh,ra)
        if pred["bet"]=="NO SAFE BET":
            verdict="NO_SAFE_BET - correctly abstained"
            print(f"  {match}: V bet NO SAFE BET - Real {rh}-{ra} ({real}) -> {verdict} - NOT counted wrong")
        elif pred["bet"].startswith("ABSTAIN"):
            verdict="ABSTAIN - fixture-only in Bulk, not counted"
            print(f"  {match}: ABSTAIN fixture-only - Real {rh}-{ra} ({real}) -> {verdict}")
        else:
            verdict="1X2 OK" if pred["pick"]==real else "1X2 WRONG"
            print(f"  {match}: pick {pred['pick']} adj {pred['adj']}% - Real {rh}-{ra} ({real}) -> {verdict}")
        br=find_bulk(rows, match)
        if br is not None and verdict in ("1X2 OK","1X2 WRONG","NO_SAFE_BET - correctly abstained"):
            eh=float(br.get("elo_home",1500)); ea=float(br.get("elo_away",1500))
            if eh==1500 or ea==1500: print(f"    [ELO] WARNING default 1500 for {match}")
            sh=1 if real=="1" else 0 if real=="2" else 0.5
            nh,na=elo_update(eh,ea,sh)
            evaluated.append({"match":match,"date":pred["date"],"pred_pick":pred["pick"],"pred_adj":pred["adj"],"pred_bet":pred["bet"],"real":f"{rh}-{ra}","real_1x2":real,"verdict":verdict,"elo_home_before":eh,"elo_home_after":nh,"elo_away_before":ea,"elo_away_after":na})
            if br in remaining: remaining.remove(br)
            moved.append({"match":match,"date":pred["date"],"real_home":rh,"real_away":ra,"elo_home_after":nh,"elo_away_after":na})
        else:
            evaluated.append({"match":match,"date":pred["date"],"pred_pick":pred["pick"],"pred_adj":pred["adj"],"pred_bet":pred["bet"],"real":f"{rh}-{ra}","real_1x2":real,"verdict":verdict})
    total=len(evaluated)
    counted=[e for e in evaluated if e["verdict"] in ("1X2 OK","1X2 WRONG")]
    corr=[e for e in evaluated if e["verdict"]=="1X2 OK"]
    wrong=[e for e in evaluated if e["verdict"]=="1X2 WRONG"]
    abst=[e for e in evaluated if "ABSTAIN" in e["verdict"]]
    nsb=[e for e in evaluated if "NO_SAFE_BET" in e["verdict"]]
    print(f"\n[PERCENTAGES] Total {total} | Counted {len(counted)} | NO_SAFE_BET {len(nsb)} | ABSTAIN {len(abst)}")
    if counted: print(f"  Correct {len(corr)}/{len(counted)} = {len(corr)/len(counted)*100:.1f}% | Wrong {len(wrong)}/{len(counted)}")
    # Split: 12 Nov vs 13-14
    ev12=[e for e in evaluated if e["date"]=="2026-11-12"]
    ev1314=[e for e in evaluated if e["date"] in ("2026-11-13","2026-11-14")]
    c12=[e for e in ev12 if e["verdict"] in ("1X2 OK","1X2 WRONG")]
    print(f"[12 NOV] Total 4 | Counted {len(c12)} | Correct {sum(1 for e in c12 if e['verdict']=='1X2 OK')} | NO_SAFE_BET {sum(1 for e in ev12 if 'NO_SAFE_BET' in e['verdict'])} | ABSTAIN-fixture {sum(1 for e in ev12 if 'fixture-only' in e['verdict'])}")
    print(f"[13-14 NOV] Total 7 | ABSTAIN {sum(1 for e in ev1314 if 'ABSTAIN' in e['verdict'])} | Waiting for FT")
    (DATA/"sigma_bulk_v64.json").write_text(json.dumps(remaining,ensure_ascii=False,indent=1),encoding="utf-8")
    print(f"[BULK V64] remaining {len(remaining)} (was {len(rows)}, moved {len(moved)}) -> data/sigma_bulk_v64.json")
    if moved:
        hp=DATA/"sigma_history_new_v64.jsonl"
        with open(hp,"a",encoding="utf-8") as f:
            for m in moved: f.write(json.dumps(m,ensure_ascii=False)+"\n")
        print(f"[HISTORY] appended {len(moved)} -> {hp}")
    report={"version":VERSION,"generated":str(TODAY),"signature":"Sigma - Mahmoud Emad","gate":"PASS","evaluated":evaluated,"percentages":{"total":total,"counted":len(counted),"correct":len(corr),"wrong":len(wrong),"abstain":len(abst),"no_safe_bet":len(nsb)},"bulk_before":len(rows),"bulk_after":len(remaining),"moved":len(moved)}
    (DATA/"sigma_v64_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding="utf-8")
    print("DONE. Report: data/sigma_v64_report.json")
if __name__=="__main__": main()
