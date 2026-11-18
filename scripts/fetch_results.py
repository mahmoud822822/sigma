import json, urllib.request, os
URL = os.environ.get("SUPABASE_URL","").rstrip("/")
KEY = os.environ.get("SUPABASE_KEY","")
if not URL or not KEY:
    print("مفيش مفاتيح - اعمل الخطوة 2 الاول")
    exit()
total = 0
off = 0
while True:
    req = urllib.request.Request(f"{URL}/rest/v1/sigma_matches?select=home,score,away,result&limit=1000&offset={off}", headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        print("فشل الاتصال:", e)
        print("لو 401 يبقى المفتاح غلط - لو 404 يبقى الرابط غلط")
        break
    if not data:
        break
    total += len(data)
    print(f"جبت {len(data)} - الإجمالي لحد دلوقتي: {total}")
    if len(data) < 1000:
        break
    off += 1000
print(f"خلص ✅ الإجمالي في Supabase: {total}")
