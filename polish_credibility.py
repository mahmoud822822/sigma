with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace("أفضلية الأرض +32 | معامل التعادل -0.06", "أفضلية الأرض الديناميكية 3%–12% | تصحيح ديكسون-كولز -0.11")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("POLISHED: Credibility tab text synced with SIGMA-X OMNI engine!")
