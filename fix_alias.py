import pathlib
p = pathlib.Path("sigma_main.py")
t = p.read_text(encoding="utf-8")
# شيل المسافات الزيادة اللي كانت في "barca" و "porto"
t = t.replace('"barca"', '"barca"').replace('"porto"', '"porto"').replace(':"porto"', ':"porto"').replace('"barca":"barcelona"', '"barca":"barcelona"')
# تأكيد إن barca موجود صح
if '"barca":"barcelona"' not in t:
    t = t.replace('"man city"', '"barca":"barcelona","man city"')
p.write_text(t, encoding="utf-8")
print("Alias fixed - barca / porto")
# تأكيد
import re
m = re.search(r'aliases = \{.*?\}', t, re.S)
print(m.group(0)[:300] if m else "no aliases")
