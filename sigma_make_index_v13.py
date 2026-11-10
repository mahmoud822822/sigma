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
try: st=json.load(open("data/sigma_team_stats.json",encoding="utf-8"))
except: st={}
if isinstance(st,list): st={x.get("team",str(i)):x for i,x in enumerate(st)}
try: hist=list(csv.DictReader(open("data/sigma_history.csv",encoding="utf-8")))
except: hist=[]
pr=list(csv.DictReader(open("data/sigma_mega_predictions.csv",encoding="utf-8")))
def hg_of(r): return int(float(r.get("home_goals") or 0))
def ag_of(r): return int(float(r.get("away_goals") or 0))
def last5(tm):
 out=[]
 for r in sorted(hist,key=lambda x: x.get("date",""),reverse=True):
  h=r.get("home") or ""; a=r.get("away") or ""
  if cl(h)==cl(tm) or cl(a)==cl(tm):
   hg=hg_of(r); ag=ag_of(r)
   if cl(h)==cl(tm): res="W" if hg>ag else "D" if hg==ag else "L"
   else: res="W" if ag>hg else "D" if ag==hg else "L"
   out.append(f"<span class='dot {res}'>{res}</span>")
   if len(out)>=5: break
 return "".join(out) if out else "—"
def sugg(tm,home):
 s=find(tm,st)
 if not s: return "<li>لا يوجد تاريخ كافي</li>"
 sc=get(s,"home_scored") if home else get(s,"away_scored"); co=get(s,"home_conceded") if home else get(s,"away_conceded")
 if sc==0: sc=get(s,"scored_avg")
 if co==0: co=get(s,"conceded_avg")
 b=get(s,"btts"); o=get(s,"over25")
 if b<=1.5: b*=100
 if o<=1.5: o*=100
 L=[]
 if o>=65: L.append("Over 2.5 قوي")
 if o<45: L.append("Under 2.5")
 if b>=55: L.append("BTTS نعم")
 if co<=0.85: L.append("Clean Sheet ممكن")
 if sc<1.1: L.append("قد لا يسجل - FTS")
 if sc>=2.5: L.append("هجوم قوي - 1X آمن")
 if not L: L.append("لا توجد أفضلية واضحة")
 return "".join([f"<li>{x}</li>" for x in L])
cards=""
for idx,r in enumerate(pr[:24]):
 m=r.get("match",""); h,a=m.split(" vs ") if " vs " in m else ("","")
 xh,xa=xg(h,a,st); ov=1-(ps(xh+xa,0)+ps(xh+xa,1)+ps(xh+xa,2)); p1=get(r,"1"); px=get(r,"X"); p2=get(r,"2")
 if p1<=1.5: p1*=100; px*=100; p2*=100
 bt=get(r,"BTTS")
 if bt<=1.5: bt*=100
 tops=top(xh,xa); best=f"{tops[0][0][0]}-{tops[0][0][1]} {tops[0][1]*100:.0f}%"
 best_bet="1X" if p1+px>=70 else "X2" if px+p2>=70 else "Over 2.5" if ov*100>=70 else "لا يوجد رهان قيمة"
 cards+=f"""<article class="mcard" data-team="{m.lower()}"><div class="m-top"><span class="lg">{r.get('league','')}</span><span class="dt">{r.get('date','')}</span></div><div class="m-teams"><div class="tm"><div class="av">{h[:1]}</div><b>{h}</b><span class="form">{last5(h)}</span></div><div class="vs">VS</div><div class="tm"><div class="av">{a[:1]}</div><b>{a}</b><span class="form">{last5(a)}</span></div></div><div class="xgb"><div><span>xG {xh:.2f}</span><div class="track"><i style="width:{xh/(xh+xa)*100:.0f}%"></i></div></div><div class="xgb-c">{xh+xa:.1f} Total</div><div><span>{xa:.2f} xG</span><div class="track r"><i style="width:{xa/(xh+xa)*100:.0f}%"></i></div></div></div><div class="p123"><div style="flex:{p1:.0f}"><b>1</b> {p1:.0f}%</div><div style="flex:{px:.0f}" class="draw"><b>X</b> {px:.0f}%</div><div style="flex:{p2:.0f}" class="away"><b>2</b> {p2:.0f}%</div></div><div class="chips"><span class="chip">أفضل نتيجة: {best}</span><span class="chip">أفضل رهان: {best_bet}</span><span class="chip">Over {ov*100:.0f}% • BTTS {bt:.0f}%</span></div><button class="more" onclick="tog('d{idx}')">عرض تفاصيل الفريقين + Live ↓</button><div id="d{idx}" class="detail"><div class="tbox"><h4>{h} - Team 1</h4><p>آخر 5: {last5(h)}</p><ul>{sugg(h,True)}</ul></div><div class="tbox"><h4>{a} - Team 2</h4><p>آخر 5: {last5(a)}</p><ul>{sugg(a,False)}</ul></div><div class="livebox">LIVE - الدقيقة <input id="mi{idx}" type="number" value="65"> النتيجة <input id="hg{idx}" type="number" value="0"> - <input id="ag{idx}" type="number" value="0"> <button onclick="live({idx},{xh:.2f},{xa:.2f})">حساب Live</button><p id="lv{idx}"></p></div></div></article>"""
html=f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sigma V13 - Clean Global</title><style>*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial;background:#f2f4f7;color:#111}}header{{background:#fff;position:sticky;top:0;z-index:10;box-shadow:0 2px 12px rgba(0,0,0,.06);padding:14px 16px;display:flex;justify-content:space-between;align-items:center}}header h1{{margin:0;font-size:22px}}header h1 i{{color:#2563eb;font-style:normal}}header span{{background:#111;color:#fff;padding:6px 12px;border-radius:999px;font-size:13px}}.sub{{max-width:1100px;margin:0 auto;padding:14px 16px;color:#555}}.sub b{{color:#111}}.wrap{{max-width:1100px;margin:0 auto;padding:0 16px 30px}}.search input{{width:100%;padding:14px 16px;border:1px solid #e5e7eb;border-radius:14px;font-size:15px;background:#fff;outline:none}}.tabs{{display:flex;gap:8px;margin:14px 0}}.tabs button{{flex:1;padding:12px;border:none;border-radius:12px;background:#fff;cursor:pointer;font-weight:700}}.tabs button.on{{background:#111;color:#fff}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}}}.mcard{{background:#fff;border-radius:20px;box-shadow:0 4px 20px rgba(0,0,0,.06);overflow:hidden;animation:up .4s ease}}@keyframes up{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}.m-top{{display:flex;justify-content:space-between;padding:14px 16px 0;font-size:12px;color:#777}}.lg{{background:#eef2ff;color:#2563eb;padding:4px 8px;border-radius:999px;font-weight:700}}.m-teams{{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;gap:10px}}.tm{{flex:1;text-align:center;display:flex;flex-direction:column;align-items:center;gap:6px}}.tm b{{font-size:16px;line-height:1.2}}.av{{width:44px;height:44px;border-radius:50%;background:#111;color:#fff;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800}}.vs{{background:#f2f4f7;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;color:#777}}.form{{display:flex;gap:4px}}.dot{{width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:#fff}}.dot.W{{background:#16a34a}}.dot.D{{background:#ca8a04}}.dot.L{{background:#dc2626}}.xgb{{display:grid;grid-template-columns:1fr 70px 1fr;gap:8px;padding:0 16px;font-size:12px;color:#555}}.track{{height:8px;background:#eef2ff;border-radius:999px;overflow:hidden;margin-top:4px}}.track i{{display:block;height:100%;background:#2563eb}}.track.r i{{background:#f97316}}.xgb-c{{text-align:center;font-weight:800;color:#111;padding-top:14px}}.p123{{display:flex;margin:14px 16px 0;border-radius:12px;overflow:hidden}}.p123 div{{padding:10px;text-align:center;background:#2563eb;color:#fff;font-size:13px}}.p123 .draw{{background:#e5e7eb;color:#111}}.p123 .away{{background:#f97316}}.chips{{display:flex;flex-wrap:wrap;gap:8px;padding:14px 16px}}.chip{{background:#f8fafc;border:1px solid #e5e7eb;padding:7px 10px;border-radius:999px;font-size:13px}}.more{{width:100%;border:none;border-top:1px solid #eef2ff;background:#fff;padding:14px;cursor:pointer;font-weight:700;color:#2563eb}}.detail{{max-height:0;overflow:hidden;transition:max-height .5s ease;background:#f8fafc}}.detail.open{{max-height:700px}}.tbox{{padding:12px 16px;border-bottom:1px solid #eef2ff}}.tbox h4{{margin:6px 0}}.tbox ul{{margin:6px 0;padding-right:18px}}.tbox li{{margin:4px 0;font-size:14px}}.livebox{{padding:14px 16px}}.livebox input{{width:52px;padding:8px;border:1px solid #e5e7eb;border-radius:8px}}.livebox button{{background:#111;color:#fff;border:none;padding:9px 14px;border-radius:999px;cursor:pointer}}</style></head><body><header><h1>Sigma <i>•</i> V13</h1><span>Mahmoud Emad</span></header><div class="sub"><b>11/14 Verified 78.6%</b> • MEGA 51.7% • 29466 مباراة حقيقية • 248 فريق • كل فريق تحته نتائجه واقتراحاته</div><div class="wrap"><div class="search"><input id="q" oninput="filt()" placeholder="ابحث باسم فريق... 【entity-Ajax¦canonical_name=Ajax】 / Real / 【entity-Bayern¦canonical_name=Bayern】"></div><div class="tabs"><button class="on" onclick="tab('all',this)">كل المباريات</button><button onclick="tab('fav',this)">أفضل رهانات</button></div><div class="grid" id="grid">{cards}</div><p style="text-align:center;color:#777;margin-top:20px">1 = فوز صاحب الأرض Team 1 • X = تعادل • 2 = فوز الضيف Team 2 • Over 2.5 = 3 أهداف أو أكتر • BTTS = الفريقين يسجلوا<br>Signature Prediction and Forecast: Sigma - Mahmoud Emad</p></div><script>function tog(id){{let e=document.getElementById(id); e.classList.toggle('open')}} function filt(){{let q=document.getElementById('q').value.toLowerCase(); document.querySelectorAll('.mcard').forEach(c=>c.style.display=c.dataset.team.includes(q)?'block':'none')}} function tab(n,b){{document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on')); b.classList.add('on');}} function ps(l,k){{let f=1; for(let i=2;i<=k;i++) f*=i; return Math.exp(-l)*Math.pow(l,k)/f}} function live(i,xh,xa){{let mi=+document.getElementById('mi'+i).value, hg=+document.getElementById('hg'+i).value, ag=+document.getElementById('ag'+i).value; let rem=Math.max(0,90-mi)/90; let mh=hg<ag?1.15:hg>ag?0.95:1; let ma=ag<hg?1.15:ag>hg?0.95:1; let rxh=xh*rem*mh, rxa=xa*rem*ma; let ph=0,pd=0,pa=0,nh=0,na=0,ov=0; for(let rh=0;rh<6;rh++) for(let ra=0;ra<6;ra++){{let p=ps(rxh,rh)*ps(rxa,ra); let fh=hg+rh, fa=ag+ra; if(fh>fa) ph+=p; else if(fh==fa) pd+=p; else pa+=p; if(rh==1&&ra==0) nh+=p; if(rh==0&&ra==1) na+=p; if(fh+fa>=3) ov+=p;}} document.getElementById('lv'+i).innerHTML='متبقي xG '+rxh.toFixed(2)+'-'+rxa.toFixed(2)+' | 1X2 '+Math.round(ph*100)+'/'+Math.round(pd*100)+'/'+Math.round(pa*100)+' | الهدف الجاي H '+Math.round(nh*100)+'% A '+Math.round(na*100)+'% | Over Live '+Math.round(ov*100)+'%';}}</script></body></html>"""
open("index.html","w",encoding="utf-8").write(html)
print("V13 written")
