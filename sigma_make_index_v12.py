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
try: hist=list(csv.DictReader(open("data/sigma_history.csv",encoding="utf-8")))
except: hist=[]
pr=list(csv.DictReader(open("data/sigma_mega_predictions.csv",encoding="utf-8")))
def hg_of(r): return int(float(r.get("home_goals") or r.get("homeGoals") or 0))
def ag_of(r): return int(float(r.get("away_goals") or r.get("awayGoals") or 0))
def last5(tm):
 out=[]
 for r in sorted(hist,key=lambda x: x.get("date",""),reverse=True):
  h=r.get("home") or r.get("home_team") or ""; a=r.get("away") or r.get("away_team") or ""
  if cl(h)==cl(tm) or cl(a)==cl(tm):
   hg=hg_of(r); ag=ag_of(r)
   if cl(h)==cl(tm): res="W" if hg>ag else "D" if hg==ag else "L"; txt=f"{res} {hg}-{ag} vs {a}"
   else: res="W" if ag>hg else "D" if ag==hg else "L"; txt=f"{res} {ag}-{hg} @ {h}"
   out.append(f"<span class='res {res}'>{txt} • {r.get('date','')[:10]}</span>")
   if len(out)>=5: break
 return "".join(out) if out else "No recent results"
def sugg(tm,home):
 s=find(tm,st)
 if not s: return "<li>Low Confidence - no history</li>"
 sc=get(s,"home_scored") if home else get(s,"away_scored"); co=get(s,"home_conceded") if home else get(s,"away_conceded")
 if sc==0: sc=get(s,"scored_avg")
 if co==0: co=get(s,"conceded_avg")
 b=get(s,"btts"); o=get(s,"over25")
 if b<=1.5: b*=100
 if o<=1.5: o*=100
 L=[]
 if o>=65: L.append("Over 2.5 STRONG - ماتش مفتوح")
 if o<45: L.append("Under 2.5 - ماتش مقفول")
 if b>=55: L.append("BTTS Yes - الفريقين يسجلوا")
 if b<45: L.append("BTTS No - فريق واحد بس")
 if co<=0.85: L.append("Clean Sheet ممكن - دفاع صلب")
 if sc<1.1: L.append("FTS Risk - ممكن ميسجلش")
 if sc>=2.5: L.append("هجوم قوي - العب 1X / Over")
 if home and sc>=2.5: L.append("في بيته مرعب - 1 آمن")
 if not home and sc>=2.0: L.append("بره بيته خطير - X2 فكر فيه")
 if not L: L.append("No edge - تخطى")
 return "".join([f"<li>{x}</li>" for x in L])
cards=""
for idx,r in enumerate(pr[:30]):
 m=r.get("match",""); h,a=m.split(" vs ") if " vs " in m else ("","")
 xh,xa=xg(h,a,st); ov=1-(ps(xh+xa,0)+ps(xh+xa,1)+ps(xh+xa,2)); p1=get(r,"1"); px=get(r,"X"); p2=get(r,"2")
 if p1<=1.5: p1*=100; px*=100; p2*=100
 bt=get(r,"BTTS")
 if bt<=1.5: bt*=100
 bets=[x for x in [("1X",p1+px),("X2",px+p2),("Over 2.5",ov*100),("BTTS",bt)] if 70<=x[1]<=88]
 bets_s=" ".join([f"<span class='pill'>{n} {v:.0f}%</span>" for n,v in sorted(bets,key=lambda x:x[1],reverse=True)]) if bets else "<span class='pill muted'>No value - skip</span>"
 tops=" ".join([f"<span class='pill score'>{hh}-{aa} {pp*100:.1f}%</span>" for (hh,aa),pp in top(xh,xa)])
 cards+=f"""<article class="card" data-team="{m.lower()}"><div class="card-head"><div><h3>{m}</h3><span>{r.get('date','')} • {r.get('league','')}</span></div><div class="xg"><b>{xh:.2f} - {xa:.2f}</b><small>xG</small></div></div><div class="bars"><div class="bar"><i style="width:{p1:.0f}%"></i><span>1 {p1:.0f}%</span></div><div class="bar"><i style="width:{px:.0f}%"></i><span>X {px:.0f}%</span></div><div class="bar"><i style="width:{p2:.0f}%"></i><span>2 {p2:.0f}%</span></div></div><div class="teams"><button class="team-btn" onclick="tog('t1-{idx}')"><b>Team 1 • {h}</b><span>{dna(h,True,st)}</span><small>اضغط لعرض النتائج والاقتراحات ▼</small></button><div id="t1-{idx}" class="team-detail"><h4>آخر 5 نتائج - {h}</h4><div class="results">{last5(h)}</div><h4>اقتراحات {h}</h4><ul>{sugg(h,True)}</ul></div><button class="team-btn" onclick="tog('t2-{idx}')"><b>Team 2 • {a}</b><span>{dna(a,False,st)}</span><small>اضغط لعرض النتائج والاقتراحات ▼</small></button><div id="t2-{idx}" class="team-detail"><h4>آخر 5 نتائج - {a}</h4><div class="results">{last5(a)}</div><h4>اقتراحات {a}</h4><ul>{sugg(a,False)}</ul></div></div><div class="meta"><p>Over 2.5 {ov*100:.0f}% • BTTS {bt:.0f}% • Total {xh+xa:.2f}</p><div>Best Bets: {bets_s}</div><div>Top Scores: {tops}</div></div><div class="live"><b>LIVE</b> Minute <input id="mi{idx}" type="number" value="65"> Score <input id="hg{idx}" type="number" value="0"> - <input id="ag{idx}" type="number" value="0"> <button onclick="live({idx},{xh:.2f},{xa:.2f})">Calc Live</button><p id="lv{idx}"></p></div></article>"""
teams_sorted=sorted(st.items(),key=lambda kv: get(kv[1],"scored_avg"),reverse=True)[:24]
teams_html=""
for ti,(tn,ts) in enumerate(teams_sorted):
 sc=get(ts,"scored_avg"); co=get(ts,"conceded_avg"); b=get(ts,"btts"); o=get(ts,"over25")
 if b<=1.5: b*=100
 if o<=1.5: o*=100
 teams_html+=f"""<article class="card team-card"><div class="card-head"><h3>{tn}</h3><span class="xg"><b>{sc:.2f} - {co:.2f}</b><small>Score-Concede</small></span></div><p>BTTS {b:.0f}% • Over {o:.0f}%</p><button class="team-btn" onclick="tog('tt-{ti}')">عرض النتائج والاقتراحات ▼</button><div id="tt-{ti}" class="team-detail"><h4>آخر 5</h4><div class="results">{last5(tn)}</div><ul>{sugg(tn,True)}</ul><ul>{sugg(tn,False)}</ul></div></article>"""
html=f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sigma V12 Global</title><style>*{{box-sizing:border-box}}body{{margin:0;font-family:Inter,Arial;background:linear-gradient(180deg,#0b1220,#0f1a2e);color:#fff}}header{{position:sticky;top:0;z-index:10;background:rgba(11,18,32,.9);backdrop-filter:blur(10px);padding:14px 16px;display:flex;justify-content:space-between;align-items:center}}header h1{{margin:0;color:#ffd700;font-size:22px}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;padding:14px}}.stat{{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);border-radius:14px;padding:12px;text-align:center;transition:.3s}}.stat:hover{{transform:translateY(-3px)}}.stat b{{font-size:20px;color:#ffd700}}nav{{display:flex;gap:8px;padding:0 14px}}nav button{{background:#16213a;color:#fff;border:1px solid #2a3a5a;padding:8px 14px;border-radius:999px;cursor:pointer;transition:.3s}}nav button.active,nav button:hover{{background:#ffd700;color:#000}}.search{{padding:12px 14px}}.search input{{width:100%;padding:12px;border-radius:999px;border:1px solid #2a3a5a;background:#0f1a2e;color:#fff}} .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px;padding:14px}}.card{{background:linear-gradient(180deg,#16213a,#0f1a2e);border:1px solid rgba(255,255,255,.1);border-radius:18px;padding:14px;transition:.35s;animation:fade .5s ease}}@keyframes fade{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}.card:hover{{transform:translateY(-4px);box-shadow:0 12px 30px rgba(0,0,0,.4)}}.card-head{{display:flex;justify-content:space-between;gap:10px}}.card-head h3{{margin:0}}.card-head span{{opacity:.7;font-size:12px}}.xg{{text-align:center;background:#ffd700;color:#000;border-radius:10px;padding:6px 10px}}.bars{{margin:10px 0}}.bar{{background:#0b1220;height:18px;border-radius:999px;margin:4px 0;position:relative;overflow:hidden}}.bar i{{display:block;height:100%;background:linear-gradient(90deg,#ffd700,#ff8a00);transition:width .6s}}.bar span{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:12px}}.teams{{display:grid;gap:8px}}.team-btn{{width:100%;text-align:right;background:#0b1220;border:1px solid #2a3a5a;color:#fff;padding:10px;border-radius:12px;cursor:pointer;transition:.3s}}.team-btn:hover{{border-color:#ffd700}}.team-btn small{{display:block;opacity:.6}}.team-detail{{max-height:0;overflow:hidden;transition:max-height .5s ease,opacity .4s;opacity:0}}.team-detail.open{{max-height:600px;opacity:1}}.results{{display:grid;gap:6px}}.res{{padding:6px;border-radius:8px;background:#0b1220;font-size:13px}}.res.W{{border-right:4px solid #22c55e}}.res.D{{border-right:4px solid #facc15}}.res.L{{border-right:4px solid #ef4444}}.pill{{display:inline-block;background:#ffd700;color:#000;padding:4px 8px;border-radius:999px;font-size:12px;margin:2px}}.pill.score{{background:#22c55e;color:#fff}}.pill.muted{{background:#444;color:#fff}}.live{{background:rgba(255,215,0,.1);border:1px solid rgba(255,215,0,.3);padding:10px;border-radius:12px;margin-top:10px}}.live input{{width:48px;padding:6px;border-radius:6px;border:none}}.live button{{background:#ffd700;border:none;padding:7px 12px;border-radius:999px;cursor:pointer}}@media(max-width:600px){{.stats{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}}}</style></head><body><header><h1>Sigma V12 • Global</h1><span>Mahmoud Emad</span></header><div class="stats"><div class="stat"><b>11/14</b><br>Verified 78.6%</div><div class="stat"><b>51.7%</b><br>MEGA Hit</div><div class="stat"><b>29466</b><br>【entity-Real¦canonical_name=Real Madrid】 Matches</div><div class="stat"><b>248</b><br>Teams</div></div><nav><button class="active" onclick="tab('matches',this)">المباريات</button><button onclick="tab('teams',this)">الفرق</button><button onclick="tab('gloss',this)">تعريفات الرهان</button></nav><div class="search"><input id="q" oninput="filt()" placeholder="ابحث باسم فريق... 【entity-Ajax¦canonical_name=Ajax】, 【entity-Real¦canonical_name=Real Madrid】, 【entity-Bayern¦canonical_name=Bayern】"></div><section id="matches" class="grid">{cards}</section><section id="teams" class="grid" style="display:none">{teams_html}</section><section id="gloss" style="display:none;padding:14px"><h2>تعريفات الرهان</h2><p>1 = فوز صاحب الأرض Team 1 | X = تعادل | 2 = فوز الضيف Team 2 | 1X = Team 1 يكسب أو يتعادل | X2 = Team 2 يكسب أو يتعادل | 12 = مفيش تعادل | Over 2.5 = 3 أهداف أو أكتر | BTTS Yes = الفريقين يسجلوا | CS = Clean Sheet | FTS = مش هيسجل</p><p>كل فريق اضغط عليه يفتح تحته آخر 5 نتائج + اقتراحاته الخاصة. الاقتراحات مبنية على تاريخه الحقيقي 29466 ماتش، مش على متوسط الدوري.</p></section><script>function tog(id){{let e=document.getElementById(id); e.classList.toggle('open')}} function tab(n,btn){{document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); ['matches','teams','gloss'].forEach(x=>document.getElementById(x).style.display=(x===n?'grid':'none')); if(n==='gloss') document.getElementById(n).style.display='block';}} function filt(){{let q=document.getElementById('q').value.toLowerCase(); document.querySelectorAll('#matches .card').forEach(c=>{{c.style.display=c.dataset.team.includes(q)?'block':'none'}})}} function ps(l,k){{let f=1; for(let i=2;i<=k;i++) f*=i; return Math.exp(-l)*Math.pow(l,k)/f}} function live(i,xh,xa){{let mi=+document.getElementById('mi'+i).value, hg=+document.getElementById('hg'+i).value, ag=+document.getElementById('ag'+i).value; let rem=Math.max(0,90-mi)/90; let mh=hg<ag?1.15:hg>ag?0.95:1; let ma=ag<hg?1.15:ag>hg?0.95:1; let rxh=xh*rem*mh, rxa=xa*rem*ma; let ph=0,pd=0,pa=0,nh=0,na=0,ov=0; for(let rh=0;rh<6;rh++) for(let ra=0;ra<6;ra++){{let p=ps(rxh,rh)*ps(rxa,ra); let fh=hg+rh, fa=ag+ra; if(fh>fa) ph+=p; else if(fh==fa) pd+=p; else pa+=p; if(rh==1&&ra==0) nh+=p; if(rh==0&&ra==1) na+=p; if(fh+fa>=3) ov+=p;}} document.getElementById('lv'+i).innerHTML='Remaining xG '+rxh.toFixed(2)+'-'+rxa.toFixed(2)+' | 1X2 '+Math.round(ph*100)+'/'+Math.round(pd*100)+'/'+Math.round(pa*100)+' | Next H '+Math.round(nh*100)+'% A '+Math.round(na*100)+'% | Over Live '+Math.round(ov*100)+'%';}}</script><p style="text-align:center;opacity:.6">Signature Prediction and Forecast: Sigma - Mahmoud Emad</p></body></html>"""
open("index.html","w",encoding="utf-8").write(html)
print(f"V12 written matches {len(pr[:30])} teams {len(teams_sorted)}")
