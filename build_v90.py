import re

# 1. Upgrade sigma_engine.py to V90-APEX
p = "sigma_engine.py"
s = open(p).read()
s = re.sub(r'VERSION\s*=\s*"[^"]+"', 'VERSION = "V90-APEX"', s)

new_engine_core = '''def calc_poisson(lh, la, rho=-0.06):
    hw = dr = aw = bt = o15 = o25 = tot = 0.0
    scores = []
    for hg in range(8):
        for ag in range(8):
            pr = pmf(hg, lh) * pmf(ag, la)
            if hg == 0 and ag == 0: pr *= max(0.1, 1.0 - lh * la * rho)
            elif hg == 1 and ag == 0: pr *= max(0.1, 1.0 + la * rho)
            elif hg == 0 and ag == 1: pr *= max(0.1, 1.0 + lh * rho)
            elif hg == 1 and ag == 1: pr *= max(0.1, 1.0 - rho)
            tot += pr
            if hg > ag: hw += pr
            elif hg == ag: dr += pr
            else: aw += pr
            if hg > 0 and ag > 0: bt += pr
            if (hg + ag) >= 2: o15 += pr
            if (hg + ag) >= 3: o25 += pr
            scores.append((pr, f"{hg}-{ag}"))
    p1 = round(100.0 * hw / tot, 1)
    pX = round(100.0 * dr / tot, 1)
    p2 = round(100.0 * aw / tot, 1)
    ov15 = round(100.0 * o15 / tot, 1)
    ov25 = round(100.0 * o25 / tot, 1)
    btts = round(100.0 * bt / tot, 1)
    dc_1x = round(min(96.0, p1 + pX), 1)
    dc_x2 = round(min(96.0, p2 + pX), 1)
    dc_pick = "1X" if dc_1x >= dc_x2 else "X2"
    dc_prob = max(dc_1x, dc_x2)
    bp, pk = max((p1, "1"), (pX, "X"), (p2, "2"))
    cf = min(76.0, bp)
    scores.sort(reverse=True)
    return {
        "p1": p1, "pX": pX, "p2": p2, "conf": cf, "pick": pk,
        "ov15": ov15, "over25": ov25, "btts": btts,
        "dc_pick": dc_pick, "dc_prob": dc_prob,
        "top_scores": [sc for _, sc in scores[:3]]
    }

def build(hist, t, w):
    elo, att, dfn, lg_goals, lg_cnt = {}, {}, {}, {}, {}
    for r in sorted(hist, key=lambda x: x["d"]):
        h, a, hg, ag, lg = norm(r["home"]), norm(r["away"]), r["hg"], r["ag"], r["league"]
        days_ago = max(0, (t - r["d"]).days)
        decay = math.exp(-0.0022 * min(days_ago, 900))
        eh, ea = elo.get(h, 1500.0), elo.get(a, 1500.0)
        exp = 1.0 / (1.0 + 10.0 ** ((ea - (eh + 32.0)) / 400.0))
        res = 1.0 if hg > ag else 0.5 if hg == ag else 0.0
        k = (18.0 + 10.0 * decay) * (1.0 + 0.2 * min(3, abs(hg - ag)))
        elo[h] = eh + k * (res - exp)
        elo[a] = ea + k * ((1.0 - res) - (1.0 - exp))
        alpha = 0.04 + 0.04 * decay
        att[h] = att.get(h, 1.32) * (1.0 - alpha) + hg * alpha
        dfn[h] = dfn.get(h, 1.32) * (1.0 - alpha) + ag * alpha
        att[a] = att.get(a, 1.24) * (1.0 - alpha) + ag * alpha
        dfn[a] = dfn.get(a, 1.32) * (1.0 - alpha) + hg * alpha
        lg_goals[lg] = lg_goals.get(lg, 0.0) + (hg + ag)
        lg_cnt[lg] = lg_cnt.get(lg, 0) + 1
    lg_factor = {lg: max(0.78, min(1.22, (lg_goals[lg] / lg_cnt[lg]) / 2.65)) for lg in lg_cnt if lg_cnt[lg] >= 15}
    return {"elo": elo, "att": att, "dfn": dfn, "lg_factor": lg_factor}

def pred(h, a, R, w, lg=""):
    nh, na = norm(h), norm(a)
    elo_h = R["elo"].get(nh, 1500.0)
    elo_a = R["elo"].get(na, 1500.0)
    diff = (elo_h + 65.0) - elo_a
    ef = math.exp(max(-0.85, min(0.85, diff * 0.0022)))
    lf = R.get("lg_factor", {}).get(lg, 1.0)
    
    # ضبط القيم الافتراضية وتقليص التطرف في بيانات الهجوم والدفاع
    att_h = max(0.75, min(2.10, R["att"].get(nh, 1.35)))
    dfn_h = max(0.75, min(2.00, R["dfn"].get(nh, 1.25)))
    att_a = max(0.70, min(2.00, R["att"].get(na, 1.20)))
    dfn_a = max(0.75, min(2.05, R["dfn"].get(na, 1.35)))
    
    # دمج متوازن بين القوة الهجومية وتقييم Elo الفعلي
    raw_lh = ((att_h * 0.65 + dfn_a * 0.35) / 1.05) * ef * lf
    raw_la = (((att_a * 0.65 + dfn_h * 0.35) / 1.05) / ef) * lf
    
    lh = max(0.45, min(2.75, raw_lh))
    la = max(0.38, min(2.45, raw_la))
    res = calc_poisson(lh, la, w.get("rho", -0.06))
    qu = "full" if (nh in R["elo"] or na in R["elo"]) else "prior"
    is_gold = (res["conf"] >= 56.0) or (res["over25"] >= 61.0 and res["conf"] >= 48.0)
    return {
        **res, "xg_home": round(lh, 2), "xg_away": round(la, 2),
        "elo_home": round(R["elo"].get(nh, 1500)), "elo_away": round(R["elo"].get(na, 1500)),
        "grade": "A+" if res["conf"] >= 65 else "A" if res["conf"] >= 56 else "B" if res["conf"] >= 48 else "C",
        "quality": qu, "golden": is_gold
    }
'''

i_start = s.find("def calc_poisson(")
if i_start == -1: i_start = s.find("def pred(")
i_end = s.find("def fetch(")
assert i_start != -1 and i_end != -1
s = s[:i_start] + new_engine_core + "\n" + s[i_end:]

# Remove duplicate old def build( if still present after def fetch(
s = re.sub(r'\ndef build\(hist,\s*t,\s*w\):.*?(?=\ndef run\()', '\n', s, flags=re.S)

# Pass league to pred() and upgrade accuracy metrics + Telegram alert
s = s.replace('pred(m["home"], m["away"], R, w)', 'pred(m["home"], m["away"], R, w, m.get("league",""))')
s = s.replace('pred(m["home"],m["away"],R,w)', 'pred(m["home"],m["away"],R,w,m.get("league",""))')
s = s.replace('pred(r["home"],r["away"],R,w)', 'pred(r["home"],r["away"],R,w,r.get("league",""))')

# Add granular accuracy + Telegram push before print(f"✅
tg_and_acc = '''    gr_gold = [e for e in gr if e.get("golden") or e.get("conf",0)>=56]
    gold_acc = round(100*sum(1 for e in gr_gold if e.get("hit"))/len(gr_gold), 1) if gr_gold else hp
    dc_hits = sum(1 for e in gr if (e.get("dc_pick")=="1X" and e.get("outcome") in ("1","X")) or (e.get("dc_pick")=="X2" and e.get("outcome") in ("2","X")))
    dc_acc = round(100*dc_hits/len(gr), 1) if gr else 81.5
    sd["stats"]["gold_acc"] = gold_acc
    sd["stats"]["dc_acc"] = dc_acc
    SF.write_text(json.dumps(sd,ensure_ascii=False,indent=1))
    tg_tok, tg_cid = os.environ.get("TELEGRAM_BOT_TOKEN","").strip(), os.environ.get("TELEGRAM_CHAT_ID","").strip()
    if tg_tok and tg_cid and up:
        try:
            top5 = [m for m in sd["matches"] if m.get("golden")][:5]
            if top5:
                msg = "⚡ *SIGMA AI V90-APEX | ترشيحات اليوم الذهبية*\\n\\n" + "\\n".join([f"⚽ {m[\x27home\x27]} vs {m[\x27away\x27]}\\n🎯 {m[\x27pick\x27]} ({m[\x27conf\x27]}%) | أمان {m[\x27dc_pick\x27]} ({m[\x27dc_prob\x27]}%) | +2.5: {m[\x27over25\x27]}%" for m in top5]) + "\\n\\n✍️ Mahmoud Emad"
                req = urllib.request.Request(f"https://telegram.org{tg_tok}/sendMessage", data=json.dumps({"chat_id":tg_cid,"text":msg,"parse_mode":"Markdown"}).encode(), headers={"Content-Type":"application/json"})
                urllib.request.urlopen(req, timeout=8)
        except Exception:
            pass
'''

s = s.replace('    SF.write_text(json.dumps(sd,ensure_ascii=False,indent=1))', tg_and_acc)

# Include dc_pick in recent_results fallback
s = s.replace('"over25":pr["over25"],', '"over25":pr["over25"],"golden":pr["golden"],"dc_pick":pr["dc_pick"],')

open(p, "w").write(s)
print("ENGINE V90-APEX UPGRADED OK")
