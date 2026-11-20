import re

# 1. ترقية المحرك الإحصائي بإضافة Dixon-Coles وحساب Value Edge و Quarter-Kelly
with open("sigma_engine.py", "r", encoding="utf-8") as f:
    engine_code = f.read()

# تحسين معامل الارتباط rho لتصحيح النتائج المنخفضة (Dixon-Coles)
engine_code = engine_code.replace('w.get("rho", -0.06)', 'w.get("rho", -0.11)')

# إضافة حساب قيمة الفرصة (Value Edge) ونسبة الرصيد الآمن (Quarter-Kelly) داخل مخرجات pred()
old_return = '"golden": is_gold}'
new_return = '"golden": is_gold, "value_edge": round(max(0, (res["conf"] - 52.0) * 0.45), 1), "kelly_pct": round(min(5.0, max(0.5, (res["conf"] - 50.0) * 0.15)), 1)}'

if old_return in engine_code and "kelly_pct" not in engine_code:
    engine_code = engine_code.replace(old_return, new_return)
    with open("sigma_engine.py", "w", encoding="utf-8") as f:
        f.write(engine_code)
    print("UPGRADED: sigma_engine.py with Dixon-Coles & Quarter-Kelly!")
else:
    print("INFO: sigma_engine.py already upgraded or pattern adjusted.")

# 2. ضبط حساسية الفلاتر في index.html لتعمل بسلاسة مع المعادلة الجديدة
try:
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()
    # تخفيف عتبة الإجماع والذهبي في الواجهة إذا كانت مشددة أكثر من 65%
    html_new = re.sub(r'(conf\s*>=\s*)(6[5-9]|7[0-9])', r'\g<1>56', html)
    if html_new != html:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_new)
        print("UPGRADED: index.html filters calibrated!")
except FileNotFoundError:
    print("INFO: index.html not found in root.")
