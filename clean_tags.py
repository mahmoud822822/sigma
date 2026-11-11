import re, pathlib
L = chr(12304)
R = chr(12305)
B = chr(166)
pat = L + "entity-([^" + B + r"\]]+)" + B + r"[^" + R + r"]*" + R
for fname in ["sigma_main.py", "fix_alias.py", "fix_fuzzy.py"]:
    p = pathlib.Path(fname)
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    t2 = re.sub(pat, r"\1", t)
    # شيل أي مسافة زيادة جوه المفاتيح " barca" -> "barca"
    t2 = t2.replace('" barca"', '"barca"').replace('" porto"', '"porto"').replace(':" porto"', ':"porto"')
    if t2 != t:
        p.write_text(t2, encoding="utf-8")
        print(fname, "cleaned")
    else:
        print(fname, "already clean")
print("Done - check aliases")
