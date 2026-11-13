#!/usr/bin/env python3
# Sigma V70 - BACKTEST + CALIBRATION + HYPE_TRAP RULE (item 4) - Continue after V69
# V69 fixed: 87.9->NO DATA, Elo 1500->NO DATA, base>=90 -> NO SAFE BET, Bulk gate.
# V70 answers: HYPE_TRAP cancels entirely or only reduces confidence?
# RULE V70 (final):
#  HYPE_TRAP alone -> reduce confidence by 7 points, KEEP bet if adj >=60 and no other flag.
#  HYPE_TRAP + ANY other flag (OVERCONFIDENT / HIGH_CONF_GATE / NO_DATA) -> CANCEL to NO SAFE BET.
#  This matches: Egypt (HYPE alone, 71.7->64.7 kept) vs Morocco (HYPE+OVERCONFIDENT -> NO SAFE BET)
# BACKTEST: reads data/sigma_bulk_predictions.json + data/sigma_history*.jsonl if present.
# If no confirmed history -> prints NO CONFIRMED DATA / ABSTAIN, never invents results.
import json, pathlib
from datetime import date
BASE=pathlib.Path(__file__).resolve().parent; DATA=BASE/"data"; DATA.mkdir(exist_ok=True)
VERSION="V70"; TODAY=str(date(2026,11,13))
def load_bulk():
    p=DATA/"sigma_bulk_predictions.json"
    if not p.exists(): return []
    o=json.loads(p.read_text(encoding="utf-8")); return o if isinstance(o,list) else o.get("matches",[])
def load_history():
    rows=[]
    for p in sorted(DATA.glob("sigma_history*.jsonl"))+sorted(DATA.glob("sigma_history*.json")):
        try:
            if p.suffix==".jsonl":
                for line in p.read_text(encoding="utf-8").splitlines():
                    if line.strip(): rows.append(json.loads(line))
            else:
                o=json.loads(p.read_text(encoding="utf-8")); rows+= o if isinstance(o,list) else o.get("matches",[])
        except Exception as e: print(f"[HIST] skip {p.name}: {e}")
    return rows
def hype_rule(base, flags):
    flags=list(flags or []); is_hype="HYPE_TRAP" in flags
    other=[f for f in flags if f not in ("HYPE_TRAP",)]
    if not is_hype: return base, "NO HYPE", "NO SAFE BET" if base is None else "KEEP"
    if other:
        return None, f"HYPE_TRAP + {other} -> CANCEL to NO SAFE BET", "NO SAFE BET"
    adj=round(float(base)-7.0,1) if base is not None else None
    bet="KEEP" if (adj is not None and adj>=60) else "NO SAFE BET"
    return adj, f"HYPE_TRAP alone -> -7 points: {base} -> {adj}, {bet}", bet
def main():
    print("="*62); print(f"Sigma {VERSION} - BACKTEST + CALIBRATION + HYPE_TRAP (item 4)"); print("="*62)
    bulk=load_bulk(); hist=load_history()
    print(f"[DATA] Bulk rows={len(bulk)} | History rows={len(hist)} (expected Bulk ~839, History ~100788)")
    if len(bulk)<500: print("[GATE] Bulk <500 -> BLOCKED, restore backup, do NOT push Bulk"); return
    if not hist: print("[BACKTEST] NO CONFIRMED DATA - History file not found in data/ -> ABSTAIN, no invented backtest"); print("  In Termux, put sigma_history file in data/ and re-run. Do NOT invent results.")
    else:
        # Simple calibration: bucket by conf if history has conf + result
        buckets={}
        ok=0; tot=0
        for r in hist:
            c=r.get("conf") or r.get("adj") or r.get("confidence")
            res=r.get("result") or r.get("outcome") or r.get("hit")
            if c is None or res is None: continue
            tot+=1; b=int(float(c)//10*10); buckets.setdefault(b,{"n":0,"hits":0})
            buckets[b]["n"]+=1
            if str(res).lower() in ("hit","win","1","true","correct"): buckets[b]["n"] and (buckets[b].__setitem__("hits", buckets[b]["hits"]+1)); ok+=1
        print(f"[BACKTEST] Usable history with conf+result: {tot} / {len(hist)}")
        if tot==0: print("[CALIBRATION] NO CONFIRMED DATA - history has no conf/result -> ABSTAIN")
        else:
            print("[CALIBRATION] Predicted bucket -> actual hit rate (should be close, if far -> overconfident):")
            for b in sorted(buckets):
                n=buckets[b]["n"]; h=buckets[b]["hits"]; print(f"  {b}-{b+9}%: n={n} hit={h} rate={h/n*100:.1f}%")
    print("\n[HYPE_TRAP RULE V70 - FINAL ANSWER]")
    tests=[(71.7,["HYPE_TRAP"]),(94.3,["HYPE_TRAP","OVERCONFIDENT_BASE"]),(82.0,["HYPE_TRAP","HIGH_CONF_GATE"]),(68.5,[])]
    for base,flags in tests:
        adj,why,bet=hype_rule(base,flags); print(f"  base={base} flags={flags} -> adj={adj} | {why} | bet={bet}")
    print("  Egypt 71.7 HYPE alone -> 64.7 KEEP (matches V64)")
    print("  Morocco 94.3 HYPE+OVERCONFIDENT -> NO SAFE BET (matches V64)")
    out={"version":VERSION,"date":TODAY,"bulk_rows":len(bulk),"history_rows":len(hist),"hype_rule":"HYPE alone -7 KEEP if >=60; HYPE+other -> NO SAFE BET"}
    (DATA/"sigma_v70_report.json").write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding="utf-8")
    print("\nDONE. Report: data/sigma_v70_report.json")
if __name__=="__main__": main()
