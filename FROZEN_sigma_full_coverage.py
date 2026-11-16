# FROZEN_sigma_full_coverage.py - V44.50 FULL COVERAGE CHECK
# الهدف: تحديث لكل احداث ومباريات كرة القدم بالكامل
# لا يخترع نتائج. اللي ملوش داتا مؤكدة يروح No-data، مش توقع.
# الاستخدام: python3 FROZEN_sigma_full_coverage.py
# المدخل: data/sigma_bulk_predictions_v44_safe.csv او data/sigma_bulk_predictions_v44.csv
# المخرج: data/sigma_full_coverage_report.json + .csv
import csv, json
from pathlib import Path
from collections import Counter

BASE = Path(__file__).parent
DATA = BASE / "data"

# التغطية الكاملة المطلوبة - بالاسم فقط، من غير IDs مخترعة
# كل بطولة لازم تتغطى، ولو مش موجودة تتسجل MISSING مش تتخترع
FULL_TARGETS = [
    # دوريات - اوروبا الكبار
    ("Premier League", "LEAGUE", "England"),
    ("La Liga", "LEAGUE", "Spain"),
    ("Serie A", "LEAGUE", "Italy"),
    ("Bundesliga", "LEAGUE", "Germany"),
    ("Ligue 1", "LEAGUE", "France"),
    ("Eredivisie", "LEAGUE", "Netherlands"),
    ("Primeira Liga", "LEAGUE", "Portugal"),
    ("Belgian Pro League", "LEAGUE", "Belgium"),
    ("Super Lig", "LEAGUE", "Turkey"),
    ("Scottish Premiership", "LEAGUE", "Scotland"),
    ("Austrian Bundesliga", "LEAGUE", "Austria"),
    ("Swiss Super League", "LEAGUE", "Switzerland"),
    ("Danish Superliga", "LEAGUE", "Denmark"),
    ("Swedish Allsvenskan", "LEAGUE", "Sweden"),
    ("Norwegian Eliteserien", "LEAGUE", "Norway"),
    ("Greek Super League", "LEAGUE", "Greece"),
    ("Czech First League", "LEAGUE", "Czech"),
    ("Polish Ekstraklasa", "LEAGUE", "Poland"),
    ("Croatian HNL", "LEAGUE", "Croatia"),
    ("Serbian SuperLiga", "LEAGUE", "Serbia"),
    # افريقيا واسيا وامريكا
    ("Egyptian Premier League", "LEAGUE", "Egypt"),
    ("Saudi Pro League", "LEAGUE", "Saudi Arabia"),
    ("UAE Pro League", "LEAGUE", "UAE"),
    ("Qatar Stars League", "LEAGUE", "Qatar"),
    ("Moroccan Botola", "LEAGUE", "Morocco"),
    ("Algerian Ligue 1", "LEAGUE", "Algeria"),
    ("Tunisian Ligue 1", "LEAGUE", "Tunisia"),
    ("South African PSL", "LEAGUE", "South Africa"),
    ("Nigerian NPFL", "LEAGUE", "Nigeria"),
    ("Brazil Serie A", "LEAGUE", "Brazil"),
    ("Argentina Primera", "LEAGUE", "Argentina"),
    ("MLS", "LEAGUE", "USA"),
    ("Liga MX", "LEAGUE", "Mexico"),
    ("Colombian Primera", "LEAGUE", "Colombia"),
    ("Chilean Primera", "LEAGUE", "Chile"),
    ("J1 League", "LEAGUE", "Japan"),
    ("K League 1", "LEAGUE", "Korea"),
    ("Indian Super League", "LEAGUE", "India"),
    ("Australian A-League", "LEAGUE", "Australia"),
    # كؤوس اندية
    ("UEFA Champions League", "CUP", "Europe"),
    ("UEFA Europa League", "CUP", "Europe"),
    ("UEFA Conference League", "CUP", "Europe"),
    ("Copa Libertadores", "CUP", "South America"),
    ("Copa Sudamericana", "CUP", "South America"),
    ("AFC Champions League", "CUP", "Asia"),
    ("CAF Champions League", "CUP", "Africa"),
    ("CAF Confederation Cup", "CUP", "Africa"),
    ("FIFA Club World Cup", "CUP", "World"),
    ("FA Cup", "CUP", "England"),
    ("Copa del Rey", "CUP", "Spain"),
    ("Coppa Italia", "CUP", "Italy"),
    ("DFB Pokal", "CUP", "Germany"),
    ("Coupe de France", "CUP", "France"),
    ("Egypt Cup", "CUP", "Egypt"),
    ("King Cup", "CUP", "Saudi Arabia"),
    # منتخبات
    ("World Cup Qualifiers", "NATIONAL", "World"),
    ("UEFA Nations League", "NATIONAL", "Europe"),
    ("AFCON", "NATIONAL", "Africa"),
    ("Copa America", "NATIONAL", "South America"),
    ("Asian Cup", "NATIONAL", "Asia"),
    ("Gold Cup", "NATIONAL", "North America"),
    ("Euro Qualifiers", "NATIONAL", "Europe"),
    ("Friendlies - National", "NATIONAL", "World"),
    # سيدات وشباب - تحتاج مصدر منفصل
    ("Women - Top Leagues", "WOMEN", "World"),
    ("Youth - U21 / U19", "YOUTH", "World"),
]

def load_bulk():
    for name in ["sigma_bulk_predictions_v44_safe.csv", "sigma_bulk_predictions_v44.csv", "sigma_bulk_predictions.csv"]:
        p = DATA / name
        if p.exists():
            rows = list(csv.DictReader(open(p, encoding='utf-8')))
            print(f"Loaded: {name} - {len(rows)} rows")
            return rows, name
    return [], "NONE"

def main():
    rows, src = load_bulk()
    if not rows:
        print("ERROR: مفيش ملف توقعات - شغل المحرك الاول")
        return
    # احصائيات الحالية
    by_type = Counter([r.get('competition_type','') or r.get('type','') for r in rows])
    by_league = Counter([r.get('league','') or r.get('competition','') for r in rows])
    print(f"Current total: {len(rows)}")
    print(f"By type: {dict(by_type)}")
    # فحص التغطية
    covered = []
    missing = []
    # نجهز اسماء البطولات الموجودة للمقارنة - تقريب بالاسم
    existing_text = " ".join([(r.get('league','') + " " + r.get('competition','') + " " + r.get('match','')) for r in rows]).lower()
    for name, typ, region in FULL_TARGETS:
        # بحث مرن: اول كلمة مهمة
        key = name.lower().split()[0]
        # اسماء خاصة
        found = False
        # تحقق بسيط: لو اسم البطولة موجود في اي صف
        for r in rows:
            comp = (r.get('league','') + " " + r.get('competition','')).lower()
            if name.lower() in comp or comp in name.lower():
                found = True
                break
        # بديل: لو نوع البطولة موجود وعدد كبير
        if not found:
            # للبطولات الكبيرة نعتبرها مغطاة لو فيه صفوف من نفس النوع والمنطقة
            pass
        if found:
            covered.append({"name": name, "type": typ, "region": region, "status": "COVERED"})
        else:
            missing.append({"name": name, "type": typ, "region": region, "status": "MISSING - needs real source, NOT invented", "action": "Fetch from API-Football / football-data if available, else No-data"})
    print(f"Covered targets: {len(covered)} / {len(FULL_TARGETS)}")
    print(f"Missing targets: {len(missing)} / {len(FULL_TARGETS)}")
    for m in missing[:20]:
        print(f"  MISSING: {m['name']} ({m['type']} - {m['region']})")
    # تقرير
    report = {
        "source_file": src,
        "total_predictions": len(rows),
        "by_type": dict(by_type),
        "by_league_top": dict(by_league.most_common(20)),
        "coverage_targets_total": len(FULL_TARGETS),
        "coverage_covered": len(covered),
        "coverage_missing": len(missing),
        "covered": covered,
        "missing": missing,
        "note": "MISSING لا يعني اختراع توقع. يعني لازم مصدر حقيقي (API-Football token في apifootball_token.txt منفصل، او football-data) او يروح No-data. لا تضع اي توكن في الشات.",
        "next_steps": [
            "1- احفظ توكن API-Football في ~/apifootball_token.txt منفصل - مش في الشات",
            "2- شغل الفetch الكامل من Termux",
            "3- شغل FROZEN_sigma_safe_markets.py للاسواق والرهان الامان",
            "4- Review + V54 - لو PASS بس اعمل Push V44.50",
            "5- اي بطولة ملهاش داتا مؤكدة تروح No-data"
        ]
    }
    with open(DATA / "sigma_full_coverage_report.json", "w", encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with open(DATA / "sigma_full_coverage_report.csv", "w", newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=["name","type","region","status","action"])
        w.writeheader()
        for r in covered + missing:
            w.writerow({**r, "action": r.get("action","OK")})
    print("DONE - Report: data/sigma_full_coverage_report.json/.csv")
    print("القاعدة: اللي مش موجود = MISSING، مش توقع مخترع.")

if __name__ == "__main__":
    main()
