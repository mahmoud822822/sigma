with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. إضافة زر القناص 4/4 بجانب زر إجماع 3/3 في لوحة الفلاتر
btn_target = 'إجماع 3/3</button>'
btn_replacement = 'إجماع 3/3</button><button class="qb" onclick="setQF(\'sniper\',this)" style="border-color:#a855f7;color:#e9d5ff">🎯 القناص 4/4</button>'

if btn_target in html and "setQF('sniper'" not in html:
    html = html.replace(btn_target, btn_replacement, 1)
    print("OK: Sniper 4/4 filter button added!")

# 2. ربط شرط الفلتر QF === "sniper" في دالة التصفية
filter_target = '(QF!=="c3"||m.consensus==="3/3")'
filter_replacement = '(QF!=="c3"||m.consensus==="3/3")&&(QF!=="sniper"||m.sniper)'

if filter_target in html and 'QF!=="sniper"' not in html:
    html = html.replace(filter_target, filter_replacement)
    print("OK: Sniper filter logic connected!")

# 3. إظهار شارة القناص في أعلى بطاقة المباراة
badge_target = '${m.golden?"⭐ ذهبي":""}'
badge_replacement = '${m.sniper?`<span style="background:rgba(168,85,247,.25);color:#d8b4fe;padding:2px 6px;border-radius:5px;border:1px solid rgba(168,85,247,.5);font-weight:800">🎯 قناص 4/4</span> `:""}${m.golden?"⭐ ذهبي":""}'

if badge_target in html and "🎯 قناص 4/4" not in html:
    html = html.replace(badge_target, badge_replacement)
    print("OK: Sniper 4/4 badge added to match cards!")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
