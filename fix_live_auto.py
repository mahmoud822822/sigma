import pathlib
p=pathlib.Path("sigma_super_update.py")
t=p.read_text()
if "sigma_live.py" not in t:
    t=t.replace("sigma_make_index_v10.py","sigma_live.py\",\"sigma_add_live.py\",\"sigma_make_index_v10.py")
    p.write_text(t)
print("live auto patched")
