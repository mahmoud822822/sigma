for fname in ["sigma_engine.py", "index.html"]:
    try:
        with open(fname, "r", encoding="utf-8") as f:
            txt = f.read()
        
        # تثبيت Elo 65+ في القالب الداخلي والواجهة
        txt_new = txt.replace("Elo 12+", "Elo 65+").replace("+12", "+65")
        
        if txt_new != txt:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(txt_new)
            print(f"FIXED permanently in {fname}!")
    except FileNotFoundError:
        pass
