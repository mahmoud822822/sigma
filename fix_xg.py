import pathlib
p=pathlib.Path("sigma_predict_next.py")
t=p.read_text(encoding="utf-8")
old="    xh=max(0.15, ah/base*da/base*base+HA); xa=max(0.10, aa/base*dh/base*base-HA*0.3)"
new="    raw_h=ah/base*da/base*base+HA; raw_a=aa/base*dh/base*base-HA*0.3\n    xh=max(0.15, min(3.5, base+(raw_h-base)*0.6)); xa=max(0.10, min(3.5, base+(raw_a-base)*0.6))"
if old in t:
    t=t.replace(old,new); print("Fixed xG cap 3.5 + damp 0.6")
else:
    print("Not found - check file")
p.write_text(t,encoding="utf-8")
