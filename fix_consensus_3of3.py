with open("sigma_engine.py", "r", encoding="utf-8") as f:
    eng = f.read()

old_str = '"golden": is_gold,'
new_str = '"golden": is_gold, "consensus": "3/3" if (res["conf"] >= 58.0 and ((elo_h > elo_a and lh > la) or (elo_a > elo_h and la > lh))) else "2/3",'

if old_str in eng and '"consensus":' not in eng:
    eng = eng.replace(old_str, new_str)
    with open("sigma_engine.py", "w", encoding="utf-8") as f:
        f.write(eng)
    print("SUCCESS: 3/3 Consensus logic added to sigma_engine.py!")
else:
    print("INFO: Consensus logic already present or pattern shifted.")
