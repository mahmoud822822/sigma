import csv, json
rows=list(csv.DictReader(open("data/sigma_mega_golden.csv", encoding="utf-8")))
rows=[r for r in rows if r.get("date","")>="2026-11-20"]
gold=[r for r in rows if float(r.get("GoldenOdds",9))<=1.25]
gold=sorted(gold, key=lambda r: float(r.get("GoldenOdds",9)))[:10]
top=sorted(rows, key=lambda r: float(r.get("conf", r.get("1",0)) or 0), reverse=True)[:5]
print(f"Golden {len(gold)} / All {len(rows)}")
js=json.dumps(rows)
head="""<!doctype html><html lang='ar' dir='rtl'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Sigma AI V6</title><style>body{background:#0a0e14;color:#fff;font-family:system-ui;padding:12px}h1{font-size:28px}.gold{background:linear-gradient(135deg,#f5c518,#ff8c00);color:#000;padding:12px;border-radius:14px;margin:8px 0}.card{background:#161d27;padding:12px;border-radius:14px;margin:8px 0}table{width:100%;border-collapse:collapse;font-size:13px}td,th{border:1px solid #2a3442;padding:7px;text-align:center}input{width:70%;padding:10px;border-radius:10px}.badge{background:#f5c518;color:#000;padding:2px 8px;border-radius:20px;font-weight:bold}</style></head><body><h1>⭐ Sigma AI V6</h1><p>Signature Prediction and Forecast: Sigma - Mahmoud Emad</p><p><b>Verified: 11/14 = 78.6% | MEGA 51.7% | History 31306 | Golden = Fair Odds ≤ 1.25</b></p><h2>🏆 Golden Bet - Odds ≤ 1.25 - Real MEGA Prob</h2>"""
gold_html="".join([f"<div class='gold'><b>{r['match']}</b> - {r.get('Golden','')} - Fair {r.get('GoldenOdds','')} - {r.get('date','')}</div>" for r in gold])
top_html="".join([f"<div class='card'><b>{r['match']}</b> - {r.get('xG','')} - 1:{r.get('1','')}% X:{r.get('X','')}% 2:{r.get('2','')}% - {r.get('Golden','')}</div>" for r in top])
mid="""<h2>Top MEGA</h2>"""+top_html+"""<h2>All Matches - Old + New Real Data</h2><input id='q' placeholder='Search team' oninput='filt()'><p id='cnt'></p><table><tr><th>Date</th><th>Match</th><th>xG</th><th>1</th><th>X</th><th>2</th><th>BTTS</th><th>Corners</th><th>Throw</th><th>Golden</th></tr><tbody id='tb'></tbody></table><script>const R="""+js+""";function filt(){let q=document.getElementById('q').value.toLowerCase();let f=R.filter(r=>r.match.toLowerCase().includes(q));document.getElementById('cnt').innerText=f.length+' matches';document.getElementById('tb').innerHTML=f.map(r=>`<tr><td>${r.date||''}</td><td>${r.match}</td><td>${r.xG||''}</td><td>${r['1']||''}%</td><td>${r['X']||''}%</td><td>${r['2']||''}%</td><td>${r.BTTS||''}%</td><td>${r.Corners||''}</td><td>${r.Throw||''}</td><td><span class='badge'>${r.Golden||''}</span></td></tr>`).join('')}filt()</script></body></html>"""
open("index.html","w",encoding="utf-8").write(head+gold_html+mid)
print("V6 written")
