import pathlib
p=pathlib.Path("sigma_main.py")
t=p.read_text(encoding="utf-8")
old="            return round(max(0.2,min(3.8, base)),2)"
new="            base2=1.35+(base-1.35)*0.6+(0.22 if is_home else -0.066)\n            return round(max(0.15,min(3.5, base2)),2)"
if old in t:
    t=t.replace(old,new); print("Patched xG")
else: print("xG not found")
old2="    btts=sum(p for (x,y),p in m.items() if x>0 and y>0); over25=sum(p for (x,y),p in m.items() if x+y>=3)"
new2="    btts=sum(p for (x,y),p in m.items() if x>0 and y>0); over25=sum(p for (x,y),p in m.items() if x+y>=3)\n    try:\n        import json as _j; _sh=_j.load(open('data/sigma_super_model.json', encoding='utf-8')).get('best_shrink',0.1)\n        hw=0.333+(1-_sh)*(hw-0.333); d=0.333+(1-_sh)*(d-0.333); aw=0.333+(1-_sh)*(aw-0.333); _s=hw+d+aw; hw,d,aw=hw/_s,d/_s,aw/_s\n    except: pass"
if old2 in t:
    t=t.replace(old2,new2); print("Patched shrink")
else: print("pred not found")
p.write_text(t,encoding="utf-8")
print("Done")
