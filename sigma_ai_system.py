import json, os, collections, math

# ===== 1. Context Modifier =====
def load_context():
    try:
        return json.load(open('data/context.json'))
    except:
        return {}
    # مثال context.json: {"【entity-FC Bayern München¦canonical_name=FC Bayern München】": -0.25, "【entity-1. FC Köln¦canonical_name=1. FC Köln】": 0.0}
    # -0.25 = غياب هداف، +0.15 = رجوع نجم، 0 = عادي

def apply_context(xg_h, xg_a, ctx_h, ctx_a):
    # ctx من -0.25 لـ +0.25، بيتضاف لـ xG قبل مونت كارلو
    return max(0.05, xg_h + ctx_h), max(0.05, xg_a + ctx_a)

# ===== 2. Ensemble Stacking - اوزان من Brier =====
def ensemble_weights(calibration):
    # calibration: {league: {brier_dixon, brier_elo, brier_xg}}
    # وزن = 1 / Brier، وكل ما Brier اقل الوزن اكبر
    w = {}
    for lg, c in calibration.items():
        inv = {}
        for k in ['dixon','elo','xg']:
            b = c.get(f'brier_{k}', 0.5)
            inv[k] = 1.0 / max(0.1, b)
        s = sum(inv.values())
        w[lg] = {k: round(v/s, 3) for k,v in inv.items()}
    return w

def ensemble_prob(p_dixon, p_elo, p_xg, weights):
    return p_dixon*weights['dixon'] + p_elo*weights['elo'] + p_xg*weights['xg']

# ===== 3. Composite Confidence Index =====
def composite_confidence(prob, variance, ev):
    prob_score = round(prob, 1)  # الاحتمال الرياضي الخام
    stability = round(max(0, 100 - variance*100), 1)  # عكس التشتت
    # Value_Rating: تقاطع احتمال + استقرار
    if prob >= 86 and stability >= 75 and ev > 0.05: rating = "A+"
    elif prob >= 86 and stability >= 60: rating = "A"
    elif prob >= 80 and stability >= 60: rating = "B"
    else: rating = "C"
    return prob_score, stability, rating

# ===== 4. Odds Drift =====
def odds_drift(open_odds, close_odds, prob):
    if not open_odds or not close_odds: return prob, ""
    drift = (close_odds - open_odds) / open_odds
    if drift < -0.15:  # هبوط حاد >15% = معلومة سوق
        return max(50, prob - 10), "SUSPICIOUS - هبوط اودز حاد"
    if drift < -0.08:
        return max(50, prob - 5), "WATCH - هبوط اودز"
    return prob, ""

# ===== 5. Dynamic LR + Caps =====
def dynamic_lr(n):
    if n < 50: return 0.01
    if n < 200: return 0.03
    if n < 500: return 0.05
    return 0.10

def apply_caps(dc_prob, pick):
    cap = 86 if pick in ["1X","X2","DNB"] else 75
    # لو Elo مجهول، كاب 52%
    return min(dc_prob, cap), cap

# ===== التشغيل على الـ Bulk + الـ Joined =====
print("=== Sigma AI System - Ensemble + Context + Composite ===")
ctx = load_context()
print(f"Context loaded: {len(ctx)} فريق")

# اوزان افتراضية لو مفيش معايرة لسه - هتتحدث بعد join
calib = {"BL1": {"brier_dixon":0.45,"brier_elo":0.52,"brier_xg":0.48},
         "BL2": {"brier_dixon":0.50,"brier_elo":0.55,"brier_xg":0.49}}
weights = ensemble_weights(calib)
print(f"Ensemble weights: {weights}")

# جرب على اول ماتش في الـ Bulk لو موجود
try:
    bulk = json.load(open('data/sigma_bulk_predictions.json'))
    bulk = bulk if isinstance(bulk, list) else bulk.get('matches', [])
    # مثال: بايرن vs كولن
    b = bulk[0]
    xg_h = float(b.get('xG_home', 1.5)); xg_a = float(b.get('xG_away', 1.0))
    ch = ctx.get(b.get('home_team',''), 0); ca = ctx.get(b.get('away_team',''), 0)
    xg_h2, xg_a2 = apply_context(xg_h, xg_a, ch, ca)
    print(f"\nمثال: {b.get('home_team')} vs {b.get('away_team')}")
    print(f" xG قبل Context: {xg_h}-{xg_a} | بعد Context ({ch}/{ca}): {xg_h2:.2f}-{xg_a2:.2f}")
    # Ensemble تقديري: Dixon = prob_1، Elo = prob_1 +- 3، xG = prob_1 +- 2
    p1 = float(b.get('prob_1',0))
    ens = ensemble_prob(p1, p1-2, p1+1, weights.get(b.get('league','BL1'), {'dixon':0.4,'elo':0.3,'xg':0.3}))
    print(f" Ensemble prob_1: {p1}% -> {ens:.1f}%")
    # Composite
    ps, st, rating = composite_confidence(ens, 0.20, 0.08)
    print(f" Composite: Prob {ps}% | Stability {st} | Value {rating}")
    # Caps
    capped, cap = apply_caps(float(b.get('DC1X',0)), "1X")
    print(f" Caps: DC1X {b.get('DC1X')}% -> {capped}% (كاب {cap}%)")
except Exception as e:
    print("Bulk مش موجود لسه:", e)

# حفظ اوزان Ensemble
json.dump({"weights": weights, "calibration": calib}, open('data/sigma_ensemble_weights.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
print("\nاتحفظ في data/sigma_ensemble_weights.json")
print("الخطوة الجاية: run_pipeline.sh هيشغل كل حاجة بالترتيب")
