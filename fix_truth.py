import re

p = "sigma_engine.py"
s = open(p).read()

# Clean, foolproof Poisson & Prediction engine where Home is ALWAYS index 0 / i / p1 / xg_home
clean_math = '''def calc_poisson(lh, la, rho=-0.06):
    home_win = draw = away_win = btts = over25 = total = 0.0
    scores = []
    for home_g in range(8):
        for away_g in range(8):
            pr = pmf(home_g, lh) * pmf(away_g, la)
            if home_g == 0 and away_g == 0: pr *= max(0.1, 1.0 - lh * la * rho)
            elif home_g == 1 and away_g == 0: pr *= max(0.1, 1.0 + la * rho)
            elif home_g == 0 and away_g == 1: pr *= max(0.1, 1.0 + lh * rho)
            elif home_g == 1 and away_g == 1: pr *= max(0.1, 1.0 - rho)
            total += pr
            if home_g > away_g: home_win += pr
            elif home_g == away_g: draw += pr
            else: away_win += pr
            if home_g > 0 and away_g > 0: btts += pr
            if (home_g + away_g) >= 3: over25 += pr
            scores.append((pr, f"{home_g}-{away_g}"))
    p1 = round(100.0 * home_win / total, 1)
    pX = round(100.0 * draw / total, 1)
    p2 = round(100.0 * away_win / total, 1)
    ov25 = round(100.0 * over25 / total, 1)
    bt = round(100.0 * btts / total, 1)
    bp, pk = max((p1, "1"), (pX, "X"), (p2, "2"))
    cf = min(76.0, bp)
    scores.sort(reverse=True)
    return p1, pX, p2, ov25, bt, bp, pk, cf, [sc for _, sc in scores[:3]]

def pred(h, a, R, w):
    diff = (R["elo"].get(h, 1500.0) + 32.0) - R["elo"].get(a, 1500.0)
    ef = math.exp(max(-0.75, min(0.75, diff * 0.00125)))
    att_h, dfn_h = R["att"].get(h, 1.30), R["dfn"].get(h, 1.30)
    att_a, dfn_a = R["att"].get(a, 1.22), R["dfn"].get(a, 1.30)
    lh = max(0.45, min(2.9, ((att_h + dfn_a) / 2.10) * ef))
    la = max(0.40, min(2.6, ((att_a + dfn_h) / 2.10) / ef))
    p1, px, p2, ov25, bt, bp, pk, cf, top_sc = calc_poisson(lh, la, w.get("rho", -0.06))
    qu = "full" if (h in R["elo"] or a in R["elo"]) else "prior"
    is_gold = (cf >= 56.0) or (ov25 >= 61.0 and cf >= 48.0)
    return {
        "p1": p1, "pX": px, "p2": p2, "conf": cf, "btts": bt, "over25": ov25,
        "xg_home": round(lh, 2), "xg_away": round(la, 2),
        "elo_home": round(R["elo"].get(h, 1500)), "elo_away": round(R["elo"].get(a, 1500)),
        "pick": pk, "grade": "A+" if cf >= 65 else "A" if cf >= 56 else "B" if cf >= 48 else "C",
        "quality": qu, "golden": is_gold, "top_scores": top_sc
    }
'''

i1 = s.find("def calc_poisson(")
if i1 == -1: i1 = s.find("def pred(")
i2 = s.find("def fetch(")
assert i1 != -1 and i2 != -1
s = s[:i1] + clean_math + "\n" + s[i2:]
open(p, "w").write(s)

# Fix index.html so Home is on LEFT and Away is on RIGHT inside a clean LTR match box (zero RTL confusion)
h = open("index.html").read()
h = h.replace("SIGMA AI V82 MASTER", "SIGMA AI V83 VERIFIED")
h = h.replace(
    '<div class="teams"><span>🏟️ ${m.home}</span><span style="color:var(--mt)">VS</span><span>✈️ ${m.away}</span></div>',
    '<div class="teams" dir="ltr"><span>🏟️ ${m.home}</span><span style="color:var(--mt)">VS</span><span>${m.away} ✈️</span></div>'
)
h = h.replace(
    '<div class="probs">',
    '<div class="probs" dir="ltr">'
)
h = h.replace(
    '<b>${m.xg_home}-${m.xg_away}</b>',
    '<b dir="ltr">${m.xg_home} - ${m.xg_away}</b>'
)
h = h.replace(
    '<b dir="ltr">${m.xg_home} - ${m.xg_away}</b>',
    '<b dir="ltr">${m.xg_home} - ${m.xg_away}</b>'
)
open("index.html", "w").write(h)
print("MATH & LTR DISPLAY FIXED OK")
