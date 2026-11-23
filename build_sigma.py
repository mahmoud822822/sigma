import json, os
p = "data/sigma_site.json"
d = json.load(open(p, encoding="utf-8"))
matches = d.get("matches", [])
if not matches and isinstance(d, list):
    matches = d
for m in matches:
    try:
        conf = float(m.get("conf", m.get("confidence", 0)) or 0)
    except:
        conf = 0
    conf = min(conf, 86)
    elo = m.get("elo", m.get("elo_home", None))
    if elo is None or elo == 0 or str(elo).lower() in ["unknown", "none", ""]:
        conf = min(conf, 52)
    m["conf"] = conf
    m["confidence"] = conf
d["risk"] = 13
d["cap"] = 86
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", p, "matches", len(matches), "cap 86 risk 13")
