import pathlib
p=pathlib.Path("sigma_mega_31k.py")
t=p.read_text(encoding="utf-8")
old="        xh=max(0.15, ah/base*da/base*base+ha+ew*(eh-ea)/100+0.05*fh)\n        xa=max(0.10, aa/base*dh/base*base-ha*0.3+ew*(ea-eh)/100+0.05*fa)"
new="        rh=ah/base*da/base*base+ha+ew*(eh-ea)/100+0.05*fh; ra=aa/base*dh/base*base-ha*0.3+ew*(ea-eh)/100+0.05*fa\n        xh=max(0.15, min(3.5, base+(rh-base)*0.6)); xa=max(0.10, min(3.5, base+(ra-base)*0.6))"
if old in t:
    t=t.replace(old,new); print("Fixed mega cap")
else:
    print("Not found - check mega file")
    print(t[2000:3000])
p.write_text(t,encoding="utf-8")
