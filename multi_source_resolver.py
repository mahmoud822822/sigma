import urllib.request, json
# ترتيب المصادر: OpenLigaDB (المانيا) -> TheSportsDB (UNL + عالمي) -> Football-Data (احتياطي)
# TheSportsDB مجاني بمفتاح تجريبي، Football-Data محتاج توكن من Secrets
def fetch_openligadb(league_code):
    url = f"https://api.openligadb.de/getmatchdata/{league_code}/2025"
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Sigma/1.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"OpenLigaDB {league_code} فشل: {e}")
        return []

def fetch_thesportsdb(date):
    # مثال: نتايج يوم معين - بيغطي UNL
    url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={date}&s=Soccer"
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Sigma/1.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
            return d.get('events', []) or []
    except Exception as e:
        print(f"TheSportsDB فشل: {e}")
        return []

print("Multi-Source Resolver جاهز")
print(" - BL1/BL2/DFB -> OpenLigaDB")
print(" - UNL (4 ماتشات) -> TheSportsDB")
print(" - باقي العالم -> Football-Data.org (لو التوكن موجود في Secrets)")
