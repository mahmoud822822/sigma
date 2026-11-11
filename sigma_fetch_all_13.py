import urllib.request, json, os, time
tok = open("token.txt").read().strip()
comps = json.load(open("data/sigma_all_competitions.json", encoding="utf-8"))
all_matches = []
for c in comps:
    code = c.get("code")
    name = c.get("name")
    url = f"https://api.football-data.org/v4/competitions/{code}/matches?season=2026"
    req = urllib.request.Request(url, headers={"X-Auth-Token": tok})
    try:
        data = json.load(urllib.request.urlopen(req, timeout=20))
        ms = data.get("matches", [])
        print(f"{name} | {code} | {len(ms)} matches")
        for m in ms:
            all_matches.append({"competition": name, "code": code, "date": m.get("utcDate","")[:10], "home": m.get("homeTeam",{}).get("name",""), "away": m.get("awayTeam",{}).get("name",""), "status": m.get("status",""), "home_goals": (m.get("score",{}).get("fullTime",{}) or {}).get("home"), "away_goals": (m.get("score",{}).get("fullTime",{}) or {}).get("away")})
        time.sleep(1)
    except Exception as e:
        print(f"{code} Error: {e}")
print(f"Total: {len(all_matches)} matches from 13 competitions")
json.dump(all_matches, open("data/sigma_all_13_matches.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("Saved to data/sigma_all_13_matches.json")
