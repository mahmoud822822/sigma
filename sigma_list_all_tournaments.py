import urllib.request, json, os
tok = ""
if os.path.exists("token.txt"):
    tok = open("token.txt").read().strip()
if not tok:
    tok = os.environ.get("FOOTBALL_TOKEN", "")
if not tok:
    print("No token in token.txt")
else:
    print(f"Token len: {len(tok)}")
    req = urllib.request.Request("https://api.football-data.org/v4/competitions", headers={"X-Auth-Token": tok})
    try:
        data = json.load(urllib.request.urlopen(req, timeout=20))
        comps = data.get("competitions", [])
        print(f"Total competitions: {len(comps)}")
        for c in comps:
            print(f"- {c.get('name')} | {c.get('code')} | {c.get('area',{}).get('name')} | {c.get('type')}")
        json.dump(comps, open("data/sigma_all_competitions.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
        print("Saved to data/sigma_all_competitions.json")
    except Exception as e:
        print(f"Error: {e}")
