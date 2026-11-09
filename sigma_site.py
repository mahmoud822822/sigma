import csv, json
pred=list(csv.DictReader(open("data/sigma_mega_predictions.csv", encoding="utf-8")))
ver=list(csv.DictReader(open("data/sigma_real_verified.csv", encoding="utf-8")))
hit=sum(1 for r in ver if r.get("bet_result")=="correct")
m=json.load(open("data/sigma_super_model.json", encoding="utf-8"))
pred=sorted(pred, key=lambda x: float(x.get("conf",0)), reverse=True)
rows=""
for p in pred:
    rows+=f"<tr><td>{p['date']}</td><td>{p['match']}</td><td>{p['league']}</td><td>{p['xG']}</td><td>{p['1']}%</td><td>{p['X']}%</td><td>{p['2']}%</td><td>{p['BTTS']}%</td><td>{p['Over25']}%</td><td>{p['top']}</td></tr>\n"
html=f"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sigma - Predictions</title><style>body{{background:#0b0f14;color:#fff;font-family:system-ui;padding:12px}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{border:1px solid #333;padding:6px;text-align:center}}th{{background:#1a2230}}input{{width:100%;padding:10px;margin:10px 0;border-radius:8px;border:1px solid #333;background:#111;color:#fff}}</style></head><body><h2>Sigma - Mahmoud Emad</h2><p>Verified: {hit}/{len(ver)} = {hit/len(ver)*100:.1f}% | Model HA={m.get('best_home_adv')} SH={m.get('best_shrink')} Brier={round(m.get('brier',0),3)} Hit={round(m.get('hit',0)*100,1)}% | Forward: {len(pred)} matches | History: {m.get('total_history')}</p><input id="q" placeholder="ابحث بفريق او دوري..." oninput="let q=this.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(q)?'':'none')"><table><thead><tr><th>Date</th><th>Match</th><th>League</th><th>xG</th><th>1</th><th>X</th><th>2</th><th>BTTS</th><th>Over</th><th>Top</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""
open("predictions.html","w",encoding="utf-8").write(html)
print(f"Saved predictions.html {len(pred)} matches")
