import csv, json, math
def ps(l,k): return math.exp(-l)*l**k/math.factorial(k)
def cl(s): return (s or "").lower().replace("fc ","").replace("cf ","").replace("afc ","").strip()
def find(n,st):
 c=cl(n)
 for k in st:
  if cl(k)==c: return st[k]
 for k in st:
  if c in cl(k) or cl(k) in c: return st[k]
 return None
def get(d,*ks):
 for k in ks:
  if k in d and d[k] not in (None,""):
   try: return float(d[k])
   except: pass
 for kk,v in d.items():
  for w in ks:
   if w.lower() in kk.lower():
    try: return float(v)
    except: pass
 return 0.0
def xg(hm,aw,st):
 hs=find(hm,st); as_=find(aw,st)
 if not hs or not as_: return 1.5,1.0
 h1=get(hs,"home_scored"); c1=get(hs,"home_conceded"); a1=get(as_,"away_scored"); c2=get(as_,"away_conceded")
 if h1==0: h1=get(hs,"scored_avg")
 if a1==0: a1=get(as_,"scored_avg")
 return max(.2,min(3.5,(h1+c2)/2*1.1)), max(.2,min(3.5,(a1+c1)/2))
def top(xh,xa):
 sc=[]
 for h in range(6):
  for a in range(6): sc.append(((h,a),ps(xh,h)*ps(xa,a)))
 sc.sort(key=lambda x:x[1],reverse=True); return sc[:3]
def dna(tm,home,st):
 s=find(tm,st)
 if not s: return tm+" No history"
 sc=get(s,"home_scored") if home else get(s,"away_scored"); co=get(s,"home_conceded") if home else get(s,"away_conceded")
 if sc==0: sc=get(s,"scored_avg")
 if co==0: co=get(s,"conceded_avg")
 b=get(s,"btts"); o=get(s,"over25")
 if b<=1.5: b*=100
 if o<=1.5: o*=100
 id="Elite" if sc>=2.5 and co<=1 else "Attack" if sc>=2.2 else "Defense" if co<=.9 else "Weak" if sc<1.2 else "Balanced"
 return f"{id} {sc:.2f}-{co:.2f} BTTS {b:.0f}% Over {o:.0f}%"
try: st=json.load(open("data/sigma_team_stats.json",encoding="utf-8"))
except: st={}
if isinstance(st,list): st={x.get("team",str(i)):x for i,x in enumerate(st)}
pr=list(csv.DictReader(open("data/sigma_mega_predictions.csv",encoding="utf-8")))
cards=""
for idx,r in enumerate(pr[:30]):
 m=r.get("match",""); h,a=m.split(" vs ") if " vs " in m else ("","")
 xh,xa=xg(h,a,st); ov=1-(ps(xh+xa,0)+ps(xh+xa,1)+ps(xh+xa,2)); p1=get(r,"1"); px=get(r,"X"); p2=get(r,"2")
 if p1<=1.5: p1*=100; px*=100; p2*=100
 bt=get(r,"BTTS")
 if bt<=1.5: bt*=100
 bets=[x for x in [("1X",p1+px),("X2",px+p2),("Over 2.5",ov*100),("BTTS",bt)] if 70<=x[1]<=88]
 bets_s=", ".join([f"{n} {v:.0f}%" for n,v in sorted(bets,key=lambda x:x[1],reverse=True)]) if bets else "No value - skip"
 tops=", ".join([f"{hh}-{aa} {pp*100:.1f}%" for (hh,aa),pp in top(xh,xa)])
 cards+=f"""<div class="card"><h3>{m}</h3><p>{r.get('date','')} | {r.get('league','')}</p><div class="two"><div><b>Team 1 - {h}</b><br>{dna(h,True,st)}</div><div><b>Team 2 - {a}</b><br>{dna(a,False,st)}</div></div><p>xG <b>{xh:.2f}-{xa:.2f}</b> Total {xh+xa:.2f} | Over 2.5 {ov*100:.0f}% BTTS {bt:.0f}% | 1X2 {p1:.0f}/{px:.0f}/{p2:.0f}</p><p><b>Best Bets:</b> {bets_s}</p><p><b>Top Scores:</b> {tops}</p><div class="live"><b>LIVE Calculator</b><br>Minute <input id="mi{idx}" type="number" value="65" style="width:50px"> Score <input id="hg{idx}" type="number" value="0" style="width:40px"> - <input id="ag{idx}" type="number" value="0" style="width:40px"> <button onclick="live({idx},{xh:.2f},{xa:.2f})">Calc Live</button><p id="lv{idx}"></p></div></div>"""
html=f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sigma V11 - Bet Card + Live</title><style>body{{font-family:Arial;background:#0b1220;color:#fff;margin:0;padding:12px}}h1{{color:#ffd700}}h2{{color:#7ee787}}.card{{background:#16213a;border-radius:12px;padding:12px;margin:10px 0}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}.two div{{background:#0f1a2e;padding:8px;border-radius:8px}}.live{{background:#1a2b4a;padding:8px;border-radius:8px;margin-top:8px}}button{{background:#ffd700;border:none;padding:6px 10px;border-radius:6px;cursor:pointer}}input{{padding:4px;border-radius:4px;border:none}}</style></head><body><h1>Sigma V11 - Bet Card + Live</h1><p>Verified 11/14 = 78.6% | MEGA 51.7% | History 29466 Real | 248 Teams</p><h2>Glossary - تعريفات الرهان</h2><p>1 = فوز صاحب الأرض (Team 1) | X = تعادل | 2 = فوز الضيف (Team 2) | 1X = Team 1 يكسب أو يتعادل | X2 = Team 2 يكسب أو يتعادل | 12 = مفيش تعادل | Over 2.5 = 3 أهداف أو أكتر | BTTS Yes = الفريقين يسجلوا | CS = Clean Sheet | FTS = مش هيسجل</p><h2>Top 30 Matches - Bet Cards</h2>{cards}<script>function ps(l,k){{let f=1; for(let i=2;i<=k;i++) f*=i; return Math.exp(-l)*Math.pow(l,k)/f}} function live(i,xh,xa){{let mi=+document.getElementById('mi'+i).value, hg=+document.getElementById('hg'+i).value, ag=+document.getElementById('ag'+i).value; let rem=Math.max(0,90-mi)/90; let mh=hg<ag?1.15:hg>ag?0.95:1; let ma=ag<hg?1.15:ag>hg?0.95:1; let rxh=xh*rem*mh, rxa=xa*rem*ma; let ph=0,pd=0,pa=0,nh=0,na=0,ov=0; for(let rh=0;rh<6;rh++) for(let ra=0;ra<6;ra++){{let p=ps(rxh,rh)*ps(rxa,ra); let fh=hg+rh, fa=ag+ra; if(fh>fa) ph+=p; else if(fh==fa) pd+=p; else pa+=p; if(rh==1&&ra==0) nh+=p; if(rh==0&&ra==1) na+=p; if(fh+fa>=3) ov+=p;}} document.getElementById('lv'+i).innerHTML='Remaining xG '+rxh.toFixed(2)+'-'+rxa.toFixed(2)+' | 1X2 '+Math.round(ph*100)+'/'+Math.round(pd*100)+'/'+Math.round(pa*100)+' | Next H '+Math.round(nh*100)+'% A '+Math.round(na*100)+'% | Over Live '+Math.round(ov*100)+'%';}}</script><p>Signature Prediction and Forecast: Sigma - Mahmoud Emad</p></body></html>"""
open("index.html","w",encoding="utf-8").write(html)
print(f"V11 written: {len(pr[:30])} cards")
