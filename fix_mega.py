import pathlib
p=pathlib.Path("sigma_mega.py")
t=p.read_text(encoding="utf-8")
old="        if lg_goals[lg]: base=sum(lg_goals[lg])/len(lg_goals[lg])/2"
new="        if lg_goals[lg]:\n            base=sum(lg_goals[lg])/len(lg_goals[lg])/2\n            base=max(base,0.8)"
if old in t:
    t=t.replace(old,new)
    print("Fixed base calc")
old2="        eh=elo.get(ht,1500); ea=elo.get(at,1500)"
new2="        base=max(base,0.8)\n        eh=elo.get(ht,1500); ea=elo.get(at,1500)"
if old2 in t:
    t=t.replace(old2,new2)
    print("Fixed guard")
p.write_text(t,encoding="utf-8")
print("Done")
