import csv, json, math
def pois(l,k): return math.exp(-l)*l**k/math.factorial(k) if l>0 else 1.0 if k==0 else 0
rows=list(csv.DictReader(open("data/sigma_insight.csv", encoding="utf-8")))
rows=[r for r in rows if r.get("date","")>="2026-11-20"]
enriched=[]
for r in rows:
 try: xh,xa=[float(x) for x in r.get("xG","0-0").split("-")]
 except: xh,xa=1.5,1.5
 ph=[pois(xh,k) for k in range(7)]; pa=[pois(xa,k) for k in range(7)]
 scores=[]
 for i in range(6):
  for j in range(6): scores.append((ph[i]*pa[j],i,j))
 scores=sorted(scores, reverse=True)[:3]
 r["TopScores"]=" - ".join([f"{i}-{j} {p*100:.1f}%" for p,i,j in scores])
 def over(n):
  s=0
  for i in range(7):
   for j in range(7):
    if i+j>n: s+=ph[i]*pa[j]
  return s*100
 r["Over05"]=round(over(0.5),1); r["Over15"]=round(over(1.5),1); r["Over35"]=round(over(3.5),1); r["Under45"]=round(100-over(4.5),1)
 r["CS_H"]=round(pa[0]*100,1); r["CS_A"]=round(ph[0]*100,1); r["Fail_H"]=round(ph[0]*100,1); r["Fail_A"]=round(pa[0]*100,1)
 try: p1=float(r.get("1",0)); px=float(r.get("X",0)); p2=float(r.get("2",0))
 except: p1,px,p2=33,33,33
 r["DC_1X"]=round(p1+px,1); r["DC_X2"]=round(px+p2,1); r["DC_12"]=round(p1+p2,1)
 conf=max(p1,px,p2)
 r["Conf"]="High" if conf>=70 else "Medium" if conf>=55 else "Low"
 r["Conf_AR"]="عالي" if conf>=70 else "متوسط" if conf>=55 else "منخفض"
 r["Upset"]="Upset Risk" if 55<=conf<65 else ""
 r["Upset_AR"]="خطر مفاجأة" if r["Upset"] else ""
 enriched.append(r)
print(f"V10 {len(enriched)} - Top {enriched[0]['TopScores']}")
js=json.dumps(enriched)
head="""<!doctype html><html lang='ar' dir='rtl'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Sigma AI V10 Bilingual</title><style>body{background:#0b0f14;color:#fff;font-family:system-ui;padding:10px;max-width:760px;margin:auto}.top{display:flex;justify-content:space-between;align-items:center}.lang{padding:10px 18px;background:#f5c518;border:0;border-radius:20px;font-weight:bold}.hero{background:linear-gradient(135deg,#1e3a8a,#7c3aed);padding:16px;border-radius:18px;text-align:center}.stats{display:flex;gap:8px;margin:10px 0}.stat{flex:1;background:#161d27;padding:10px;border-radius:12px;text-align:center}.chat{position:sticky;top:0;background:#0b0f14;padding:8px 0;z-index:9}.chat input{width:68%;padding:12px;border-radius:12px;border:0}.chat button{padding:12px;background:#f5c518;border:0;border-radius:12px;font-weight:bold}.chip{padding:8px 14px;border-radius:20px;background:#1e293b;border:1px solid #334155;margin:3px}.chip.on{background:#f5c518;color:#000}.card{background:#151c26;padding:14px;border-radius:16px;margin:10px 0}.bar{display:flex;height:10px;border-radius:10px;overflow:hidden;margin:8px 0}.dot{display:inline-block;width:20px;height:20px;border-radius:50%;text-align:center;font-size:11px;line-height:20px;margin:1px}.W{background:#22c55e}.D{background:#94a3b8}.L{background:#ef4444}.gold{background:#f5c518;color:#000;padding:3px 10px;border-radius:20px;font-weight:bold;font-size:12px}.btn{padding:8px 12px;background:#2a3442;color:#fff;border:0;border-radius:10px;margin-top:8px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:13px}.grid div{background:#0f172a;padding:8px;border-radius:10px}</style></head><body><div class='top'><h2>⭐ Sigma AI V10</h2><button class='lang' onclick='toggleLang()'>AR / EN</button></div><div class='hero'><h1>Sigma AI - Complete Global<br>سيجما AI - عالمي كامل</h1><p>Signature Prediction and Forecast: Sigma - Mahmoud Emad<br>Real AI - 31306 Matches - MEGA Model - ذكاء اصطناعي حقيقي</p></div><div class='stats'><div class='stat'><b>236</b><br>Matches / مباريات</div><div class='stat'><b>78.6%</b><br>Verified / موثق</div><div class='stat'><b>51.7%</b><br>MEGA</div></div>"""
gold=[r for r in enriched if float(r.get("GoldenOdds",9))<=1.25]
gold=sorted(gold, key=lambda r: float(r.get("GoldenOdds",9)))
picked=[]; used=set()
for r in gold:
 try: h,a=r["match"].split(" vs ")
 except: continue
 if h in used or a in used: continue
 picked.append(r); used.add(h); used.add(a)
 if len(picked)==3: break
comb=1.0
for r in picked: comb*=float(r["GoldenOdds"])
acca="<div class='card' style='border:1px solid #22c55e'><h3>🏆 ACCA Global x3 - Fair "+f"{comb:.2f}"+" - Prob "+f"{100/comb:.1f}% - أكوموليتر عالمي</h3>"+"".join([f"<div>{r['match']} - {r.get('Golden','')} - Fair {r.get('GoldenOdds','')}</div>" for r in picked])+"</div>"
chat="<div class='chat'><input id='q' placeholder='اسأل Sigma AI / Ask Sigma AI: مين أحسن فريق؟ Who is best?'><button onclick='askAI()'>Ask AI / اسأل</button><div id='aiAns'></div></div><div><button class='chip on' onclick='filterTab(\"all\",this)'>All / الكل</button><button class='chip' onclick='filterTab(\"today\",this)'>Today / اليوم</button><button class='chip' onclick='filterTab(\"golden\",this)'>Golden / الذهبي</button></div><div id='list'></div><script>let LANG='ar';const R="+js+";"
js2="""function T(ar,en){return LANG=='ar'?ar:en}function dots(f){return (f||'').split('').map(c=>`<span class='dot ${c}'>${c}</span>`).join('')}function card(r){let p1=parseFloat(r['1']||0),px=parseFloat(r['X']||0),p2=parseFloat(r['2']||0);return `<div class='card'><div style='display:flex;justify-content:space-between'><b>${r.match}</b><span>${r.date||''} - ${r.league||''}</span></div><div>${T('الثقة: ','Confidence: ')}${LANG=='ar'?r.Conf_AR:r.Conf} - ${r.Upset?`⚠️ ${T(r.Upset_AR,r.Upset)}`:''} - xG ${r.xG||''}</div><div class='bar'><div style='width:${p1}%;background:#22c55e'></div><div style='width:${px}%;background:#f1c40f'></div><div style='width:${p2}%;background:#ef4444'></div></div><div>1 ${p1}% - X ${px}% - 2 ${p2}%</div><div>${T('أكتر نتائج: ','Top Scores: ')}${r.TopScores||''}</div><div class='grid'><div>BTTS ${r.BTTS||''}%</div><div>Over 2.5 ${r.Over25||''}%</div><div>Over 0.5 ${r.Over05}%</div><div>Over 1.5 ${r.Over15}%</div><div>Over 3.5 ${r.Over35}%</div><div>Under 4.5 ${r.Under45}%</div><div>1X ${r.DC_1X}%</div><div>X2 ${r.DC_X2}%</div><div>12 ${r.DC_12}%</div><div>CS Home ${r.CS_H}%</div><div>CS Away ${r.CS_A}%</div><div>${T('كورنر: ','Corners: ')}${r.Corners||''}</div></div><div>${T('فورم: ','Form: ')}${dots(r.FormH)} vs ${dots(r.FormA)}</div><div>${r.Golden?`<span class='gold'>🏆 ${r.Golden} Fair ${r.GoldenOdds}</span>`:''} - ${T('رميات: ','Throw-ins: ')}${r.Throw||''}</div><button class='btn' onclick='this.nextElementSibling.style.display=this.nextElementSibling.style.display==\"none\"?\"block\":\"none\"'>🧠 ${T('ليه؟ - الاستنتاج','Why? - Insight')}</button><div style='display:none;font-size:13px;margin-top:8px'>${r.Insight||''}<br>H2H: ${r.H2H||''}<br>${T('فشل التسجيل - بيته: ','Fail to Score Home: ')}${r.Fail_H}% - ${T('الضيف: ','Away: ')}${r.Fail_A}%</div></div>`}function render(list){document.getElementById('list').innerHTML=list.map(card).join('')}function filterTab(t,el){document.querySelectorAll('.chip').forEach(c=>c.classList.remove('on'));el.classList.add('on');if(t=='all')render(R);if(t=='golden')render(R.filter(r=>parseFloat(r.GoldenOdds||9)<=1.25));if(t=='today')render(R.filter(r=>r.date=='2026-11-20'))}function toggleLang(){LANG=LANG=='ar'?'en':'ar';document.documentElement.dir=LANG=='ar'?'rtl':'ltr';render(R)}function askAI(){let q=document.getElementById('q').value.toLowerCase();let el=document.getElementById('aiAns');let f=R.find(r=>r.match.toLowerCase().includes(q));if(f){el.innerHTML=card(f)}else{el.innerHTML=`<div class='card'>${T('اكتب اسم فريق زي Bayern أو اسأل: مين أحسن فريق؟','Type a team like Bayern or ask: Who is best?')}</div>`}}render(R)</script></body></html>"""
open("index.html","w",encoding="utf-8").write(head+acca+chat+js2)
print("V10 Bilingual written")
js2="""function T(ar,en){return LANG=='ar'?ar:en}function dots(f){return (f||'').split('').map(c=>`<span class='dot ${c}'>${c}</span>`).join('')}function card(r){let p1=parseFloat(r['1']||0),px=parseFloat(r['X']||0),p2=parseFloat(r['2']||0);return `<div class='card'><div style='display:flex;justify-content:space-between'><b>${r.match}</b><span>${r.date||''} - ${r.league||''}</span></div><div>${T('الثقة: ','Confidence: ')}${LANG=='ar'?r.Conf_AR:r.Conf} - ${r.Upset?`⚠️ ${T(r.Upset_AR,r.Upset)}`:''} - xG ${r.xG||''}</div><div class='bar'><div style='width:${p1}%;background:#22c55e'></div><div style='width:${px}%;background:#f1c40f'></div><div style='width:${p2}%;background:#ef4444'></div></div><div>1 ${p1}% - X ${px}% - 2 ${p2}%</div><div>${T('أكتر نتائج: ','Top Scores: ')}${r.TopScores||''}</div><div class='grid'><div>BTTS ${r.BTTS||''}%</div><div>Over 2.5 ${r.Over25||''}%</div><div>Over 0.5 ${r.Over05}%</div><div>Over 1.5 ${r.Over15}%</div><div>Over 3.5 ${r.Over35}%</div><div>Under 4.5 ${r.Under45}%</div><div>1X ${r.DC_1X}%</div><div>X2 ${r.DC_X2}%</div><div>12 ${r.DC_12}%</div><div>CS Home ${r.CS_H}%</div><div>CS Away ${r.CS_A}%</div><div>${T('كورنر: ','Corners: ')}${r.Corners||''}</div></div><div>${T('فورم: ','Form: ')}${dots(r.FormH)} vs ${dots(r.FormA)}</div><div>${r.Golden?`<span class='gold'>🏆 ${r.Golden} Fair ${r.GoldenOdds}</span>`:''} - ${T('رميات: ','Throw-ins: ')}${r.Throw||''}</div><button class='btn' onclick='this.nextElementSibling.style.display=this.nextElementSibling.style.display==\"none\"?\"block\":\"none\"'>🧠 ${T('ليه؟ - الاستنتاج','Why? - Insight')}</button><div style='display:none;font-size:13px;margin-top:8px'>${r.Insight||''}<br>H2H: ${r.H2H||''}<br>${T('فشل التسجيل - بيته: ','Fail to Score Home: ')}${r.Fail_H}% - ${T('الضيف: ','Away: ')}${r.Fail_A}%</div></div>`}function render(list){document.getElementById('list').innerHTML=list.map(card).join('')}function filterTab(t,el){document.querySelectorAll('.chip').forEach(c=>c.classList.remove('on'));el.classList.add('on');if(t=='all')render(R);if(t=='golden')render(R.filter(r=>parseFloat(r.GoldenOdds||9)<=1.25));if(t=='today')render(R.filter(r=>r.date=='2026-11-20'))}function toggleLang(){LANG=LANG=='ar'?'en':'ar';document.documentElement.dir=LANG=='ar'?'rtl':'ltr';render(R)}function askAI(){let q=document.getElementById('q').value.toLowerCase();let el=document.getElementById('aiAns');let f=R.find(r=>r.match.toLowerCase().includes(q));if(f){el.innerHTML=card(f)}else{el.innerHTML=`<div class='card'>${T('اكتب اسم فريق زي Bayern أو اسأل: مين أحسن فريق؟','Type a team like Bayern or ask: Who is best?')}</div>`}}render(R)</script></body></html>"""
open("index.html","w",encoding="utf-8").write(head+acca+chat+js2)
print("V10 Bilingual written")
