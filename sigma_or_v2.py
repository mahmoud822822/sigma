import json, math, difflib, collections

# ===== 1. معدل تعلم ديناميكي - Bayesian محافظ =====
def dynamic_lr(n_results):
    if n_results < 50: return 0.01
    if n_results < 200: return 0.03
    if n_results < 500: return 0.05
    return 0.10

def bayesian_update(prior_prob, observed_prob, n_results):
    # مثال: n=4 -> وزن الداتا 5% بس
    lr = dynamic_lr(n_results)
    # وزن الداتا يكبر مع عدد النتايج: w = n / (n+100)
    w_data = n_results / (n_results + 100) if n_results>0 else 0.05
    # نضرب في lr عشان يبقى محافظ
    w_data = w_data * (lr / 0.10) if lr>0 else 0.05
    w_data = min(0.05, max(0.01, w_data)) if n_results<50 else w_data
    w_prior = 1 - w_data
    return prior_prob * w_prior + observed_prob * w_data, w_data, lr

# ===== 2. تصنيف الخطأ - Error Audit Log =====
def classify_error(pred_prob, actual_outcome, pick, had_red_card=False, had_penalty=False, had_anomaly=False):
    # actual_outcome: 1 او X او 2، pick: 1X او X2 او 1
    hit = False
    if pick=="1X" and actual_outcome in ["1","X"]: hit=True
    if pick=="X2" and actual_outcome in ["X","2"]: hit=True
    if pick in ["1","X","2"] and pick==actual_outcome: hit=True
    if hit: return "correct"
    if had_red_card or had_penalty: return "random_event - طرد/جزاء"
    if had_anomaly: return "anomaly - غيابات/طقس"
    if pred_prob >= 80: return "model_overconfidence - ثقة مبالغ فيها"
    return "model_error - تقدير xG"

# ===== 3. محفظة OR - TOP_PICK =====
def select_top_picks(matches, top_n=12):
    # matches: قايمة فيها dc_prob_capped, ev, variance, league, date
    scored = []
    for m in matches:
        prob = m.get('dc_prob_capped', 0)
        ev = m.get('ev', 0)
        var = m.get('variance', 0.25)
        # لو مفيش EV لان مفيش اودز في ملف اللايف، نستخدم prob كمؤشر
        if ev == 0:
            ev = (prob - 70) / 100.0  # تقدير مبدئي
        score = ev * (1 - var) / ((100 - prob)/100 + 0.1)
        m['_or_score'] = score
        scored.append(m)
    scored.sort(key=lambda x: -x['_or_score'])
    picked = []
    per_league = collections.Counter()
    per_date = collections.Counter()
    for m in scored:
        if m.get('dc_prob_capped',0) < 86: continue
        if m.get('ev',0) < 0: continue
        lg = m.get('league','?')
        dt = m.get('date','?')
        if per_league[lg] >= 2: continue
        if per_date[dt] >= 3: continue
        m['TOP_PICK'] = True
        picked.append(m)
        per_league[lg]+=1
        per_date[dt]+=1
        if len(picked) >= top_n: break
    return picked

# ===== اختبار البايزي على الـ 4 نتايج =====
print("=== Bayesian - حماية من 4 نتايج ===")
for n in [4, 50, 150, 400, 600]:
    new, w, lr = bayesian_update(85.2, 50.0, n)
    print(f"عدد النتايج {n} | lr={lr} | وزن الداتا {w*100:.1f}% | وزن القاعدة {(1-w)*100:.1f}% | 85.2% -> {new:.1f}%")

# ===== تصنيف الـ 4 نتايج الحقيقية =====
print("\n=== Error Audit - الـ 4 نتايج ===")
real4 = [
    ("بايرن 1-1 كولن", 85.2, "1", "X", False, False, False),
    ("اتلتيك 0-1 اسبانيول", 55, "1X", "2", False, False, False),
    ("تروا 3-1 لوهافر", 45, "1", "1", False, False, False),
    ("الاهلي 3-1 【entity-النصر¦canonical_name=النصر】", 40, "1", "1", False, False, False),
]
for name, prob, pick, act, rc, pen, an in real4:
    print(f"{name}: {classify_error(prob, act, pick, rc, pen, an)}")

# ===== تطبيق على اللايف بمنطق جديد =====
print("\n=== اللايف - بعد اصلاح منطق القرار ===")
try:
    d = json.load(open('data/sigma_site.json'))
    matches = d.get('matches', [])
    over=0; candidates=[]
    for m in matches:
        dc = float(m.get('dc_prob', 0))
        pick = m.get('dc_pick','1X')
        cap = 86 if pick in ["1X","X2","DNB"] else 75
        capped = min(dc, cap)
        if dc > cap: over+=1
        if capped >= 86 and pick in ["1X","X2","DNB"]:
            candidates.append({'home':m.get('home'),'away':m.get('away'),'league':m.get('league'),'date':m.get('date'),'dc_prob_capped':capped,'ev':0,'variance':0.2})
    print(f"عدد الماتشات: {len(matches)} | فوق الكاب: {over} | مرشحين على الكاب 86%: {len(candidates)}")
    top = select_top_picks(candidates, top_n=12)
    print(f"TOP_PICK بعد فلتر التنويع (2 لكل دوري / 3 لكل يوم): {len(top)}")
    for t in top[:12]:
        print(f" - TOP_PICK: {t.get('home')} vs {t.get('away')} | {t.get('league')} | {t.get('date')} | {t.get('dc_prob_capped')}%")
    # حفظ المرشحين
    json.dump({'top_picks': top, 'candidates_on_cap': candidates}, open('data/sigma_or_top_picks.json','w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print("اتحفظ في data/sigma_or_top_picks.json")
except Exception as e:
    print("مشكلة في قراية اللايف:", e)
