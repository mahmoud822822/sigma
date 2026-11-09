import csv, json, pathlib
rows=[]
p=pathlib.Path("data/sigma_mega_predictions.csv")
if p.exists():
    rows=list(csv.DictReader(open(p, encoding="utf-8")))
    rows=[r for r in rows if r.get("date","")>="2026-11-20"]
    rows=sorted(rows, key=lambda r: (r.get("date",""), -float(r.get("1",0) or 0)))
print(f"MEGA after break: {len(rows)}")
js=json.dumps(rows)
head="""<!doctype html><html lang='ar' dir='rtl'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Sigma AI - All Matches</title><style>body{background:#0b0f14;color:#fff;font-family:system-ui;padding:12px}#box{max-width:800px;margin:auto}input{width:70%;padding:10px}table{width:100%;border-collapse:collapse;font-size:13px}td,th{border:1px solid #333;padding:6px;text-align:center}</style></head><body><div id='box'><h1>Sigma AI - All Matches After Break</h1><p>Verified: 11/14 = 78.6% | MEGA 51.7% | History 31306 | Break 10-19 Nov skipped</p><input id='q' placeholder='Search team' oninput='filt()'><p id='cnt'></p><table><thead><tr><th>Date</th><th>Match</th><th>xG</th><th>1</th><th>X</th><th>2</th><th>BTTS</th></tr></thead><tbody id='tb'>"""
tail="""</tbody></table></div><script>const R="""+js+""";function filt(){let q=document.getElementById('q').value.toLowerCase();let f=R.filter(r=>r.match.toLowerCase().includes(q));document.getElementById('cnt').innerText=f.length+' matches';document.getElementById('tb').innerHTML=f.map(r=>`<tr><td>${r.date||''}</td><td>${r.match}</td><td>${r.xG||''}</td><td>${r['1']||''}%</td><td>${r['X']||''}%</td><td>${r['2']||''}%</td><td>${r.BTTS||''}%</td></tr>`).join('')}filt()</script></body></html>"""
open("index.html","w",encoding="utf-8").write(head+tail)
print("NEW full index written")
