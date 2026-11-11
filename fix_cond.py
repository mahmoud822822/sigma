import pathlib
p=pathlib.Path("sigma_conditions.py")
t=p.read_text()
t=t.replace("def team_attack(team, is_home):\n    s=STATS.get(team, {})","def find_team(name):\n    low=name.lower().strip()\n    for k in STATS:\n        if k.lower()==low: return k\n    for k in STATS:\n        if low in k.lower() or k.lower() in low: return k\n    return None\ndef team_attack(team, is_home):\n    k=find_team(team)\n    s=STATS.get(k, {}) if k else {}")
# لو __main__ متكرر شيل التاني
parts=t.split('if __name__=="__main__":')
if len(parts)>2:
    t=parts[0]+'if __name__=="__main__":'+parts[1]
p.write_text(t)
print("fixed")
