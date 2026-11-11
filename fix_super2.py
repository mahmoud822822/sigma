import pathlib
p=pathlib.Path("sigma_super_update.py")
t=p.read_text()
if "sigma_conditions_bulk" not in t:
    t=t.replace("sigma_make_index_full.py","sigma_conditions_bulk.py\",\"sigma_make_index_full.py")
    p.write_text(t)
print("super patched")
