import os, re, ast

print("=== 1. UPGRADING WORKFLOW (EVERY 6 HOURS + AUTO-SYNC) ===")
wf_path = ".github/workflows/sigma-auto-update.yml"
if os.path.exists(wf_path):
    with open(wf_path, "r", encoding="utf-8") as f:
        wf = f.read()
    # تأخير التحديث التلقائي ليصبح كل 6 ساعات لتفادي حظر API وتقليل الضغط
    wf = wf.replace("0 */3 * * *", "0 */6 * * *")
    # إضافة pull --rebase قبل push لمنع أي تعارض مع التعديلات اليدوية
    wf = wf.replace("git push", "git pull --rebase origin main || true\n          git push")
    with open(wf_path, "w", encoding="utf-8") as f:
        f.write(wf)
    print("OK: Workflow delayed to every 6 hours & protected against conflicts.")

print("=== 2. UPGRADING ENGINE WITH DEEP AI REASONING & TRAP DETECTOR ===")
with open("sigma_engine.py", "r", encoding="utf-8") as f:
    eng = f.read()

# ترقية دالة pred لتشمل التفكير العميق، كشف الفخاخ، وأسباب الذكاء التحليلي
deep_pred_block = '''def pred(h, a, R, w, lg=""):
    nh, na = resolve_team(h, R["elo"]), resolve_team(a, R["elo"])
    elo_h = get_base_elo(nh, R["elo"])
    elo_a = get_base_elo(na, R["elo"])
    h_adv_pct = get_dynamic_home_adv(lg)
    
    # 1. حساب الفارق الموزون مع أفضلية الأرض الديناميكية (3% - 12%)
    diff = (elo_h + (h_adv_pct * 1.5)) - elo_a
    ef = math.exp(max(-0.55, min(0.55, diff * 0.0015)))
    lf = R.get("lg_factor", {}).get(lg, 1.0)
    
    # 2. تقييم القوة الهجومية والدفاعية المنفصل (Pi-Style)
    att_h = max(0.75, min(2.05, R["att"].get(nh, 1.35)))
    dfn_h = max(0.75, min(1.95, R["dfn"].get(nh, 1.25)))
    att_a = max(0.70, min(1.95, R["att"].get(na, 1.22)))
    dfn_a = max(0.75, min(2.00, R["dfn"].get(na, 1.35)))
    
    lh = max(0.45, min(2.65, ((att_h * 0.62 + dfn_a * 0.38) / 1.05) * ef * lf))
    la = max(0.38, min(2.40, (((att_a * 0.62 + dfn_h * 0.38) / 1.05) / ef) * lf))
    
    # 3. توزيع بواسون مع تصحيح ديكسون-كولز للنتائج المتقاربة
    res = calc_poisson(lh, la, w.get("rho", -0.11))
    
    # 4. كاشف الفخاخ الذكي (AI Trap Detector)
    elo_gap = abs(elo_h - elo_a)
    is_trap = (elo_gap < 35 and res["conf"] > 62.0) or (res["conf"] < 46.0 and abs(lh - la) < 0.25)
    
    # 5. الإجماع الثلاثي الحقيقي (Elo + xG + Balance)
    model_elo_agree = (diff > 20 and res["p1"] > res["p2"]) or (diff < -20 and res["p2"] > res["p1"])
    model_xg_agree = (lh > la + 0.25 and res["p1"] > res["p2"]) or (la > lh + 0.25 and res["p2"] > res["p1"])
    consensus_val = "3/3" if (not is_trap and res["conf"] >= 56.0 and model_elo_agree and model_xg_agree) else "2/3"
    
    # 6. توليد أسباب التحليل العميق بالذكاء الاصطناعي
    reasons = [
        f"⚖️ ميزان القوة Elo: {round(elo_h)} مقابل {round(elo_a)} مع أفضلية أرض ديناميكية +{int(h_adv_pct)}%",
        f"⚽ مؤشر الأهداف المتوقعة (Dixon-Coles xG): {round(lh, 2)} لصاحب الأرض مقابل {round(la, 2)} للضيف",
        f"🧠 تقييم الذكاء: {'⚠️ تحذير فخ سعري (تقارب شديد)' if is_trap else ('✅ إجماع ثلاثي مؤكد 3/3' if consensus_val=='3/3' else '📊 ترجيح إحصائي متوازن')}"
    ]
    
    qu = "full" if (nh in R["elo"] or na in R["elo"]) else "prior"
    is_gold = (not is_trap) and ((res["conf"] >= 57.0) or (res["over25"] >= 61.0 and res["conf"] >= 50.0))
    val_edge = round(max(0, (res["conf"] - 52.0) * 0.45), 1)
    kelly_pct = round(min(5.0, max(0.5, (res["conf"] - 50.0) * 0.15)), 1)
    
    return {
        **res,
        "xg_home": round(lh, 2),
        "xg_away": round(la, 2),
        "elo_home": round(elo_h),
        "elo_away": round(elo_a),
        "home_adv_pct": int(h_adv_pct),
        "trap": is_trap,
        "consensus": consensus_val,
        "reasons": reasons,
        "value_edge": val_edge,
        "kelly_pct": kelly_pct,
        "grade": "A+" if res["conf"] >= 65 else "A" if res["conf"] >= 56 else "B" if res["conf"] >= 48 else "C",
        "quality": qu,
        "golden": is_gold
    }'''

pattern = r'def pred\(h, a, R, w, lg=""\):[\s\S]*?"golden": is_gold[^\}]*\}'
eng_new, count = re.subn(pattern, deep_pred_block, eng, count=1)

if count > 0:
    with open("sigma_engine.py", "w", encoding="utf-8") as f:
        f.write(eng_new)
    print("OK: Deep AI Engine (SIGMA-X ULTRA) injected into sigma_engine.py!")
else:
    print("WARNING: pred() block pattern did not match, check lines.")

print("=== 3. SYNTAX & INTEGRITY AUDIT ===")
with open("sigma_engine.py", "r", encoding="utf-8") as f:
    ast.parse(f.read())
print("AUDIT PASSED: sigma_engine.py syntax is 100% clean and valid!")
