import re

with open("sigma_engine.py", "r", encoding="utf-8") as f:
    eng = f.read()

# ترقية منطق التوقع ليجمع 4 عقول إحصائية مستقلة + مؤشر القناص الخارق (Sniper 90%+)
sniper_block = '''    # 5. الذكاء الجمعي الرباعي (4-Brain Ensemble Consensus)
    brain_elo = (diff > 22 and res["p1"] > res["p2"]) or (diff < -22 and res["p2"] > res["p1"])
    brain_xg = (lh > la + 0.28 and res["p1"] > res["p2"]) or (la > lh + 0.28 and res["p2"] > res["p1"])
    brain_form = (att_h > att_a * 1.12 and dfn_h <= dfn_a * 1.05 and res["p1"] > res["p2"]) or (att_a > att_h * 1.12 and dfn_a <= dfn_h * 1.05 and res["p2"] > res["p1"])
    brain_safety = (res["dc_prob"] >= 84.0)
    
    brains_agreed = sum([brain_elo, brain_xg, brain_form, brain_safety])
    consensus_val = "3/3" if (not is_trap and brains_agreed >= 3 and res["conf"] >= 57.0) else "2/3"
    
    # 6. وضع القناص الخارق (Sniper 90%+): تطابق كل العقول الأربعة بدون أي فخ
    is_sniper = (not is_trap) and (brains_agreed == 4) and (res["conf"] >= 63.0) and (elo_gap >= 95)
    
    # 7. توليد تقرير التفكير العميق للذكاء الجمعي
    reasons = [
        f"🧠 تصويت العقول الذكية: اتفاق {brains_agreed}/4 نماذج مستقلة ({'🎯 وضع القناص 90%+' if is_sniper else 'تحليل متوازن'})",
        f"⚖️ ميزان القوة Elo: {round(elo_h)} مقابل {round(elo_a)} مع أفضلية أرض ديناميكية +{int(h_adv_pct)}%",
        f"⚽ محاكاة الأهداف (Dixon-Coles xG): {round(lh, 2)} مقابل {round(la, 2)} | أمان مزدوج: {res['dc_prob']}%"
    ]'''

old_section = r'    # 5\. الإجماع الثلاثي الحقيقي[\s\S]*?    \]'
eng_new, count = re.subn(old_section, sniper_block, eng, count=1)

if count > 0:
    eng_new = eng_new.replace('"golden": is_gold', '"golden": is_gold, "sniper": is_sniper, "brains": brains_agreed')
    with open("sigma_engine.py", "w", encoding="utf-8") as f:
        f.write(eng_new)
    print("SUCCESS: 4-Brain Ensemble & Sniper 90%+ Mode activated in sigma_engine.py!")
else:
    print("WARNING: Section pattern not matched.")
