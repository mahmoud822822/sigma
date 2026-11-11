import pathlib
p=pathlib.Path("sigma_super_update.py")
t=p.read_text()
# شيل القديم وحط الجديد
for old in ["sigma_make_index_v7.py","sigma_make_index_v6.py","sigma_make_index_full.py","sigma_make_index.py"]:
    t=t.replace(old,"sigma_insight.py\",\"sigma_acca.py\",\"sigma_track_golden.py\",\"sigma_make_index_v8.py")
    # لو اتكرر نظف
    t=t.replace("sigma_insight.py\",\"sigma_insight.py","sigma_insight.py")
p.write_text(t)
print("v8 auto patched")
print([l for l in t.splitlines() if "sigma_" in l][:6])
