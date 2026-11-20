import re

# 1. تحديث المحرك sigma_engine.py لحساب أفضلية الأرض ديناميكياً (3, 5, 8, 12) وإرسالها لكل مباراة
with open("sigma_engine.py", "r", encoding="utf-8") as f:
    eng = f.read()

dyn_func = '''def get_dynamic_home_adv(lg):
    s = str(lg).lower()
    if any(k in s for k in ["friend", "world", "euro", "afcon", "copa-america", "nations", "neutral", "club-world"]):
        return 3.0
    if any(k in s for k in ["champions-league", "europa", "conference", "cup", "fa-cup", "copa", "pokal", "championship", "serie-b", "segunda", "ligue-2", "2-bundesliga"]):
        return 5.0
    if any(k in s for k in ["egypt", "saudi", "morocco", "botola", "tunisia", "algeria", "qatar", "uae", "caf", "brazil", "brasileiro", "argentina", "libertadores", "sudamericana", "turkey", "greece"]):
        return 12.0
    return 8.0

def pred(h, a, R, w, lg=""):'''

if "def get_dynamic_home_adv" not in eng:
    eng = eng.replace('def pred(h, a, R, w, lg=""):', dyn_func)

# استبدال القيمة الثابتة بالدالة الديناميكية وحفظها في مخرجات المباراة
eng = re.sub(r'\(elo_h\s*\+\s*\d+\.?\d*\)\s*-\s*elo_a', '(elo_h + (get_dynamic_home_adv(lg) * 1.5)) - elo_a', eng)
eng = eng.replace('"elo_away": round(elo_a),', '"elo_away": round(elo_a), "home_adv_pct": int(get_dynamic_home_adv(lg)),')

with open("sigma_engine.py", "w", encoding="utf-8") as f:
    f.write(eng)

# 2. تحديث الواجهة index.html لعرض النسبة الديناميكية الخاصة بكل مباراة بدلاً من الرقم الثابت
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace('Elo 12+', 'أرض +${m.home_adv_pct||8}%')
html = html.replace('Elo 38+', 'أرض +${m.home_adv_pct||8}%')
html = html.replace('Elo 65+', 'أرض +${m.home_adv_pct||8}%')

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("SUCCESS: Dynamic Home Advantage (3%, 5%, 8%, 12%) enabled across Engine & UI!")
