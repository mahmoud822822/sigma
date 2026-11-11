import csv, pathlib, re
rows=list(csv.DictReader(open('data/sigma_mega_predictions.csv')))
gold=[r for r in rows if float(r['conf'])>=68][:10]
html='<div id="golden"></div><div class="card" style="border:2px solid #FFC107"><h3 style="color:#FFC107">Golden Bets - Real - Conf 68%+</h3>'
for r in gold:
  html+=f"<p><b>{r['match']}</b> - {r['date']} - Conf {r['conf']}% - Top {r['top']}</p>"
html+='</div>'
p=pathlib.Path('index.html'); h=p.read_text()
h=re.sub(r'No Real Golden Bets Loaded Yet.*?</p>', '', h, flags=re.DOTALL)
h=h.replace('</div><div style="height:60px">', html+'</div><div style="height:60px">', 1)
# mark DEFAULT duplicates
h=h.replace('xG 2.52-0.95','xG 2.52-0.95 [DEFAULT]')
p.write_text(h); print('Golden real', len(gold))
