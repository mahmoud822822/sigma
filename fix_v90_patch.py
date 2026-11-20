with open("build_v90.py", "r", encoding="utf-8") as f:
    code = f.read()

old_block = '''def pred(h, a, R, w, lg=""):
    nh, na = norm(h), norm(a)
    diff = (R["elo"].get(nh, 1500.0) + 32.0) - R["elo"].get(na, 1500.0)
    ef = math.exp(max(-0.75, min(0.75, diff * 0.00125)))
    lf = R.get("lg_factor", {}).get(lg, 1.0)
    att_h, dfn_h = R["att"].get(nh, 1.32), R["dfn"].get(nh, 1.32)
    att_a, dfn_a = R["att"].get(na, 1.24), R["dfn"].get(na, 1.32)
    lh = max(0.42, min(2.9, ((att_h + dfn_a) / 2.10) * ef * lf))
    la = max(0.38, min(2.6, (((att_a + dfn_h) / 2.10) / ef) * lf))'''

new_block = '''def pred(h, a, R, w, lg=""):
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
    la = max(0.38, min(2.45, raw_la))'''

if old_block in code:
    code = code.replace(old_block, new_block)
    with open("build_v90.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("SUCCESS: build_v90.py patched successfully!")
else:
    print("WARNING: Exact block not found, checking line indentation...")
