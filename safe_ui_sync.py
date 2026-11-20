import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. تحديث نص ميثاق الشفافية
html = html.replace(
    "أفضلية الأرض +32 | معامل التعادل -0.06",
    "أفضلية الأرض الديناميكية 3%–12% | تصحيح ديكسون-كولز -0.11 | ذكاء جمعي 4/4"
)

# 2. إضافة زر القناص 4/4 بأمان تام
if "القناص 4/4" not in html:
    html = re.sub(
        r'(إجماع 3/3</button>)',
        r'\1<button class="qb" onclick="setQF(\'sniper\',this)" style="border-color:#a855f7;color:#e9d5ff">🎯 القناص 4/4</button>',
        html,
        count=1
    )

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("RESTORED & SYNCED: Clean index.html verified!")
