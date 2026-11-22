import urllib.request, json
for code in ["dfbpokal", "dfb", "dfb-pokal", "bl3"]:
    url = f"https://api.openligadb.de/getmatchdata/{code}/2025"
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Sigma/1.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
        print(f"{code}: {len(d)} ماتش - اول واحد: {d[0].get('team1',{}).get('teamName','?') if d else 'فاضي'} vs {d[0].get('team2',{}).get('teamName','?') if d else ''}")
    except Exception as e:
        print(f"{code} فشل: {e}")
