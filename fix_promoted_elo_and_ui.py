import ast

print("=== 1. APPLYING REALISTIC ELO FLOOR (1380) IN SIGMA_ENGINE.PY ===")
with open("sigma_engine.py", "r", encoding="utf-8") as f:
    eng = f.read()

target_lines = '''    elo_h = get_base_elo(nh, R["elo"])
    elo_a = get_base_elo(na, R["elo"])'''

replacement_lines = '''    elo_h = max(1380.0, get_base_elo(nh, R["elo"]))
    elo_a = max(1380.0, get_base_elo(na, R["elo"]))'''

if target_lines in eng:
    eng = eng.replace(target_lines, replacement_lines)
    ast.parse(eng)
    with open("sigma_engine.py", "w", encoding="utf-8") as f:
        f.write(eng)
    print("AUDIT PASSED: Realistic Elo floor (1380) applied cleanly to sigma_engine.py!")
else:
    print("INFO: Elo floor already applied or pattern adjusted.")

print("=== 2. SYNCING DYNAMIC HOME ADVANTAGE LABEL IN INDEX.HTML ===")
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

if "Elo 12+" in html:
    html = html.replace("Elo 12+", "أرض +${m.home_adv_pct||8}%")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("OK: UI home advantage label synced with dynamic engine values!")
