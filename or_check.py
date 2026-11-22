import json, glob, os

# دور على ملف البيانات
files = glob.glob("data/*.json")
print("ملفات البيانات:", files)
if not files:
    print("مفيش ملف json في data - ابعت صورة لـ ls data")
    exit()

path = "data/sigma_site.json" if os.path.exists("data/sigma_site.json") else files[0]
print("هنفحص:", path)
d = json.load(open(path))

# حاول تلاقي قايمة الماتشات
matches = d.get("matches") or d.get("games") or d.get("data") or []
if isinstance(d, list):
    matches = d
print("عدد الماتشات:", len(matches))
if not matches:
    print("شكل الملف:", list(d.keys())[:10] if isinstance(d, dict) else type(d))
    exit()

# معايرة - نقسم حسب الاحتمال
buckets = [(0.50,0.60),(0.60,0.70),(0.70,0.80),(0.80,0.86),(0.86,1.01)]
for lo, hi in buckets:
    sel = []
    for m in matches:
        p = m.get("prob") or m.get("p_1x") or m.get("prob_1x") or m.get("probability") or 0
        try: p = float(p)
        except: continue
        if lo <= p < hi:
            sel.append(m)
    if not sel: 
        print(f"من {lo:.0%} لـ {hi:.0%}: مفيش ماتشات")
        continue
    # النتيجة - جرب كذا اسم حقل
    wins = 0
    counted = 0
    for m in sel:
        res = m.get("result") or m.get("outcome") or m.get("won") or m.get("hit")
        if res is None: continue
        counted += 1
        if res in [1, True, "WIN", "win", "1", "1X", "X2"]: wins += 1
    if counted:
        print(f"من {lo:.0%} لـ {hi:.0%}: عدد {len(sel)} - اتقاس منهم {counted} - نسبة المكسب الفعلية {wins/counted:.1%} - الفرق عن المتوقع {wins/counted - (lo+hi)/2:+.1%}")
    else:
        print(f"من {lo:.0%} لـ {hi:.0%}: عدد {len(sel)} - مفيش نتائج مسجلة، مش هنقدر نحسب المعايرة")
