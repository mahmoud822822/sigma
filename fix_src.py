import pathlib
p = pathlib.Path("sigma_main.py")
t = p.read_text(encoding="utf-8")
t = t.replace('"Over25","conf"]', '"Over25","conf","src"]')
p.write_text(t, encoding="utf-8")
print("fixed src in CSV")
