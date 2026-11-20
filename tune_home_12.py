import re

# 1. ضبط أفضلية الأرض عند 12.0 نقطة Elo في المحرك
with open("sigma_engine.py", "r", encoding="utf-8") as f:
    eng = f.read()

eng = re.sub(r'\(elo_h\s*\+\s*\d+\.?\d*\)\s*-\s*elo_a', '(elo_h + 12.0) - elo_a', eng)
eng = re.sub(r'max\(-0\.\d+,\s*min\(0\.\d+,\s*diff\s*\*\s*0\.\d+\)\)', 'max(-0.45, min(0.45, diff * 0.0013))', eng)

with open("sigma_engine.py", "w", encoding="utf-8") as f:
    f.write(eng)

# 2. تنسيق الرقم المعروض في الواجهة والقالب ليصبح Elo 12+
for fname in ["sigma_engine.py", "index.html"]:
    try:
        with open(fname, "r", encoding="utf-8") as f:
            txt = f.read()
        txt = re.sub(r'Elo\s+(38|65)\+', 'Elo 12+', txt)
        txt = re.sub(r'\+(38|65)(?=[^\d])', '+12', txt)
        with open(fname, "w", encoding="utf-8") as f:
            f.write(txt)
    except FileNotFoundError:
        pass

print("DONE: Home advantage set to +12 Elo (10-15 range) across engine & UI!")
