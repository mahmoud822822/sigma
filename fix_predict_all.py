import pathlib
p = pathlib.Path("sigma_main.py")
t = p.read_text(encoding="utf-8")
old_h = '        h=round(bh*1.08,2); a=round(ba,2)'
new_h = """
        # History 50 اولا - لو الفريقين موجودين، xG منهم مش من الدوري
        try:
            _home, _away = mm.get("match","").split(" vs ")
        except:
            _home, _away = "", ""
        _hs=stats.get(_home); _aws=stats.get(_away)
        if _hs and _aws and _hs.get("source")=="history50" and _aws.get("source")=="history50":
            h=round(max(0.2,min(3.8, _hs["home_scored"] * (_aws["away_conceded"]/1.35))),2)
            a=round(max(0.2,min(3.8, _aws["away_scored"] * (_hs["home_conceded"]/1.35))),2)
            src="history50"
        else:
            h=round(bh*1.08,2); a=round(ba,2); src="league"
"""
if old_h in t and "stats=team_stats()" not in t.split("def predict_all")[1].split("def do_history")[0]:
    t = t.replace(old_h, new_h)
    t = t.replace('    out=[]\n    for mm in items:', '    stats=team_stats()\n    out=[]\n    for mm in items:')
    t = t.replace('"conf":round(conf*100,1)})', '"conf":round(conf*100,1),"src":src})')
    t = t.replace('print(f"{o[\'date\']} {o[\'match\']}  1:{o[\'1\']}% X:{o[\'X\']}% 2:{o[\'2\']}%  BTTS:{o[\'BTTS\']}%")',
                  'print(f"{o[\'date\']} {o[\'match\']}  xG:{o[\'xG\']} 1:{o[\'1\']}% X:{o[\'X\']}% 2:{o[\'2\']}%  BTTS:{o[\'BTTS\']}% [{o.get(\'src\',\'\')}]")')
    p.write_text(t, encoding="utf-8")
    print("Predict All patched to history50")
else:
    print("Already patched or not found")
hp = pathlib.Path("sigma_history_fetch.py")
if hp.exists():
    ht = hp.read_text(encoding="utf-8")
    if "Belgian Pro League" not in ht:
        ht = ht.replace('"Jupiler Pro League":"Belgium"', '"Jupiler Pro League":"Belgium","Belgian Pro League":"Belgium","First Division A":"Belgium","Pro League":"Belgium"')
        hp.write_text(ht, encoding="utf-8")
        print("MAP patched - Belgium")
    else:
        print("MAP already patched")
print("Done")
