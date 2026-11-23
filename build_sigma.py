import json, urllib.request, urllib.parse, datetime
p = "data/sigma_site.json"
d = json.load(open(p, encoding="utf-8"))
matches = d.get("matches", [])
if not matches and isinstance(d, list):
    matches = d
seen = set()
for m in matches:
    h = str(m.get("home", m.get("home_team", ""))).strip().lower()
    a = str(m.get("away", m.get("away_team", ""))).strip().lower()
    dt = str(m.get("date", "")).strip()
    seen.add((h, a, dt))
added = 0
template = matches[0] if matches else {}
for day in ["2026-11-23", "2026-11-24"]:
    url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={day}&s=Soccer"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        print("fetch failed", day, e)
        continue
    events = data.get("events") or []
    for ev in events:
        home = (ev.get("strHomeTeam") or "").strip()
        away = (ev.get("strAwayTeam") or "").strip()
        date = (ev.get("dateEvent") or day).strip()
        if not home or not away:
            continue
        key = (home.lower(), away.lower(), date)
        if key in seen:
            continue
        league = ev.get("strLeague") or ""
        new = dict(template) if isinstance(template, dict) else {}
        new.update({
            "home": home, "home_team": home,
            "away": away, "away_team": away,
            "date": date, "league": league,
            "conf": 52, "confidence": 52, "prob": 52,
            "elo": 1500, "status": "upcoming"
        })
        matches.append(new)
        seen.add(key)
        added += 1
    print("day", day, "events", len(events), "added total", added)
for m in matches:
    try:
        conf = float(m.get("conf", m.get("confidence", m.get("prob", 0))) or 0)
    except:
        conf = 0
    conf = min(conf, 86)
    elo = m.get("elo", m.get("elo_home", None))
    if elo is None or elo == 0 or elo == 1500 or str(elo).lower() in ["unknown", "none", ""]:
        conf = min(conf, 52)
    m["conf"] = conf
    m["confidence"] = conf
    if "prob" in m:
        m["prob"] = conf
if isinstance(d, dict):
    d["matches"] = matches
    d["risk"] = 13
    d["cap"] = 86
    out = d
else:
    out = matches
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", p, "matches", len(matches), "added", added, "cap 86 risk 13")
for m in matches:
    h = str(m.get("home", "")).lower()
    if "ahly" in h or "أهلي" in h or "alahly" in h:
        print("AHLY:", m.get("home"), "vs", m.get("away"), m.get("date"), m.get("league"))
