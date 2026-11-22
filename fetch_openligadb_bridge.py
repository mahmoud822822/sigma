import json, urllib.request, urllib.error, difflib, re

def norm(s):
    s = (s or "").lower()
    s = re.sub(r'^(al|el|fc|sc|real|club|sv|vfb|borussia)\s+', '', s)
    s = re.sub(r'[^a-z0-9 ]', '', s)
    s = s.replace('bayern munich','bayern').replace('bayern muenchen','bayern')
    return s.strip()

def similar(a,b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()

print("=== فحص شكل الملفات - عشان المطابقة ===")
try:
    v = json.load(open('data/sigma_v64_results.json'))
    items = v if isinstance(v, list) else v.get('matches', v.get('results', []))
    print("v64_results اول عنصر:")
    print(json.dumps(items[0] if items else v, ensure_ascii=False)[:500])
except Exception as e:
    print("v64_results مش قادر اقراه:", e)

try:
    # جرب ملف الـ Bulk - لو اسمه مختلف هيطبع رسالة
    import os
    for fname in ['data/sigma_bulk_predictions.json','data/sigma_universal_fixtures.json','data/sigma_site.json']:
        if os.path.exists(fname):
            d = json.load(open(fname))
            ms = d.get('matches', d) if isinstance(d, dict) else d
            print(f"\n{fname} اول ماتش:")
            print(json.dumps(ms[0] if isinstance(ms, list) and ms else ms, ensure_ascii=False)[:600])
            # عد الدوريات
            leagues = {}
            for m in ms if isinstance(ms, list) else []:
                lg = m.get('league') or m.get('competition') or m.get('league_name') or '?'
                leagues[lg] = leagues.get(lg,0)+1
            print(f"الدوريات في {fname}: {leagues}")
            break
except Exception as e:
    print("Bulk مش قادر اقراه:", e)

print("\n=== محاولة جلب نتايج المانية من OpenLigaDB ===")
print("ملحوظة: OpenLigaDB بيغطي المانيا بس. باقي الدوريات هتتعلم NEED_OTHER_SOURCE")
# مثال: جلب اخر جولة بوندسليجا - لو مفيش نت هيطبع رسالة ومش هيفشل
try:
    url = "https://api.openligadb.de/getmatchdata/bl1/2025"
    req = urllib.request.Request(url, headers={'User-Agent':'Sigma/1.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode('utf-8'))
    print(f"جاب {len(data)} ماتش من bl1 2025")
    for m in data[:3]:
        h = m.get('team1',{}).get('teamName','?')
        a = m.get('team2',{}).get('teamName','?')
        res = m.get('matchResults',[])
        print(f" - {h} vs {a} | نتايج: {res[-1] if res else 'لسه متلعبتش'}")
except Exception as e:
    print("مقدرش اجيب من OpenLigaDB دلوقتي (نت او API):", e)
    print("الحل: هنكمل يدوي للـ 4 المعروفين + نجهز المطابقة لباقي الـ 444 لما النت يرجع")
