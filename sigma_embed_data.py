import json, pathlib, re
p = pathlib.Path("index.html")
h = p.read_text(encoding="utf-8")
d = json.load(open("data/sigma_next_month.json", encoding="utf-8"))
matches = d.get("matches", [])
print(f"Embedding {len(matches)} matches")
js = f'<script id="sigma-embedded-data" type="application/json">{json.dumps(matches, ensure_ascii=False)}</script>'
if "sigma-embedded-data" in h:
    h = re.sub(r'<script id="sigma-embedded-data".*?</script>', js, h, flags=re.DOTALL)
else:
    h = h.replace("</body>", js + "</body>")
p.write_text(h, encoding="utf-8")
print("Done - Data embedded")
