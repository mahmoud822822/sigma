# FROZEN_sigma_safe_markets.py - V44.49 SAFE MARKETS
# يضيف اختيارات اكتر + رهان امان من نفس احتمالات V44 - من غير ما يغير اي xG او توقع
# لا يخترع نتائج. كل سوق جديد مشتق رياضيا من الاحتمالات الموجودة.
# الاستخدام: python3 FROZEN_sigma_safe_markets.py
# المدخل: data/sigma_bulk_predictions_v44.csv (444 REAL)
# المخرج: data/sigma_bulk_predictions_v44_safe.csv + .json
import csv, json, math
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"
IN_CSV = DATA / "sigma_bulk_predictions_v44.csv"
OUT_CSV = DATA / "sigma_bulk_predictions_v44_safe.csv"
OUT_JSON = DATA / "sigma_bulk_predictions_v44_safe.json"

def f(v, default=0.0):
    try:
        return float(str(v).strip())
    except:
        return default

def main():
    if not IN_CSV.exists():
        print(f"ERROR: missing {IN_CSV} - شغل المحرك الاول")
        return
    rows = list(csv.DictReader(open(IN_CSV, encoding='utf-8')))
    print(f"Input: {len(rows)} rows")
    out = []
    safe_n = medium_n = nosafe_n = 0
    for r in rows:
        # لو صف DEFAULT / No-data - مفيش رهان امان
        if str(r.get('is_default','0')) == '1' or str(r.get('xG','')) == 'No confirmed data':
            r['safe_pick'] = 'No confirmed data'
            r['safe_prob'] = ''
            r['safe_level'] = 'NO SAFE - DO NOT BET'
            r['all_markets_ranked'] = 'No confirmed data'
            r['combo_suggestion'] = 'No confirmed data'
            r['risk_note'] = 'No confirmed data - لا تلعب'
            out.append(r)
            nosafe_n += 1
            continue
        lam_h = f(r.get('xG_home'))
        lam_a = f(r.get('xG_away'))
        btts = f(r.get('BTTS'))
        over15 = f(r.get('Over15'))
        over25 = f(r.get('Over25'))
        over35 = f(r.get('Over35'))
        under25 = f(r.get('Under25'))
        dc1x = f(r.get('DC1X'))
        dc12 = f(r.get('DC12'))
        dcx2 = f(r.get('DCX2'))
        cs_h = f(r.get('CS_Home'))
        cs_a = f(r.get('CS_Away'))
        p1 = f(r.get('prob_1')); px = f(r.get('prob_X')); p2 = f(r.get('prob_2'))

        # اسواق مشتقة - مكملات رياضية، مش اختراع:
        # Over 0.5 = 1 - P(0-0) من Poisson بنفس xG
        p00 = math.exp(-lam_h - lam_a) if lam_h>0 and lam_a>0 else 0.0
        over05 = (1.0 - p00) * 100.0
        under35 = 100.0 - over35
        under15 = 100.0 - over15
        btts_no = 100.0 - btts
        home_to_score = 100.0 - cs_a  # Away Clean Sheet = Home يسجل 0
        away_to_score = 100.0 - cs_h

        markets = [
            ("Over 0.5", over05),
            ("Over 1.5", over15),
            ("Over 2.5", over25),
            ("Over 3.5", over35),
            ("Under 1.5", under15),
            ("Under 2.5", under25),
            ("Under 3.5", under35),
            ("BTTS Yes", btts),
            ("BTTS No", btts_no),
            ("1X (Home or Draw)", dc1x),
            ("12 (No Draw)", dc12),
            ("X2 (Draw or Away)", dcx2),
            ("1", p1),
            ("X", px),
            ("2", p2),
            ("Home to Score", home_to_score),
            ("Away to Score", away_to_score),
            ("Home Clean Sheet", cs_h),
            ("Away Clean Sheet", cs_a),
        ]
        # رتب كل الاسواق من الاعلى للاقل - دي الاختيارات الاكتر
        ranked = sorted(markets, key=lambda x: x[1], reverse=True)
        ranked_str = " / ".join([f"{n} {p:.1f}%" for n,p in ranked])

        # رهان الامان = اعلى احتمال من مجموعة الامان فقط
        safe_pool = [m for m in markets if m[0] in ("Over 0.5","Over 1.5","Under 3.5","1X (Home or Draw)","X2 (Draw or Away)","12 (No Draw)","Home to Score","Away to Score")]
        safe_pick, safe_prob = max(safe_pool, key=lambda x: x[1])
        if safe_prob >= 75:
            level = "SAFE"
            safe_n += 1
            note = "احتمال عالي - لكن مش مضمون 100%، ممكن يخسر"
        elif safe_prob >= 65:
            level = "MEDIUM"
            medium_n += 1
            note = "احتمال متوسط - رهان متوازن، مخاطرة موجودة"
        else:
            level = "NO SAFE - DO NOT BET"
            nosafe_n += 1
            note = "مفيش رهان امان في الماتش ده - الافضل متلعبش"

        # كومبو مقترح = اعلى سوقين امان - الاحتمال المشترك تقديري = حاصل الضرب / 100
        top2 = sorted(safe_pool, key=lambda x: x[1], reverse=True)[:2]
        combo_prob = (top2[0][1] * top2[1][1] / 100.0) if len(top2)==2 else 0
        combo = f"{top2[0][0]} + {top2[1][0]} ~ {combo_prob:.1f}% (تقديري)"

        r['safe_pick'] = safe_pick
        r['safe_prob'] = f"{safe_prob:.1f}"
        r['safe_level'] = level
        r['all_markets_ranked'] = ranked_str
        r['combo_suggestion'] = combo
        r['risk_note'] = note
        # اسواق اضافية للعرض
        r['Over05'] = f"{over05:.1f}"
        r['BTTS_No'] = f"{btts_no:.1f}"
        r['Under35'] = f"{under35:.1f}"
        r['Home_to_Score'] = f"{home_to_score:.1f}"
        r['Away_to_Score'] = f"{away_to_score:.1f}"
        out.append(r)

    # حفظ
    fieldnames = list(out[0].keys()) if out else []
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as fo:
        w = csv.DictWriter(fo, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out)
    with open(OUT_JSON, 'w', encoding='utf-8') as fo:
        json.dump({"total": len(out), "safe": safe_n, "medium": medium_n, "no_safe": nosafe_n, "matches": out}, fo, ensure_ascii=False, indent=2)
    print(f"Output: {OUT_CSV.name} / {OUT_JSON.name}")
    print(f"SAFE: {safe_n} | MEDIUM: {medium_n} | NO SAFE: {nosafe_n} | Total: {len(out)}")
    print("DONE - لم يتم تغيير اي xG او توقع اصلي. تمت اضافة اعمدة فقط.")

if __name__ == "__main__":
    main()
