import json, math, random

# ===== الطبقة 1: الادراك - Time-Decay والتنقية =====
def time_decay(days_ago, half_life=30):
    # مباراة من 5 ايام وزنها اكبر من مباراة من 60 يوم
    return 0.5 ** (days_ago / half_life)

def anomaly_check(absences=0, lineup_change=False, bad_weather=False, fatigue=0):
    # كشف الشذوذ: غيابات مؤثرة او تغيير تشكيل مفاجئ او طقس قاسي
    reasons = []
    if absences >= 2:
        reasons.append(f"غيابات مؤثرة: {absences}")
    if lineup_change:
        reasons.append("تغيير تشكيل مفاجئ")
    if bad_weather:
        reasons.append("طقس قاسي")
    if fatigue >= 3:
        reasons.append("ارهاق ضغط مباريات")
    penalty = min(0.15, 0.04 * absences + (0.07 if lineup_change else 0) + (0.05 if bad_weather else 0))
    return reasons, penalty

# ===== الطبقة 2: النمذجة - Dixon-Coles + Elo ديناميكي =====
def poisson_pmf(k, lam):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def dixon_coles_matrix(xg_h, xg_a, rho=-0.13, max_goals=5):
    # مصفوفة من 0-0 لحد 5-5 مع تصحيح النتايج القليلة
    mat = {}
    for h in range(max_goals+1):
        for a in range(max_goals+1):
            p = poisson_pmf(h, xg_h) * poisson_pmf(a, xg_a)
            if h==0 and a==0:
                tau = 1 - xg_h*xg_a*rho
            elif h==0 and a==1:
                tau = 1 + xg_h*rho
            elif h==1 and a==0:
                tau = 1 + xg_a*rho
            elif h==1 and a==1:
                tau = 1 - rho
            else:
                tau = 1.0
            mat[(h,a)] = p * tau
    # تطبيع
    s = sum(mat.values())
    for k in mat: mat[k] /= s
    return mat

def elo_update(elo, opp_elo, result, goal_diff, k_base=20, importance=1.0):
    # result: 1 فوز، 0.5 تعادل، 0 خسارة
    exp = 1 / (1 + 10 ** ((opp_elo - elo)/400))
    k = k_base * importance * (1 + 0.3 * min(abs(goal_diff), 3))
    return elo + k * (result - exp)

def poisson_sample(lam):
    # Knuth - بدون numpy
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        p *= random.random()
        if p <= L: break
        k += 1
    return k

# ===== الطبقة 3: OR - مونت كارلو + قيود التحسين =====
def monte_carlo(xg_h, xg_a, n=10000, rho=-0.13):
    random.seed(42)
    counts = {"1":0, "X":0, "2":0, "1X":0, "X2":0}
    score_counts = {}
    for _ in range(n):
        # محاكاة مع عشوائية الطرد والاصابة كتشويش صغير
        lam_h = max(0.1, xg_h * random.uniform(0.85, 1.15))
        lam_a = max(0.1, xg_a * random.uniform(0.85, 1.15))
        h = poisson_sample(lam_h)
        a = poisson_sample(lam_a)
        score_counts[(h,a)] = score_counts.get((h,a), 0) + 1
        if h > a: counts["1"] += 1; counts["1X"] += 1
        elif h == a: counts["X"] += 1; counts["1X"] += 1; counts["X2"] += 1
        else: counts["2"] += 1; counts["X2"] += 1
    probs = {k: v/n*100 for k,v in counts.items()}
    top3 = sorted(score_counts.items(), key=lambda x: -x[1])[:3]
    top3_str = " / ".join([f"{h}-{a} {c/n*100:.1f}%" for (h,a),c in top3])
    return probs, top3_str

def apply_caps(prob, pick_type, elo_known=True):
    # كاب 86 لـ 1X/X2/DNB، 75 لـ 1X2، 52 لو Elo مش معروف
    cap = 86 if pick_type in ["1X","X2","DNB"] else 75
    if not elo_known: cap = min(cap, 52)
    capped = min(prob, cap)
    return capped, cap, prob > cap

def ev_and_kelly(prob_pct, odds, fraction=0.25):
    p = prob_pct/100
    q = 1-p
    b = odds - 1
    if b <= 0: return -1, 0
    ev = p * odds - 1
    kelly_full = (p*b - q)/b if b!=0 else 0
    kelly_full = max(0, kelly_full)
    return ev, kelly_full * fraction * 100

def brier_score(p1, px, p2, actual):
    # actual: 1 او X او 2
    probs = {"1":p1/100, "X":px/100, "2":p2/100}
    return sum((probs[k] - (1 if k==actual else 0))**2 for k in probs)

def or_decision(prob_capped, ev, pick_type, anomaly_reasons=None):
    if anomaly_reasons:
        return f"ABSTAIN - شذوذ: {anomaly_reasons}"
    if ev < 0:
        return f"ABSTAIN - EV سالب {ev:.3f}"
    if pick_type in ["1X","X2","DNB"]:
        if prob_capped >= 86:
            return "SAFE-ON-CAP - على الكاب 86% + EV موجب"
        risk = 100 - prob_capped
        return f"ABSTAIN - مخاطرة {risk:.1f}% تحت الكاب 86%"
    else:
        if prob_capped >= 75:
            return "SAFE-ON-CAP - على الكاب 75% + EV موجب"
        risk = 100 - prob_capped
        return f"ABSTAIN - مخاطرة {risk:.1f}% تحت الكاب 75%"

# ===== اختبار على 5 ماتشات افتراضية =====
tests = [
    {"name":"1- متكافئة","xg_h":1.4,"xg_a":1.3,"elo_diff":0,"abs":0,"odds":2.6,"pick":"1X","pick_prob":55},
    {"name":"2- قوي ضد ضعيف (【entity-بايرن¦canonical_name=بايرن】)","xg_h":3.5,"xg_a":0.78,"elo_diff":264,"abs":0,"odds":1.12,"pick":"1","pick_prob":85.2},
    {"name":"3- قوي ضد ضعيف مع غيابات","xg_h":2.2,"xg_a":1.0,"elo_diff":200,"abs":3,"odds":1.45,"pick":"1X","pick_prob":82},
    {"name":"4- ديربي","xg_h":1.6,"xg_a":1.5,"elo_diff":20,"abs":1,"odds":2.4,"pick":"X2","pick_prob":58},
    {"name":"5- دفاعية قليلة","xg_h":0.9,"xg_a":0.8,"elo_diff":10,"abs":0,"odds":2.8,"pick":"1X","pick_prob":70},
]

print("=== اختبار المحرك الجديد - 5 ماتشات ===")
for t in tests:
    reasons, penalty = anomaly_check(absences=t["abs"])
    # طبق عقوبة الشذوذ على الاحتمال
    prob_adj = t["pick_prob"] * (1 - penalty)
    capped, cap, was_over = apply_caps(prob_adj, t["pick"], elo_known=True)
    probs_mc, top3 = monte_carlo(t["xg_h"], t["xg_a"], n=2000)
    ev, kelly25 = ev_and_kelly(capped, t["odds"])
    dec = or_decision(capped, ev, t["pick"], reasons)
    print(f"\n{t['name']} | xG {t['xg_h']}-{t['xg_a']} | فرق Elo {t['elo_diff']}")
    print(f"  احتمال قبل الكاب {t['pick_prob']:.1f}% -> بعد الشذوذ {prob_adj:.1f}% -> بعد الكاب {capped:.1f}% (كاب {cap}%) كسر؟ {was_over}")
    print(f"  مونت كارلو 1X={probs_mc['1X']:.1f}% X2={probs_mc['X2']:.1f}% | Top3: {top3}")
    print(f"  EV={ev:.3f} Kelly25={kelly25:.2f}% | شذوذ: {reasons if reasons else 'لا يوجد'}")
    print(f"  قرار OR: {dec}")

# ===== Brier على النتايج الحقيقية الـ 4 =====
print("\n=== Brier على النتايج المؤكدة الـ 4 ===")
real = [
    ("【entity-بايرن¦canonical_name=بايرن】 1-1 كولن", 85.2, 10.4, 4.4, "X"),
    ("اتلتيك 0-1 اسبانيول", 55, 25, 20, "2"),
    ("تروا 3-1 لوهافر", 45, 28, 27, "1"),
    ("الاهلي 3-1 【entity-النصر¦canonical_name=النصر】", 40, 28, 32, "1"),
]
for name, p1, px, p2, act in real:
    print(f"{name}: Brier={brier_score(p1,px,p2,act):.3f} (0 ممتاز، 2 سيئ)")

# ===== تطبيق على ملف اللايف الحقيقي =====
print("\n=== تطبيق على sigma_site.json ===")
try:
    d = json.load(open('data/sigma_site.json'))
    matches = d['matches']
    over = 0
    abstain = 0
    for m in matches:
        dc = float(m.get('dc_prob', 0))
        pick = m.get('dc_pick', '1X')
        capped, cap, was_over = apply_caps(dc, pick, elo_known=True)
        if was_over: over += 1
        risk = 100 - capped
        if risk > 13: abstain += 1
    print(f"عدد الماتشات: {len(matches)} | فوق الكاب 86%: {over} | هيبقوا ABSTAIN تحت 13%: {abstain}")
    print("مثال يوفنتوس: dc_prob 88.2 -> بعد الكاب 86.0 -> مخاطرة 14.0% -> ABSTAIN")
except Exception as e:
    print("مش قادر اقرأ sigma_site.json:", e)

print("\n=== هيكل قاعدة البيانات المقترح ===")
print('{"predictions": [{"match_id": "...", "date": "...", "home": "...", "away": "...", "league": "...", "p1": ..., "pX": ..., "p2": ..., "dc_prob_capped": ..., "ev": ..., "kelly25": ..., "or_decision": "...", "anomaly": []}], "calibration": [{"league": "...", "brier": ..., "weight": ..., "last_update": "..."}]}')
