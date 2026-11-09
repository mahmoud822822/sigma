import subprocess, sys, os, shutil, csv, pathlib, time
def sh(cmd):
    print(f">>> {cmd}")
    try:
        r=subprocess.run([sys.executable]+cmd); print(f"exit {r.returncode}"); return r.returncode
    except Exception as e: print(f"skip {e}"); return -1
def clean():
    print("--- Clean ---")
    try: os.remove(".git/index.lock")
    except: pass
    shutil.rmtree("__pycache__", ignore_errors=True)
    shutil.rmtree("data/__pycache__", ignore_errors=True)
    idx=pathlib.Path("index.html")
    if idx.exists() and idx.stat().st_size==0:
        print("index 0 - restoring"); subprocess.run(["git","checkout","--","index.html"])
    print(f"Free: {shutil.disk_usage('.').free//1024//1024} MB")
def dedup():
    p=pathlib.Path("data/sigma_history.csv")
    if not p.exists(): return
    rows=list(csv.DictReader(open(p, encoding="utf-8")))
    seen=set(); out=[]
    for r in rows:
        k=(r.get("date",""),r.get("home",""),r.get("away",""))
        if k in seen: continue
        seen.add(k); out.append(r)
    print(f"Dedup {len(rows)} -> {len(out)}")
    if len(out)!=len(rows):
        with open(p,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
def one_cycle():
    clean(); dedup()
    import os
    for f in ["sigma_auto_fetch.py","sigma_predict_next.py","sigma_track.py","sigma_report.py","sigma_make_index.py"]:
        if os.path.exists(f): sh([f])
    print("--- Git ---")
    import subprocess as sp
    sp.run(["git","pull","--rebase"])
    sp.run(["git","add","-f","index.html","data/sigma_mega_predictions.csv","data/sigma_real_verified.csv","sigma_super_update.py"])
    sp.run(["git","commit","-m","Sigma Super Update - auto"])
    sp.run(["git","push"])
    print("Cycle done")
if __name__=="__main__":
    import sys, time
    if "--loop" in sys.argv:
        print("SUPER LOOP every 6h")
        while True:
            one_cycle(); print("Sleep 6h..."); time.sleep(6*3600)
    else:
        one_cycle()
