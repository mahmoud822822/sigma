with open("sigma_engine.py", "r", encoding="utf-8") as f:
    eng = f.read()

# التأكد من أن دالة get_dynamic_home_adv سليمة وتُمرر النسبة لكل مباراة
if "home_adv_pct" not in eng:
    eng = eng.replace('"elo_away": round(elo_a),', '"elo_away": round(elo_a), "home_adv_pct": int(get_dynamic_home_adv(lg)),')
    with open("sigma_engine.py", "w", encoding="utf-8") as f:
        f.write(eng)

print("READY: Code verified and pushed for GitHub Actions execution!")
