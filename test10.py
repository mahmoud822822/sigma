import os, json, urllib.request, urllib.error
token="".join(c for c in os.environ.get("FOOTBALL_DATA_TOKEN","").strip() if c.isascii() and c.isalnum())
def try_url(name, url):
    req=urllib.request.Request(url, headers={"X-Auth-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d=json.loads(r.read().decode())
            print(f"{name}: OK got {len(d.get('matches',[]))}")
    except urllib.error.HTTPError as e:
        try: body=e.read().decode()[:300]
        except: body=""
        print(f"{name}: FAIL {e.code} - {body}")
try_url("A 10d no-status", "https://api.football-data.org/v4/matches?dateFrom=2025-01-01&dateTo=2025-01-10&competitions=2021,2014,2019,2002,2015,2003,2017,2004")
try_url("B 10d FINISHED", "https://api.football-data.org/v4/matches?dateFrom=2025-01-01&dateTo=2025-01-10&competitions=2021,2014,2019,2002,2015,2003,2017,2004&status=FINISHED")
try_url("C 30d no-status", "https://api.football-data.org/v4/matches?dateFrom=2025-01-01&dateTo=2025-01-30&competitions=2021,2014,2019,2002,2015,2003,2017,2004")
