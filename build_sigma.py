import json, sys, os, urllib.request
p = "data/sigma_site.json"
d = json.load(open(p, encoding="utf-8"))
matches = d.get("matches", []) if isinstance(d, dict) else d
if isinstance(d, list):
    d = {"matches": matches}
if not matches:
    print("REFUSE: matches==0, not overwriting")
    sys.exit(2)
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
        new = dict(template) if isinstance(template, dict) else {}
        new.update({"home": home, "home_team": home, "away": away, "away_team": away, "date": date, "league": ev.get("strLeague") or "", "conf": 52, "confidence": 52, "prob": 52, "elo": 1500, "status": "upcoming", "market": "1X2"})
        matches.append(new)
        seen.add(key)
        added += 1
    print("day", day, "events", len(events), "added total", added)
for m in matches:
    try:
        conf = float(m.get("conf", m.get("confidence", m.get("prob", 0))) or 0)
    except:
        conf = 0
    market = str(m.get("market", "") or m.get("bet_type", "") or "").upper()
    elo_vals = []
    for k in ["elo", "elo_home", "elo_away", "home_elo", "away_elo"]:
        if k in m and m[k] is not None:
            elo_vals.append(m[k])
    unknown = False
    if not elo_vals:
        unknown = True
    else:
        for v in elo_vals:
            s = str(v).strip().lower()
            if s in ["", "unknown", "none", "nan"]:
                unknown = True
            try:
                if float(v) == 0 or float(v) == 1500:
                    unknown = True
            except:
                unknown = True
    if unknown:
        conf = min(conf, 52)
    elif "DC" in market or "DOUBLE" in market:
        conf = min(conf, 86)
    elif "1X2" in market or market in ["1X", "X2", "12"]:
        conf = min(conf, 75)
    else:
        conf = min(conf, 86)
    m["conf"] = conf
    m["confidence"] = conf
    if "prob" in m:
        m["prob"] = conf
d["matches"] = matches
d["risk"] = 13
d["cap"] = 86
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", p, "matches", len(matches), "added", added, "cap 86 risk 13")
for m in matches:
    h = str(m.get("home", "")).lower()
    if "ahly" in h or "juventus" in h or "venezia" in h:
        print("CHECK:", m.get("home"), "vs", m.get("away"), m.get("date"), "conf", m.get("conf"))
