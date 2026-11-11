#!/usr/bin/env python3
# Sigma Results V5 - جلب النتائج الفعلية + مقارنة بالتوقع + أرشيف + سجل
# يقرأ توقعات data/sigma_next_month.json، ويجلب نتائج آخر 7 أيام، ويقارن
# stdlib only. لا يمسح توقعات، يضيف نتيجة فقط. يحفظ سجل في data/sigma_log.json
import os, json, csv, urllib.request, urllib.error, time, shutil
from datetime import date, timedelta
from pathlib import Path
BASE=Path(__file__).parent
DATA=BASE/"data"
DATA.mkdir(exist_ok=True)
COMP="2021,2014,2019,2002,2015,2003,2017,2004"
def log_event(event):
    logp=DATA/"sigma_log.json"
    logs=[]
    if logp.exists():
        try: logs=json.loads(logp.read_text(encoding="utf-8"))
        except: logs=[]
    logs.append({"date":str(date.today()),"time":time.strftime("%H:%M"),"event":event})
    logp.write_text(json.dumps(logs[-200:],ensure_ascii=False,indent=2),encoding="utf-8")
def fetch_results(token, df, dt):
    url=f"https://api.football-data.org/v4/matches?dateFrom={df}&dateTo={dt}&competitions={COMP}&status=FINISHED"
    req=urllib.request.Request(url, headers={"X-Auth-Token":token})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode()).get("matches",[]), None
    except Exception as e:
        return [], str(e)
def main():
    token="".join(c for c in os.environ.get("FOOTBALL_DATA_TOKEN","").strip() if c.isascii() and c.isalnum())
    if len(token)!=32:
        print("ERROR: Token len !=32 - results not fetched, old data kept")
        log_event("results: token invalid - skipped")
        return 2
    # Backup قبل التعديل
    predp=DATA/"sigma_next_month.json"
    if predp.exists(): shutil.copy(predp, DATA/"sigma_next_month.backup.json")
    # تحميل توقعات
    preds={}
    if predp.exists():
        try:
            j=json.loads(predp.read_text(encoding="utf-8"))
            for m in j.get("matches",[]): preds[m["match"]]=m
        except: pass
    print(f"Loaded {len(preds)} predictions")
    today=date.today(); start=today-timedelta(days=7)
    matches, err = fetch_results(token, start.isoformat(), today.isoformat())
    print(f"Fetched finished: {len(matches)} - err: {err}")
    if not matches:
        print("No finished matches - keeping old")
        log_event("results: 0 finished - kept old")
        return 0
    updated=0; compared=[]
    for m in matches:
        try:
            home=m['homeTeam']['name']; away=m['awayTeam']['name']; match=f"{home} vs {away}"
            score=m.get("score",{}).get("fullTime",{})
            rh,ra=score.get("home"),score.get("away")
            if rh is None or ra is None: continue
        except: continue
        # لو الماتش كان في توقعاتنا، قارن
        if match in preds:
            p=preds[match]
            pred_total=p.get("pred_home",0)+p.get("pred_away",0)
            real_total=rh+ra
            hit = abs(pred_total-real_total)<=1.0
            compared.append({"match":match,"date":m["utcDate"][:10],"pred":f"{p.get('pred_home')}-{p.get('pred_away')}","real":f"{rh}-{ra}","mae_total":abs(pred_total-real_total),"hit_within_1":hit})
            preds[match]["real_home"]=rh; preds[match]["real_away"]=ra; preds[match]["status"]="FINISHED"; preds[match]["mae_total"]=abs(pred_total-real_total)
            updated+=1
        else:
            # ماتش جديد مش في توقعاتنا - أرشيف فقط
            preds[match]={"match":match,"date":m["utcDate"][:10],"league":"Archive","pred_home":None,"pred_away":None,"real_home":rh,"real_away":ra,"status":"ARCHIVE_ONLY"}
    # حفظ - لا نحذف القديم، نحدث فقط
    out={"generated":str(today),"total_matches":len(preds),"compared":len(compared),"archive_note":"Predictions kept, results added, never deleted","matches":list(preds.values()),"compared_details":compared}
    (DATA/"sigma_next_month.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    # سجل التعلم
    if compared:
        mae=sum(c["mae_total"] for c in compared)/len(compared)
        hit=sum(1 for c in compared if c["hit_within_1"])/len(compared)*100
        print(f"Learning: compared {len(compared)}, MAE {mae:.2f}, Hit within 1 goal {hit:.1f}%")
        log_event(f"results: compared {len(compared)}, MAE {mae:.2f}, Hit1 {hit:.1f}%")
    else:
        print("No overlap with predictions - archive only")
        log_event("results: archive only, no overlap")
    print(f"Updated {updated} predictions with real results")
    return 0
if __name__=="__main__": raise SystemExit(main())
