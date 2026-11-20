with open("sigma_engine.py", "r", encoding="utf-8") as f:
    code = f.read()

# تعديل أفضلية الأرض ومعامل Elo في الدالة الأصلية النظيفة
code = code.replace("+ 32.0)", "+ 65.0)")
code = code.replace("* 0.00125", "* 0.0022")

with open("sigma_engine.py", "w", encoding="utf-8") as f:
    f.write(code)
print("CLEAN PATCH APPLIED!")
