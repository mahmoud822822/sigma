import csv, pathlib
rows=list(csv.DictReader(open('data/sigma_mega_predictions.csv')))
rows=rows
html=""
for r in rows:
 html+=f"<div class='card'><b>{r['match']}</b><br>{r['date']} - {r['league']}<br>xG {r['xG']} | 1 {r['1']}% X {r['X']}% 2 {r['2']}%<br>BTTS {r['BTTS']}% Over25 {r['Over25']}% Conf {r['conf']}%<br>Top: {r['top']}</div>"
p=pathlib.Path('index.html')
h=p.read_text()
h=h.replace('</div><div style="height:60px">', html+'</div><div style="height:60px">')
p.write_text(h)
print('embedded',len(rows))
