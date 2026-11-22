import json, urllib.request, difflib, re, collections

def norm(s):
    s = (s or "").lower()
    s = re.sub(r'^(al|el|fc|sc|real|club|sv|vfb|borussia|1\.)\s+', '', s)
    s = re.sub(r'[^a-z0-9 ]', '', s)
    s = s.replace('bayern munich','bayern').replace('bayern muenchen','bayern').replace('koln','cologne')
    return s.strip()
def sim(a,b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()

# 1. اطبع الـ 4 كلهم في v64_results عشان Brier الصح
print("=== كل الـ 4 في v64_results ===")
v = json.load(open('data/sigma_v64_results.json'))
items = v if isinstance(v, list) else v.get('matches', [])
for it in items:
    print(it)

# 2. هات نتايج المانيا كلها
print("\n=== جلب BL1 + BL2 + DFB ===")
all_results = []  # (home, away, date, hg, ag, league)
for league, code in [('BL1','bl1'), ('BL2','bl2'), ('DFB','dfbpokal')]:
    try:
        url = f"https://api.openligadb.de/getmatchdata/{code}/2025"
        req = urllib.request.Request(url, headers={'User-Agent':'Sigma/1.0'})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode())
        c=0
        for m in data:
            res = m.get('matchResults', [])
            if not res: continue
            last = res[-1]
            hg = last.get('pointsTeam1'); ag = last.get('pointsTeam2')
            if hg is None: continue
            h = m.get('team1',{}).get('teamName','')
            a = m.get('team2',{}).get('teamName','')
            dt = (m.get('matchDateTime') or '')[:10]
            all_results.append((h,a,dt,hg,ag,league))
            c+=1
        print(f"{league} ({code}): {c} نتيجة منتهية")
    except Exception as e:
        print(f"{league} فشل: {e}")

# 3. طابق الـ Bulk
bulk = json.load(open('data/sigma_bulk_predictions.json'))
bulk = bulk if isinstance(bulk, list) else bulk.get('matches', [])
joined=[]
unmatched=[]
brier_sum=0; brier_n=0; acc=0; acc_n=0
per_league = collections.defaultdict(lambda: [0,0])
for b in bulk:
    h = b.get('home_team') or b.get('home','')
    a = b.get('away_team') or b.get('away','')
    dt = b.get('date','')
    best=None; best_score=0
    for (rh,ra,rdt,hg,ag,lg) in all_results:
        if abs((sim(h,rh)+sim(a,ra))/2) < 0.75: continue
        # التاريخ قريب - فرق يوم واحد مسموح
        if rdt and dt and abs((__import__('datetime').date.fromisoformat(rdt) - __import__('datetime').date.fromisoformat(dt)).days) > 2: continue
        sc = (sim(h,rh)+sim(a,ra))/2
        if sc > best_score:
            best_score=sc; best=(rh,ra,rdt,hg,ag,lg)
    if not best:
        unmatched.append(b)
        continue
    rh,ra,rdt,hg,ag,lg = best
    actual = "1" if hg>ag else "X" if hg==ag else "2"
    p1 = float(b.get('prob_1',0))/100; px = float(b.get('prob_X',0))/100; p2 = float(b.get('prob_2',0))/100
    brier = (p1-(1 if actual=="1" else 0))**2 + (px-(1 if actual=="X" else 0))**2 + (p2-(1 if actual=="2" else 0))**2
    brier_sum+=brier; brier_n+=1
    # هل التوقع الاصلي صح؟ DC1X مثلا
    dc1x = float(b.get('DC1X',0))
    # نعتبر التوقع صح لو DC1X >= 70 و actual في 1/X او DCX2 و actual في X/2
    # هنحسب accuracy على 1X2 الاساسي: اعلى احتمال
    pred_1x2 = max([("1",p1),("X",px),("2",p2)], key=lambda x: x[1])[0]
    hit = 1 if pred_1x2==actual else 0
    acc+=hit; acc_n+=1
    per_league[b.get('league','?')][0]+=brier; per_league[b.get('league','?')][1]+=1
    # error_type
    if hit: err="correct"
    elif p1>=0.80 or px>=0.80 or p2>=0.80: err="model_overconfidence"
    else: err="model_error"
    joined.append({**b, "actual_score": f"{hg}-{ag}", "actual_1X2": actual, "brier": round(brier,3), "pred_1X2": pred_1x2, "hit": hit, "error_type": err, "matched_openligadb": f"{rh} vs {ra} {rdt}", "match_score": round(best_score,2)})

print(f"\n=== النتيجة ===")
print(f"الـ Bulk: {len(bulk)} | اتطابق: {len(joined)} | متطابقش: {len(unmatched)}")
if brier_n:
    print(f"Brier الكلي: {brier_sum/brier_n:.3f} على {brier_n} ماتش (0 ممتاز، 2 سيئ)")
    print(f"Accuracy 1X2: {acc/acc_n*100:.1f}% على {acc_n} ماتش")
    for lg,(s,n) in per_league.items():
        print(f" - {lg}: Brier {s/n:.3f} على {n} ماتش")
    # Bayesian جديد: n بقى كبير، فمعدل التعلم هيزيد
    n = brier_n
    lr = 0.01 if n<50 else 0.03 if n<200 else 0.05 if n<500 else 0.10
    print(f"Bayesian: n={n} -> lr={lr} (كان 0.01 لما كان n=4)")
    json.dump(joined, open('data/sigma_results_joined.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
    json.dump(unmatched, open('data/sigma_unmatched.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
    print("اتحفظ في data/sigma_results_joined.json + data/sigma_unmatched.json")
    print("الـ 4 بتوع UNL هيكونوا في unmatched - دول هيتجابوا من international_results اللي في sigma-auto.yml")
else:
    print("مفيش تطابق - راجع اسماء الفرق والتواريخ")
