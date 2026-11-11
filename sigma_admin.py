#!/usr/bin/env python3
# Sigma Admin V5 - فحص: Backup + Token + Data Freshness + Missing Data - بدون طباعة أي توكن
import os, json, time
from datetime import date
from pathlib import Path
BASE=Path(__file__).parent
DATA=BASE/"data"
def check():
    print("=== Sigma Admin Check V5 ===")
    # 1. Backup موجود؟
    backups=list(DATA.glob("*.backup.json")) if DATA.exists() else []
    print(f"Backup files: {len(backups)} - {'OK' if backups else 'MISSING - شغل fetch مرة'}")
    # 2. Token موجود لكن لا نطبعه
    tok=os.environ.get("FOOTBALL_DATA_TOKEN","")
    print(f"Football token in env: {'YES len 32' if len(tok)==32 else 'NO / INVALID - لن يجلب جديد'}")
    print("Token never printed - حماية المفاتيح: فقط في GitHub Secrets + env")
    # 3. Freshness
    p=DATA/"sigma_next_month.json"
    if p.exists():
        age=(time.time()-p.stat().st_mtime)/3600
        print(f"Data age: {age:.1f} hours - {'FRESH' if age<30 else 'OLD - يحتاج تحديث'}")
        try:
            j=json.loads(p.read_text(encoding="utf-8"))
            print(f"Matches in file: {j.get('total_matches')} - Generated: {j.get('generated')}")
            # Missing data detection
            missing=[m["match"] for m in j.get("matches",[]) if m.get("data_quality")=="limited"]
            print(f"Limited data matches: {len(missing)} / {len(j.get('matches',[]))} - هذه المباريات توقعاتها متحفظة")
            finished=[m for m in j.get("matches",[]) if m.get("status")=="FINISHED"]
            print(f"Finished with real result: {len(finished)}")
        except Exception as e: print(f"JSON error: {e}")
    else: print("sigma_next_month.json MISSING")
    # 4. Current version backup - النسخة القديمة محفوظة؟
    print("Current version (V4) backup: يجب أن تبقى index.html القديم كـ index_v4_backup.html قبل رفع V5 - لا تحذف أي وظيفة")
    print("Changelog: data/sigma_log.json - كل تحديث مسجل")
    print("=== End Admin ===")
if __name__=="__main__": check()
