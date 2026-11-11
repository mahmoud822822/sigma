import pathlib
p = pathlib.Path("sigma_main.py")
t = p.read_text(encoding="utf-8")
print("6 موجود؟", 'elif c=="6"' in t)
if 'elif c=="6"' not in t:
    t = t.replace('    elif c=="5": do_fetch()', '    elif c=="5": do_fetch()\n    elif c=="6": predict_all()')
    p.write_text(t, encoding="utf-8")
    print("اتصلح - 6 رجع")
else:
    print("6 موجود أصلاً - المشكلة في حاجة تانية")
