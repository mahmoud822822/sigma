import pathlib
p = pathlib.Path("index.html")
t = p.read_text(encoding="utf-8")
t = t.replace("V20 Fix", "V23 Full World 84449 + Admin")
t = t.replace("Sigma V20", "Sigma V23")
t = t.replace("V20 -", "V23 -")
t = t.replace("History 84449", "History 84449 - V23")
p.write_text(t, encoding="utf-8")
print("Renamed to V23")
