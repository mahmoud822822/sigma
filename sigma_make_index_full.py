import csv, json, pathlib
rows=[]; top=[]; alls=[]
p=pathlib.Path("data/sigma_mega_predictions.csv")
if p.exists():
    rows=list(csv.DictReader(open(p, encoding="utf-8")))
    rows=[r for r in rows if r.get("date","")>="2026-11-20"]
    top=sorted(rows, key=lambda r: float(r.get("conf", r.get("1",0)) or 0), reverse=True)[:5]
    alls=sorted(rows, key=lambda r: r.get("date",""))
print(f"Top {len(top)} / All {len(alls)}")
def tr(r):
    return f"<tr><td>{r.get('2','')}%</td><td>{r.get('X','')}%</td><td>{r.get('1','')}%</td><td>{r.get('xG','')}</td><td>{r.get('match','')}</td></tr>"
top_html="".join([tr(r) for r in top])
js=json.dumps(alls)
head="""<!doctype html><html lang='ar' dir='rtl'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Sigma AI - Mahmoud Emad</title><style>body{background:#111;color:#fff;font-family:system-ui;padding:12px;text-align:center}table{width:100%;border-collapse:collapse;font-size:14px}td,th{border:1px solid #333;padding:8px}input{width:70%;padding:10px}</style></head><body><h1>Sigma AI</h1><p>Signature Prediction and Forecast: Sigma - Mahmoud Emad</p><p><b>Verified: 11/14 = 78.6% | MEGA Hit 51.7% on 5000 | Brier 0.609 | History 31306 | HA 0.22 SH 0.1 Cap 3.5</b></p><input id='q' placeholder='Twente vs Willem II' oninput='filt()'><button>Send</button><h2>Top MEGA Predictions</h2><table><tr><th>2</th><th>X</th><th>1</th><th>xG</th><th>Match</th></tr>"""
mid="""</table><h2>All Matches After Break - """+str(len(alls))+"""</h2><p id='cnt'></p><table><tr><th>Date</th><th>Match</th><th>xG</th><th>1</th><th>X</th><th>2</th><th>BTTS</th></tr><tbody id='tb'></tbody></table><script>const R="""+js+""";function filt(){let q=document.getElementById('q').value.toLowerCase();let f=R.filter(r=>r.match.toLowerCase().includes(q));document.getElementById('cnt').innerText=f.length+' matches';document.getElementById('tb').innerHTML=f.map(r=>`<tr><td>${r.date||''}</td><td>${r.match}</td><td>${r.xG||''}</td><td>${r['1']||''}%</td><td>${r['X']||''}%</td><td>${r['2']||''}%</td><td>${r.BTTS||''}%</td></tr>`).join('')}filt()</script></body></html>"""
open("index.html","w",encoding="utf-8").write(head+top_html+mid)
print("NEW full index written")
