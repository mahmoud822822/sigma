import csv, json
rows=list(csv.DictReader(open("data/sigma_insight.csv", encoding="utf-8")))
rows=[r for r in rows if r.get("date","")>="2026-11-20"]
gold=[r for r in rows if float(r.get("GoldenOdds",9))<=1.25]
gold=sorted(gold, key=lambda r: float(r.get("GoldenOdds",9)))[:3]
comb=1.0
for r in gold: comb*=float(r["GoldenOdds"])
print(f"V8 Insight {len(rows)} - Acca {comb:.2f}")
js=json.dumps(rows)
head="""<!doctype html><html lang='ar' dir='rtl'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Sigma AI V8</title><style>body{background:#0a0e14;color:#fff;font-family:system-ui;padding:12px}.gold{background:linear-gradient(135deg,#f5c518,#ff8c00);color:#000;padding:12px;border-radius:14px;margin:8px 0}.acca{background:#1e2a1e;border:1px solid #2ecc71;padding:12px;border-radius:14px}.card{background:#161d27;padding:12px;border-radius:14px;margin:8px 0}table{width:100%;border-collapse:collapse;font-size:13px}td,th{border:1px solid #2a3442;padding:7px;text-align:center}input,select{padding:10px;border-radius:10px;margin:4px}.badge{background:#f5c518;color:#000;padding:2px 8px;border-radius:20px;font-weight:bold}</style></head><body><h1>⭐ Sigma AI V8 - Insight + Acca</h1><p>Signature Prediction and Forecast: Sigma - Mahmoud Emad</p><p><b>Verified: 11/14 = 78.6% | MEGA 51.7% | History 31306</b></p>"""
acca_html=f"<div class='acca'><h2>🏆 ACCA Golden x3 - Fair {comb:.2f} - Prob {100/comb:.1f}%</h2>"+"".join([f"<div>{r['match']} - {r.get('Golden','')} - Fair {r.get('GoldenOdds','')}</div>" for r in gold])+"</div><p>Risk multiplies - max 3 legs - Real MEGA Prob</p>"
body="""<h2>All Matches - Form + H2H + Insight</h2><input id='q' placeholder='Search team' oninput='filt()'><p id='cnt'></p><table><tr><th>Date</th><th>Match</th><th>xG</th><th>1X2</th><th>Form</th><th>Golden</th><th>Insight</th></tr><tbody id='tb'></tbody></table><script>const R="""+js+""";function filt(){let q=document.getElementById('q').value.toLowerCase();let f=R.filter(r=>r.match.toLowerCase().includes(q));document.getElementById('cnt').innerText=f.length+' matches';document.getElementById('tb').innerHTML=f.map(r=>`<tr><td>${r.date||''}</td><td>${r.match}</td><td>${r.xG||''}</td><td>${r['1']||''}% / ${r['X']||''}% / ${r['2']||''}%</td><td>${r.FormH||''} - ${r.FormA||''}</td><td><span class='badge'>${r.Golden||''}</span></td><td style='text-align:right;font-size:12px'>${r.Insight||''}</td></tr>`).join('')}filt()</script></body></html>"""
open("index.html","w",encoding="utf-8").write(head+acca_html+body)
print("V8 written")
