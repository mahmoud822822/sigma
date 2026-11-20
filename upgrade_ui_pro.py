with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. إضافة عرض شارة القيمة المضافة (+EV) ونسبة إدارة رأس المال (Kelly) في أعلى بطاقة المباراة
target_top = '${m.golden?"⭐ ذهبي":""}'
replacement_top = '${m.golden?"⭐ ذهبي":""}${valEdge>=4?` <span style="color:#38bdf8">💎 قيمة +${valEdge}%</span>`:""}${m.kelly_pct?` <span style="color:#10b981">💰 رصيد ${m.kelly_pct}%</span>`:""}'

if target_top in html and "💎 قيمة" not in html:
    html = html.replace(target_top, replacement_top)
    print("UPGRADED: Added +EV Value Badge & Kelly Staking to match cards!")

# 2. التأكد من وجود توقيع Mahmoud Emad بالإنجليزية في دالة رسم البطاقة المصورة mkCard
if "Mahmoud Emad" not in html:
    html = html.replace("SIGMA AI", "SIGMA AI • Mahmoud Emad")
    print("UPGRADED: Added Mahmoud Emad signature!")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
