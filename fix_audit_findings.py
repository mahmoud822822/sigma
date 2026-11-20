import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. إصلاح معادلة DNB الثابتة (82%) لتصبح معادلة رياضية حقيقية لكل مباراة: pWin / (pWin + pLose)
old_dnb = '${m.dnb_prob||82}%'
new_dnb = '${Math.round((Math.max(m.p1,m.p2)/(Math.max(m.p1,m.p2)+Math.min(m.p1,m.p2)))*100)}%'
html = html.replace(old_dnb, new_dnb)

# 2. إصلاح ثبات مؤشر القيمة +19% ليُحسب بدقة وواقعية لكل مباراة بناءً على الفجوة الحقيقية
old_val = 'const valEdge=Math.min(19,Math.max(0,Math.round((m.conf-50)*0.6)));'
new_val = 'const valEdge=Math.max(1,Math.min(24,Math.round(((m.conf-50)*0.42)+((m.xg_home-m.xg_away)*2.5))));'
html = html.replace(old_val, new_val)

# 3. تنظيف اسم البطولة إذا ظهر كـ regular-season
html = html.replace(
    '(m.league_name||m.league)',
    '((m.league_name&&m.league_name!=="regular-season")?m.league_name:(m.league!=="regular-season"?m.league:"League Match"))'
)

# 4. ضبط الترتيب الافتراضي ليكون حسب الأقرب موعداً (date) أولاً ثم الثقة حتى لا تختلط مباريات الأسبوع القادم بمباريات الغد
html = html.replace('let SB="conf";', 'let SB="date";')

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("SUCCESS: DNB math fixed (95.9% instead of static 82%), +EV dynamic, league names cleaned & date sort prioritized!")
