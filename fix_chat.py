import pathlib
p=pathlib.Path("sigma_super_update.py")
t=p.read_text()
if "sigma_make_chat_v6" not in t:
    t=t.replace("sigma_make_index_v6.py","sigma_make_index_v6.py\",\"sigma_make_chat_v6.py")
    p.write_text(t)
print("chat patched")
