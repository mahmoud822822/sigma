import zipfile, pathlib
files = ["sigma_main.py","sigma_forecaster.py","sigma_auto_fetch.py","data/sigma_bulk_predictions.csv","data/sigma_real_verified.csv","data/sigma_history.csv","data/sigma_team_stats.json","TEST_REPORT.txt","README_AR.txt"]
with zipfile.ZipFile("sigma-v5-final.zip","w",zipfile.ZIP_DEFLATED) as z:
    for f in files:
        p = pathlib.Path(f)
        if p.exists():
            z.write(p, f)
            print("added", f)
        else:
            print("missing", f)
print("ZIP done")
