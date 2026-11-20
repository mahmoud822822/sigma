# 1. معايرة معامل Elo في sigma_engine.py لمنع تضخم النسب فوق 85%
with open("sigma_engine.py", "r", encoding="utf-8") as f:
    eng = f.read()

eng = eng.replace("max(-0.85, min(0.85, diff * 0.0028))", "max(-0.65, min(0.65, diff * 0.0019))")
with open("sigma_engine.py", "w", encoding="utf-8") as f:
    f.write(eng)

# 2. إصلاح تشوه التاريخ، وتحديث Elo 12+ إلى 65+، وإطالة اسم الفريق في index.html
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace('.replace(/-2026$/,"").slice(0,10)', '.slice(0,10)')
html = html.replace('Elo 12+', 'Elo 65+')
html = html.replace('m.home.slice(0,10)', 'm.home.slice(0,15)')
html = html.replace('m.away.slice(0,10)', 'm.away.slice(0,15)')
html = html.replace('m.home.slice(0,12)', 'm.home.slice(0,15)')
html = html.replace('m.away.slice(0,12)', 'm.away.slice(0,15)')

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("POLISHED: Engine calibrated & UI glitches fixed!")
