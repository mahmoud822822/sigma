#!/usr/bin/env python3
# Sigma RUN FULL - One command executes EVERYTHING
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# Usage in Termux:  python3 sigma_run_full.py
# Order:
#  1. Forecaster (14 verified) - offline
#  2. Main: Eval + PredictAll + Learn + Team + xG + List - offline, inputs piped
#  3. V54 Check (14 real / 0 manual / 7 quarantine / 49 dup) - offline
#  4. Auto-Fetch (needs FOOTBALL_DATA_TOKEN 32 chars + internet, else SKIP with clear message)
#  5. V44 One-Shot (history openfootball + internationals + fetch + engine + review)
#     - With internet+token: fetches REAL history + REAL fixtures
#     - Without internet: SKIP URLs, dedup existing history, MANUAL fixtures only, Review still runs
#     - NEVER invents a match. DEFAULT predictions are labelled is_default=1, Golden=0
#  6. Writes data/sigma_full_report.json + data/sigma_full_run.log
# Stdlib only. No Arabic inside .py (report file is also English for Termux safety).
import subprocess, sys, json, os
from pathlib import Path
from datetime import date
BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
LOG = DATA / "sigma_full_run.log"
results = {"date": str(date.today()), "signature": "Signature Prediction and Forecast: Sigma - Mahmoud Emad", "steps": []}
log_lines = []
def log(s=""):
    print(s); log_lines.append(s)
def run_step(name, cmd, inp=None, timeout=180):
    log(f"\n{'='*68}\nSTEP: {name}\nCMD: {' '.join(cmd)}\n{'='*68}")
    try:
        r = subprocess.run(cmd, input=inp, capture_output=True, text=True, timeout=timeout, cwd=str(BASE))
        out = (r.stdout or "")[-5000:]
        log(out)
        if r.stderr: log("STDERR: " + (r.stderr or "")[-1000:])
        log(f"EXIT: {r.returncode}")
        results["steps"].append({"name": name, "exit": r.returncode, "ok": r.returncode == 0, "tail": out[-800:]})
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        log(f"TIMEOUT after {timeout}s")
        results["steps"].append({"name": name, "exit": "timeout", "ok": False, "tail": "timeout"})
        return False
def main():
    log("Sigma RUN FULL - Mahmoud Emad - executing EVERYTHING")
    log(f"Date: {date.today()}  Base: {BASE}")
    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    if not token:
        tf = Path.home() / "token.txt"
        if tf.exists():
            token = tf.read_text().strip(); os.environ["FOOTBALL_DATA_TOKEN"] = token
    log(f"Token: {'OK len=32' if len(token)==32 else 'MISSING/invalid len='+str(len(token))+' -> Auto-Fetch + FD layer will SKIP, MANUAL only'}")
    # 1 Forecaster
    run_step("1 Forecaster (14 verified)", [sys.executable, "sigma_forecaster.py"], timeout=30)
    # 2 Main - Eval + PredictAll + Learn
    run_step("2 Main Eval/PredictAll/Learn", [sys.executable, "sigma_main.py"], inp="4\n6\n8\n0\n", timeout=30)
    # 2b Main - Team + xG + List
    run_step("2b Main Team/xG/List", [sys.executable, "sigma_main.py"], inp="2\nManchester City FC\nFulham FC\n1\n1.78\n1.35\n3\n\n0\n", timeout=30)
    # 3 V54 Check
    run_step("3 V54 Check", [sys.executable, "sigma_v54_check.py"], timeout=30)
    # 4 Auto-Fetch (fails fast without token - expected, not fatal)
    ok_fetch = run_step("4 Auto-Fetch (needs token+internet)", [sys.executable, "sigma_auto_fetch.py"], timeout=60)
    if not ok_fetch:
        log("NOTE: Auto-Fetch did not produce fixtures (token/internet). V44 MANUAL path below still runs.")
    # 5 V44 One-Shot = history + fetch + engine + review + diagnosis
    ok_oneshot = run_step("5 V44 One-Shot (history+fetch+engine+review)", [sys.executable, "sigma_v44_final_one_shot.py"], timeout=180)
    # 6 Summary from generated files
    log(f"\n{'='*68}\nFINAL FILES\n{'='*68}")
    for p in ["data/sigma_history.csv", "data/sigma_universal_fixtures.json", "data/sigma_bulk_predictions_v44.json", "data/sigma_bulk_predictions_v44.csv", "data/sigma_bulk_predictions.csv", "data/sigma_bulk_predictions.json", "data/sigma_v44.json", "data/sigma_real_verified.csv"]:
        fp = BASE / p
        log(f"{p}: {'EXISTS '+str(fp.stat().st_size)+' bytes' if fp.exists() else 'MISSING'}")
    try:
        d = json.loads((DATA / "sigma_bulk_predictions_v44.json").read_text(encoding="utf-8"))
        rows = d.get("matches", [])
        log(f"V44 predictions: total={len(rows)} DEFAULT={sum(1 for r in rows if r.get('is_default')==1)} Golden={sum(1 for r in rows if r.get('golden')==1)}")
        log("RULE: DEFAULT rows are template fallback (xG 1.45-1.97), NOT real team history. Do NOT present them as confident picks.")
        results["v44"] = {"total": len(rows), "default": sum(1 for r in rows if r.get('is_default')==1), "golden": sum(1 for r in rows if r.get('golden')==1)}
    except Exception as e:
        log(f"V44 summary failed: {e}")
    try:
        import csv as _csv
        vr = list(_csv.DictReader(open(DATA / "sigma_real_verified.csv", encoding="utf-8")))
        results["verified_rows"] = len(vr)
        log(f"Verified rows: {len(vr)}")
    except Exception as e:
        log(f"Verified summary failed: {e}")
    results["oneshot_ok"] = ok_oneshot
    (DATA / "sigma_full_report.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    LOG.write_text("\n".join(log_lines), encoding="utf-8")
    log("\nDONE - Report: data/sigma_full_report.json  Log: data/sigma_full_run.log")
    log("In Termux with internet + token: re-run this file to get REAL history (openfootball) + REAL fixtures (football-data.org).")
    if not ok_oneshot:
        log("WARNING: V44 Review did NOT pass - DO NOT UPLOAD.")
        return 1
    return 0
if __name__ == "__main__":
    sys.exit(main())
