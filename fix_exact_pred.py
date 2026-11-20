with open("sigma_engine.py", "r", encoding="utf-8") as f:
    code = f.read()

old_pred = '''def pred(h, a, R, w, lg=""):
    nh, na = resolve_team(h, R["elo"]), resolve_team(a, R["elo"])
    diff = (get_base_elo(nh, R["elo"]) + 12.0) - get_base_elo(na, R["elo"])
    ef = math.exp(max(-0.75, min(0.75, diff * 0.0022)))
    lf = R.get("lg_factor", {}).get(lg, 1.0)
    att_h, dfn_h = R["att"].get(nh, 1.32), R["dfn"].get(nh, 1.32)
    att_a, dfn_a = R["att"].get(na, 1.24), R["dfn"].get(na, 1.32)
    lh = max(0.42, min(2.9, ((att_h + dfn_a) / 2.10) * ef * lf))
    la = max(0.38, min(2.6, (((att_a + dfn_h) / 2.10) / ef) * lf))
    res = calc_poisson(lh, la, w.get("rho", -0.06))
    qu = "full" if (nh in R["elo"] or na in R["elo"]) else "prior"
    is_gold = (res["conf"] >= 56.0) or (res["over25"] >= 61.0 and res["conf"] >= 48.0)
    return {**res, "xg_home": round(lh, 2), "xg_away": round(la, 2), "elo_home": round(get_base_elo(nh, R["elo"])), "elo_away": round(get_base_elo(nh, R["elo"])), "grade": "A+" if res["conf"] >= 65 else "A" if res["conf"] >= 56 else "B" if res["conf"] >= 48 else "C", "quality": qu, "golden": is_gold}'''

new_pred = '''def pred(h, a, R, w, lg=""):
    nh, na = resolve_team(h, R["elo"]), resolve_team(a, R["elo"])
    elo_h = get_base_elo(nh, R["elo"])
    elo_a = get_base_elo(na, R["elo"])
    diff = (elo_h + 65.0) - elo_a
    ef = math.exp(max(-0.85, min(0.85, diff * 0.0028)))
    lf = R.get("lg_factor", {}).get(lg, 1.0)
    att_h = max(0.75, min(2.05, R["att"].get(nh, 1.35)))
    dfn_h = max(0.75, min(1.95, R["dfn"].get(nh, 1.25)))
    att_a = max(0.70, min(1.95, R["att"].get(na, 1.22)))
    dfn_a = max(0.75, min(2.00, R["dfn"].get(na, 1.35)))
    lh = max(0.45, min(2.75, ((att_h * 0.6 + dfn_a * 0.4) / 1.05) * ef * lf))
    la = max(0.38, min(2.45, (((att_a * 0.6 + dfn_h * 0.4) / 1.05) / ef) * lf))
    res = calc_poisson(lh, la, w.get("rho", -0.06))
    qu = "full" if (nh in R["elo"] or na in R["elo"]) else "prior"
    is_gold = (res["conf"] >= 56.0) or (res["over25"] >= 61.0 and res["conf"] >= 48.0)
    return {**res, "xg_home": round(lh, 2), "xg_away": round(la, 2), "elo_home": round(elo_h), "elo_away": round(elo_a), "grade": "A+" if res["conf"] >= 65 else "A" if res["conf"] >= 56 else "B" if res["conf"] >= 48 else "C", "quality": qu, "golden": is_gold}'''

if old_pred in code:
    code = code.replace(old_pred, new_pred)
    with open("sigma_engine.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("SUCCESS: All 4 bugs in pred() fixed!")
else:
    print("ERROR: Could not match old_pred block exactly.")
