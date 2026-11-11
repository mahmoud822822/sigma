import pathlib
p = pathlib.Path("sigma_main.py")
t = p.read_text(encoding="utf-8")
helper = '''
def find_team(stats, inp):
    if not inp: return None
    if inp in stats: return inp
    low = inp.lower().strip()
    for k in stats:
        if k.lower()==low: return k
    aliases = {"man city":"manchester city","man utd":"manchester united","man united":"manchester united","barca":"barcelona","real":"real madrid","spurs":"tottenham","psg":"paris saint","milan":"ac milan","inter":"inter","juve":"juventus","porto":"porto","benfica":"benfica","ajax":"ajax","psv":"psv","feyenoord":"feyenoord","atletico":"atletico","sevilla":"sevilla","valencia":"valencia","chelsea":"chelsea","arsenal":"arsenal","liverpool":"liverpool","city":"manchester city","united":"manchester united"}
    if low in aliases:
        want = aliases[low]
        for k in stats:
            if want in k.lower(): return k
    for k in stats:
        kl = k.lower()
        if low in kl or kl in low: return k
    parts = low.split()
    if parts:
        for k in stats:
            if parts[0] in k.lower(): return k
    return None

'''
if "def find_team" not in t:
    t = t.replace("def predict_by_team():", helper + "def predict_by_team():")
old = "    base_h, base_a = 1.55, 1.25\n    hs=stats.get(home); aws=stats.get(away)"
new = """    base_h, base_a = 1.55, 1.25
    _rh = find_team(stats, home); _ra = find_team(stats, away)
    if _rh: print(f"Found: {home} -> {_rh}")
    if _ra: print(f"Found: {away} -> {_ra}")
    home = _rh or home; away = _ra or away
    hs=stats.get(home); aws=stats.get(away)"""
if old in t:
    t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print("Fuzzy patched")
else:
    print("Already patched")
