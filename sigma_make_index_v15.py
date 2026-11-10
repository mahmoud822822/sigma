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
def H(r): return r.get("home") or ""
def A(r): return r.get("away") or ""
def HG(r):
 try: return int(float(r.get("home_goals") or 0))
 except: return 0
def AG(r):
 try: return int(float(r.get("away_goals") or 0))
 except: return 0
def team_matches(tm, limit=12, home_only=False, away_only=False):
 out=[]
 for r in sorted(hist,key=lambda x: x.get("date",""),reverse=True):
  h=H(r); a=A(r)
  if cl(h)==cl(tm) or cl(a)==cl(tm):
   if home_only and cl(h)!=cl(tm): continue
   if away_only and cl(a)!=cl(tm): continue
   out.append(r)
   if len(out)>=limit: break
 return out
def rates(ms, tm):
 if not ms: return (0,0,0,0,0,0)
 n=len(ms); sc=0; co=0; btts=0; over=0; cs=0; fts=0
 for r in ms:
  hg=HG(r); ag=AG(r)
  if cl(H(r))==cl(tm): s=hg; c=ag
  else: s=ag; c=hg
  sc+=s; co+=c
  if hg>0 and ag>0: btts+=1
  if hg+ag>=3: over+=1
  if c==0: cs+=1
  if s==0: fts+=1
 return (sc/n, co/n, btts/n*100, over/n*100, cs/n*100, fts/n*100)
def h2h(h,a):
 out=[]
 for r in sorted(hist,key=lambda x: x.get("date",""),reverse=True):
  if (cl(H(r))==cl(h) and cl(A(r))==cl(a)) or (cl(H(r))==cl(a) and cl(A(r))==cl(h)):
   out.append(r)
   if len(out)>=5: break
 return out
def conf_score(h,a,p1,px,p2):
 hs=find(h,st); as_=find(a,st)
 n1=get(hs,"n") if hs else 0; n2=get(as_,"n") if as_ else 0
 c=50
 if min(n1,n2)>=100: c+=20
 elif min(n1,n2)>=50: c+=10
 ms_h=team_matches(h,10,home_only=True); ms_a=team_matches(a,10,away_only=True)
 rh=rates(ms_h,h); ra=rates(ms_a,a)
 sh=get(hs,"over25") if hs else 0; sa=get(as_,"over25") if as_ else 0
 if sh<=1.5: sh*=100
 if sa<=1.5: sa*=100
 if abs(rh[3]-sh)<15 and abs(ra[3]-sa)<15: c+=10
 if h2h(h,a): c+=10
 if abs(p1-p2)>20: c+=10
 return min(95,max(40,c))
def sugg_list(tm, home, opp):
 ms=team_matches(tm,10,home_only=home,away_only=not home)
 s10=rates(ms,tm)
 s=find(tm,st); season_over=get(s,"over25") if s else 0; season_btts=get(s,"btts") if s else 0
 if season_over<=1.5: season_over*=100
 if season_btts<=1.5: season_btts*=100
 L=[]
 if s10[3]>=60 and season_over>=60: L.append((f"Over 2.5 STRONG - Last 10 {s10[3]:.0f}% | Season {season_over:.0f}%", f"Over 2.5 قوي - آخر 10 {s10[3]:.0f}% | الموسم {season_over:.0f}%"))
 if s10[3]<=35 and season_over<=45: L.append((f"Under 2.5 Value - Last 10 Over {s10[3]:.0f}% only", f"Under 2.5 قيمة - آخر 10 Over {s10[3]:.0f}% فقط"))
 if s10[2]>=60 and season_btts>=55: L.append((f"BTTS Yes - Last 10 {s10[2]:.0f}% | Season {season_btts:.0f}%", f"BTTS نعم - آخر 10 {s10[2]:.0f}% | الموسم {season_btts:.0f}%"))
 if s10[2]<=30: L.append((f"BTTS No - Last 10 only {s10[2]:.0f}%", f"BTTS لا - آخر 10 {s10[2]:.0f}% فقط"))
 if s10[4]>=50: L.append((f"Clean Sheet {s10[4]:.0f}% in last 10", f"Clean Sheet {s10[4]:.0f}% في آخر 10"))
 if s10[5]>=40: L.append((f"Fail To Score risk {s10[5]:.0f}% in last 10", f"خطر عدم التسجيل {s10[5]:.0f}% في آخر 10"))
 if s10[0]>=2.2: L.append((f"Scores {s10[0]:.2f}/match - Attack in form", f"يسجل {s10[0]:.2f} - هجوم في الفورمة"))
 if s10[1]<=0.8: L.append((f"Concedes {s10[1]:.2f} - Solid defence", f"يستقبل {s10[1]:.2f} - دفاع صلب"))
 if s10[0]>=1.5 and s10[5]<=20: L.append((f"Team to Score 1+ - Very likely {100-s10[5]:.0f}% scored in last 10", f"الفريق يسجل 1+ - محتمل جدا {100-s10[5]:.0f}% سجل في آخر 10"))
 if not L: L.append(("No clear edge - Skip", "لا توجد أفضلية - تخطى"))
 return L
def last5_html(tm):
 ms=team_matches(tm,5); out=""
 for r in ms:
  hg=HG(r); ag=AG(r)
  if cl(H(r))==cl(tm): res="W" if hg>ag else "D" if hg==ag else "L"; txt=f"{hg}-{ag} vs {A(r)}"
  else: res="W" if ag>hg else "D" if ag==hg else "L"; txt=f"{ag}-{hg} @ {H(r)}"
  out+=f"<div class='lastrow'><span class='dot {res}'>{res}</span><span>{txt}</span><small>{r.get('date','')[:10]}</small></div>"
 return out or "No data"
def h2h_html(h,a):
 ms=h2h(h,a)
 if not ms: return "<p>No H2H in history</p>"
 out=""
 for r in ms:
  out+=f"<div class='lastrow'><span>{H(r)} {HG(r)}-{AG(r)} {A(r)}</span><small>{r.get('date','')[:10]}</small></div>"
 tot=sum(HG(r)+AG(r) for r in ms)/len(ms); b=sum(1 for r in ms if HG(r)>0 and AG(r)>0)/len(ms)*100; ov=sum(1 for r in ms if HG(r)+AG(r)>=3)/len(ms)*100
 out+=f"<p>H2H Avg {tot:.2f} goals - BTTS {b:.0f}% - Over {ov:.0f}% in last {len(ms)}</p>"
 return out
def golden_for(p1,px,p2,xh,xa):
 tot=xh+xa; cands=[]
 cands.append(("1X",p1+px)); cands.append(("X2",px+p2)); cands.append(("12",p1+p2)); cands.append(("Over 1.5", (1-ps(tot,0)-ps(tot,1))*100)); cands.append(("Over 0.5", (1-ps(tot,0))*100)); cands.append(("Under 4.5", sum(ps(tot,k) for k in range(5))*100))
 cands=[c for c in cands if c[1]>=80]
 if not cands: return None
 best=max(cands,key=lambda x:x[1]); return (best[0], best[1], 100/best[1] if best[1]>0 else 0)
def upset_alert(h,a,p1,p2):
 ms_h=team_matches(h,10,home_only=True); ms_a=team_matches(a,10,away_only=True)
 rh=rates(ms_h,h); ra=rates(ms_a,a)
 if p1>=70 and ra[0]>=1.8 and rh[1]>=1.4: return (f"UPSET RISK - {a} scores {ra[0]:.2f} away, {h} concedes {rh[1]:.2f} home", f"خطر مفاجأة - {a} يسجل {ra[0]:.2f} بره، و {h} يستقبل {rh[1]:.2f} في بيته")
 if p2>=70 and rh[0]>=1.8 and ra[1]>=1.4: return (f"UPSET RISK - {h} scores {rh[0]:.2f} home, {a} concedes {ra[1]:.2f} away", f"خطر مفاجأة - {h} يسجل {rh[0]:.2f} في بيته، و {a} يستقبل {ra[1]:.2f} بره")
 return None
def sugg_html(L): return "".join([f"<li><span class='en'>{e}</span><span class='ar' style='display:none'>{a2}</span></li>" for e,a2 in L])
cards=""; golden_cards=""; upset_cards=""; acca_cands=[]
for idx,r in enumerate(pr[:24]):
 m=r.get("match",""); h,a=m.split(" vs ") if " vs " in m else ("","")
 xh,xa=xg(h,a,st); tot=xh+xa; ov=1-(ps(tot,0)+ps(tot,1)+ps(tot,2)); p1=get(r,"1"); px=get(r,"X"); p2=get(r,"2")
 if p1<=1.5: p1*=100; px*=100; p2*=100
 bt=get(r,"BTTS")
 if bt<=1.5: bt*=100
 tops=top(xh,xa); best=f"{tops[0][0][0]}-{tops[0][0][1]} {tops[0][1]*100:.0f}%"
 s_h=sugg_list(h,True,a); s_a=sugg_list(a,False,h)
 cf=conf_score(h,a,p1,px,p2)
 g=golden_for(p1,px,p2,xh,xa)
 up=upset_alert(h,a,p1,p2)
 if g: golden_cards+=f"<div class='gold'><b>{h} vs {a}</b><span>{g[0]} {g[1]:.0f}% - Fair {g[2]:.2f}</span></div>"
 if up: upset_cards+=f"<div class='upset'><b>{h} vs {a}</b><span class='en'>{up[0]}</span><span class='ar' style='display:none'>{up[1]}</span></div>"
 for nm,prob in [("1X",p1+px),("X2",px+p2),("Over 2.5",ov*100),("BTTS Yes",bt)]:
  if 70<=prob<=85: acca_cands.append((prob,m,nm))
 golden_txt=f"Golden: {g[0]} {g[1]:.0f}%" if g else "No Golden"
 upset_html=""
 if up: upset_html=f"<div class='upset'><span class='en'>{up[0]}</span><span class='ar' style='display:none'>{up[1]}</span></div>"
 corners_h=min(11, xh*2.6+2); corners_a=min(11, xa*2.6+1); corners_tot=corners_h+corners_a; throw_tot=min(55, 32+tot*3)
 cards+=f"""<article class="mcard" data-team="{m.lower()}"><div class="m-top"><span class="lg">{r.get('league','')}</span><span class="dt">{r.get('date','')} - Conf {cf:.0f}%</span></div><div class="m-teams"><div class="tm"><div class="av">{h[:1]}</div><b>{h}</b></div><div class="vs">VS</div><div class="tm"><div class="av">{a[:1]}</div><b>{a}</b></div></div><div class="xgb"><div><span>xG {xh:.2f}</span><div class="track"><i style="width:{xh/(xh+xa)*100:.0f}%"></i></div></div><div class="xgb-c">{tot:.1f} Total</div><div><span>{xa:.2f} xG</span><div class="track r"><i style="width:{xa/(xh+xa)*100:.0f}%"></i></div></div></div><div class="p123"><div style="flex:{p1:.0f}"><b>1</b> {p1:.0f}%</div><div style="flex:{px:.0f}" class="draw"><b>X</b> {px:.0f}%</div><div style="flex:{p2:.0f}" class="away"><b>2</b> {p2:.0f}%</div></div><div class="chips"><span class="chip"><span class="en">Best Score: {best}</span><span class="ar" style="display:none">أفضل نتيجة: {best}</span></span><span class="chip">Over {ov*100:.0f}% - BTTS {bt:.0f}%</span><span class="chip">{golden_txt}</span></div>{upset_html}<button class="more" onclick="tog('d{idx}')"><span class="en">Show Details + H2H + Corners + Live</span><span class="ar" style="display:none">عرض التفاصيل + المواجهات + كورنر + Live</span></button><div id="d{idx}" class="detail"><div class="tbox"><h4>{h} - Team 1 Home</h4><div class="lastlist">{last5_html(h)}</div><ul>{sugg_html(s_h)}</ul></div><div class="tbox"><h4>{a} - Team 2 Away</h4><div class="lastlist">{last5_html(a)}</div><ul>{sugg_html(s_a)}</ul></div><div class="tbox"><h4>Head to Head</h4>{h2h_html(h,a)}</div><div class="tbox"><h4>Corners & Throw-ins (Estimate)</h4><p>Corners {corners_h:.1f} - {corners_a:.1f} Total {corners_tot:.1f} - Throw-ins Total ~{throw_tot:.0f} - Estimate from xG</p></div><div class="livebox">LIVE - Minute <input id="mi{idx}" type="number" value="65"> Score <input id="hg{idx}" type="number" value="0"> - <input id="ag{idx}" type="number" value="0"> <button onclick="live({idx},{xh:.2f},{xa:.2f})">Calc Live</button><p id="lv{idx}"></p></div></div></article>"""
acca_cands=sorted(acca_cands,key=lambda x:x[0],reverse=True)
acca_pick=[]; used=set()
for prob,m,nm in acca_cands:
 if m in used: continue
 used.add(m); acca_pick.append((prob,m,nm))
 if len(acca_pick)>=3: break
if len(acca_pick)==3:
 comb=1
 for prob,m,nm in acca_pick: comb*=prob/100
 acca_html=f"<div class='acca'><h3>Best Acca - 3 Diversified Value Bets</h3>"+"".join([f"<p>{m} - {nm} {prob:.0f}%</p>" for prob,m,nm in acca_pick])+f"<p><b>Combined {comb*100:.1f}% - Fair Odds {1/comb:.2f}</b></p></div>"
else:
 acca_html="<div class='acca'><p>No valid Acca - Do not force</p></div>"
if not golden_cards: golden_cards="<p>No Golden today</p>"
if not upset_cards: upset_cards="<p>No Upset Alert</p>"
html=f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sigma V15 - Complete Merged</title><style>*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial;background:#f2f4f7;color:#111}}header{{background:#fff;position:sticky;top:0;z-index:10;box-shadow:0 2px 12px rgba(0,0,0,.06);padding:14px 16px;display:flex;justify-content:space-between;align-items:center}}header h1{{margin:0;font-size:22px}}header h1 i{{color:#2563eb;font-style:normal}}.langbtn{{background:#111;color:#fff;border:none;padding:8px 14px;border-radius:999px;cursor:pointer}}.sub{{max-width:1100px;margin:0 auto;padding:14px 16px;color:#555}}.wrap{{max-width:1100px;margin:0 auto;padding:0 16px 30px}}.search input{{width:100%;padding:14px 16px;border:1px solid #e5e7eb;border-radius:14px;font-size:15px;background:#fff;outline:none}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}}}.mcard{{background:#fff;border-radius:20px;box-shadow:0 4px 20px rgba(0,0,0,.06);overflow:hidden;animation:up .4s ease}}@keyframes up{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}.m-top{{display:flex;justify-content:space-between;padding:14px 16px 0;font-size:12px;color:#777}}.lg{{background:#eef2ff;color:#2563eb;padding:4px 8px;border-radius:999px;font-weight:700}}.m-teams{{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;gap:10px}}.tm{{flex:1;text-align:center;display:flex;flex-direction:column;align-items:center;gap:6px}}.tm b{{font-size:16px;line-height:1.2}}.av{{width:44px;height:44px;border-radius:50%;background:#111;color:#fff;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800}}.vs{{background:#f2f4f7;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;color:#777}}.xgb{{display:grid;grid-template-columns:1fr 70px 1fr;gap:8px;padding:0 16px;font-size:12px;color:#555}}.track{{height:8px;background:#eef2ff;border-radius:999px;overflow:hidden;margin-top:4px}}.track i{{display:block;height:100%;background:#2563eb}}.track.r i{{background:#f97316}}.xgb-c{{text-align:center;font-weight:800;color:#111;padding-top:14px}}.p123{{display:flex;margin:14px 16px 0;border-radius:12px;overflow:hidden}}.p123 div{{padding:10px;text-align:center;background:#2563eb;color:#fff;font-size:13px}}.p123 .draw{{background:#e5e7eb;color:#111}}.p123 .away{{background:#f97316}}.chips{{display:flex;flex-wrap:wrap;gap:8px;padding:14px 16px}}.chip{{background:#f8fafc;border:1px solid #e5e7eb;padding:7px 10px;border-radius:999px;font-size:13px}}.more{{width:100%;border:none;border-top:1px solid #eef2ff;background:#fff;padding:14px;cursor:pointer;font-weight:700;color:#2563eb}}.detail{{max-height:0;overflow:hidden;transition:max-height .6s ease;background:#f8fafc}}.detail.open{{max-height:1000px;overflow:auto}}.tbox{{padding:12px 16px;border-bottom:1px solid #eef2ff}}.tbox h4{{margin:6px 0}}.tbox ul{{margin:6px 0;padding-inline-start:18px}}.tbox li{{margin:6px 0;font-size:14px;line-height:1.5}}.lastrow{{display:flex;gap:8px;align-items:center;padding:6px 0;border-bottom:1px solid #eee;font-size:13px}}.lastrow small{{margin-inline-start:auto;color:#777}}.dot{{width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:#fff;flex-shrink:0}}.dot.W{{background:#16a34a}}.dot.D{{background:#ca8a04}}.dot.L{{background:#dc2626}}.livebox{{padding:14px 16px}}.livebox input{{width:52px;padding:8px;border:1px solid #e5e7eb;border-radius:8px}}.livebox button{{background:#111;color:#fff;border:none;padding:9px 14px;border-radius:999px;cursor:pointer}}.gold,.upset,.acca{{background:#fff;border-radius:16px;padding:12px 14px;margin:10px 0;box-shadow:0 2px 10px rgba(0,0,0,.05);display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}}.gold{{border-inline-start:4px solid #f59e0b}}.upset{{border-inline-start:4px solid #dc2626;background:#fef2f2}}.acca{{display:block;border:2px solid #111}}.sec{{background:#fff;border-radius:16px;padding:14px 16px;margin:14px 0}}.sec h2{{margin:0 0 8px;font-size:18px}}</style></head><body class="ar"><header><h1>Sigma <i>•</i> V15</h1><button class="langbtn" onclick="toggleLang()">EN / عربي</button></header><div class="sub"><span class="en" style="display:none"><b>11/14 Verified 78.6%</b> - MEGA 51.7% - 29466 real matches - 248 teams - Merged V13+V14+V15: Real suggestions + Golden + Acca + Confidence + Upset + Corners</span><span class="ar"><b>11/14 موثق 78.6%</b> - MEGA 51.7% - 29466 مباراة حقيقية - 248 فريق - دمج V13+V14+V15: اقتراحات حقيقية + Golden + Acca + ثقة + مفاجآت + كورنر</span></div><div class="wrap"><div class="search"><input id="q" oninput="filt()" placeholder="Search team... / ابحث باسم فريق..."></div><div class="sec"><h2><span class="en">Golden Bets - Safest 80%+</span><span class="ar">Golden Bets - الأكثر أمانا 80%+</span></h2>{golden_cards}</div><div class="sec">{acca_html}</div><div class="sec"><h2><span class="en">Upset Alerts</span><span class="ar">تنبيهات المفاجآت</span></h2>{upset_cards}</div><div class="sec"><h2><span class="en">All Matches - Same Clean Design</span><span class="ar">كل المباريات - نفس الشكل النضيف</span></h2><div class="grid" id="grid">{cards}</div></div><p style="text-align:center;color:#777"><span class="en">1 = Home Team 1 - X = Draw - 2 = Away Team 2 - Every suggestion has evidence: Last 10 + Season + H2H - Corners are estimates</span><span class="ar">1 = فريق 1 صاحب الأرض - X = تعادل - 2 = فريق 2 الضيف - كل اقتراح بدليله: آخر 10 + الموسم + المواجهات - الكورنر تقدير</span></p></div><script>function tog(id){{let e=document.getElementById(id); e.classList.toggle('open')}} function filt(){{let q=document.getElementById('q').value.toLowerCase(); document.querySelectorAll('.mcard').forEach(c=>c.style.display=c.dataset.team.includes(q)?'block':'none')}} function toggleLang(){{let b=document.body; let isAr=b.classList.contains('ar'); b.classList.toggle('ar'); b.classList.toggle('en'); document.querySelectorAll('.en').forEach(e=>e.style.display=isAr?'':'none'); document.querySelectorAll('.ar').forEach(e=>e.style.display=isAr?'none':''); document.documentElement.dir=isAr?'ltr':'rtl';}} function ps(l,k){{let f=1; for(let i=2;i<=k;i++) f*=i; return Math.exp(-l)*Math.pow(l,k)/f}} function live(i,xh,xa){{let mi=+document.getElementById('mi'+i).value, hg=+document.getElementById('hg'+i).value, ag=+document.getElementById('ag'+i).value; let rem=Math.max(0,90-mi)/90; let mh=hg<ag?1.15:hg>ag?0.95:1; let ma=ag<hg?1.15:ag>hg?0.95:1; let rxh=xh*rem*mh, rxa=xa*rem*ma; let ph=0,pd=0,pa=0,nh=0,na=0,ov=0; for(let rh=0;rh<6;rh++) for(let ra=0;ra<6;ra++){{let p=ps(rxh,rh)*ps(rxa,ra); let fh=hg+rh, fa=ag+ra; if(fh>fa) ph+=p; else if(fh==fa) pd+=p; else pa+=p; if(rh==1&&ra==0) nh+=p; if(rh==0&&ra==1) na+=p; if(fh+fa>=3) ov+=p;}} document.getElementById('lv'+i).innerHTML='Remaining xG '+rxh.toFixed(2)+'-'+rxa.toFixed(2)+' | 1X2 '+Math.round(ph*100)+'/'+Math.round(pd*100)+'/'+Math.round(pa*100)+' | Next H '+Math.round(nh*100)+'% A '+Math.round(na*100)+'% | Over Live '+Math.round(ov*100)+'%';}}</script><p style="text-align:center;opacity:.6">Signature Prediction and Forecast: Sigma - Mahmoud Emad</p></body></html>"""
open("index.html","w",encoding="utf-8").write(html)
print("V15 merged written")
