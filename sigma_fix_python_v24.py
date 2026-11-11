import pathlib
p = pathlib.Path("sigma_main.py")
t = p.read_text(encoding="utf-8")
t = t.replace('rows=[r for r in rows if r["status"]=="FINISHED"]', 'rows=[r for r in rows if r.get("status","FINISHED")=="FINISHED" or "status" not in r]')
p.write_text(t, encoding="utf-8")
print("Fixed sigma_main.py - status column")
p2 = pathlib.Path("sigma_auto_fetch.py")
t2 = p2.read_text(encoding="utf-8")
old = 'mk=[("Over 1",f"Over 1 ({ph+pa:.1f} exp)",9.0,82,"Gold"),("2H Over 0.5","2H Over 0.5 - Late 76-90 30%",9.5,85,"Gold"),("BTTS","BTTS - weight 70",7.0,67,"Value"),("X2",f"{away} X2",8.0,76,"Balanced"),("Home X2",f"{home} X2",8.0,76,"Balanced")]'
new = 'mk=[("Over 1",f"Over 1 ({ph+pa:.1f} exp)",9.0,82,"Gold"),("2H Over 0.5","2H Over 0.5 - Late 76-90 30%",9.5,85,"Gold"),("BTTS","BTTS - weight 70",7.0,67,"Value"),("X2",f"{away} X2",8.0,76,"Balanced"),("Home X2",f"{home} X2",8.0,76,"Balanced"),("Over 2.5",f"Over 2.5 - exp {ph+pa:.1f}",7.5,72,"Value"),("1X",f"{home} 1X",8.5,78,"Balanced"),("BTTS + Over 1.5","BTTS + Over 1.5 Combo",6.5,64,"Value")]'
if old in t2:
    t2 = t2.replace(old, new)
    p2.write_text(t2, encoding="utf-8")
    print("Fixed sigma_auto_fetch.py - 8 markets")
else:
    print("auto_fetch already 8 or pattern different")
