import csv, pathlib
p=pathlib.Path("data/sigma_live.csv")
live=list(csv.DictReader(open(p, encoding="utf-8"))) if p.exists() else []
if not live:
  html="<div class='card' style='border:1px solid #f5c518'><b>🔴 LIVE - لا يوجد مباريات حية الآن - استراحة دولية حتى 2026-11-20 | No Live Now</b><br>التوقعات داخل المباراة هتشتغل أوتوماتيك كل 5 دقائق أول ما الماتشات تبدأ - Live predictions every 5 min</div>"
else:
  html="<div class='card' style='border:1px solid #ef4444'><h3>🔴 LIVE - توقعات داخل المباراة - Live Predictions</h3>"+"".join([f"<div>{r['minute']}' {r['match']} - {r['score']} - 1:{r['Live1']}% X:{r['LiveX']}% 2:{r['Live2']}% - Next Goal Home {r['NextGoal_H']}%</div>" for r in live])+"</div>"
h=open("index.html", encoding="utf-8").read()
h=h.replace("<div class='hero'>", html+"<div class='hero'>")
open("index.html","w", encoding="utf-8").write(h)
print(f"Live injected: {len(live)}")
