import csv, json, math, sys
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
 h1=get(hs,"home_scored"); c1=get(hs,"home_conceded")
 a1=get(as_,"away_scored"); c2=get(as_,"away_conceded")
 if h1==0: h1=get(hs,"scored_avg")
 if a1==0: a1=get(as_,"scored_avg")
 return max(.2,min(3.5,(h1+c2)/2*1.1)), max(.2,min(3.5,(a1+c1)/2))
try: st=json.load(open("data/sigma_team_stats.json",encoding="utf-8"))
except: st={}
if isinstance(st,list): st={x.get("team",str(i)):x for i,x in enumerate(st)}
def dna(tm,home):
 s=find(tm,st)
 if not s: return tm+" No history"
 sc=get(s,"home_scored") if home else get(s,"away_scored")
 co=get(s,"home_conceded") if home else get(s,"away_conceded")
 if sc==0: sc=get(s,"scored_avg")
 if co==0: co=get(s,"conceded_avg")
 b=get(s,"btts"); o=get(s,"over25")
 if b<=1.5: b*=100
 if o<=1.5: o*=100
 id="Elite" if sc>=2.5 and co<=1 else "Attack" if sc>=2.2 else "Defense" if co<=.9 else "Weak" if sc<1.2 else "Balanced"
 return f"{tm} {id} {sc:.2f}-{co:.2f} BTTS {b:.0f}% Over {o:.0f}%"
def top(xh,xa):
 sc=[]
 for h in range(6):
  for a in range(6): sc.append(((h,a),ps(xh,h)*ps(xa,a)))
 sc.sort(key=lambda x:x[1],reverse=True); return sc[:3]
if len(sys.argv)>=5:
 m=sys.argv[1]; mi=int(sys.argv[2]); hg=int(sys.argv[3]); ag=int(sys.argv[4]); h,a=m.split(" vs ")
 xh,xa=xg(h,a,st); rem=max(0,90-mi)/90; rxh=xh*rem*(1.15 if hg<ag else .95 if hg>ag else 1); rxa=xa*rem*(1.15 if ag<hg else .95 if ag>hg else 1)
 ph=pd=pa=nh=na=ov=0
 for rh in range(6):
  for ra in range(6):
   p=ps(rxh,rh)*ps(rxa,ra); fh,fa=hg+rh,ag+ra
   if fh>fa: ph+=p
   elif fh==fa: pd+=p
   else: pa+=p
   if rh==1 and ra==0: nh+=p
   if rh==0 and ra==1: na+=p
   if fh+fa>=3: ov+=p
 print(f"LIVE {mi}' {m} {hg}-{ag} Pre {xh:.2f}-{xa:.2f} Rem {rxh:.2f}-{rxa:.2f}"); print(f"1X2 1:{ph*100:.0f}% X:{pd*100:.0f}% 2:{pa*100:.0f}% Next H {nh*100:.0f}% A {na*100:.0f}% Over Live {ov*100:.0f}%")
else:
 pr=list(csv.DictReader(open("data/sigma_mega_predictions.csv",encoding="utf-8")))
 for r in pr[:6]:
  m=r.get("match",""); h,a=m.split(" vs ") if " vs " in m else ("","")
  xh,xa=xg(h,a,st); ov=1-(ps(xh+xa,0)+ps(xh+xa,1)+ps(xh+xa,2)); p1=get(r,"1"); px=get(r,"X"); p2=get(r,"2")
  if p1<=1.5: p1*=100; px*=100; p2*=100
  print("="*40); print(m); print("T1:",dna(h,True)); print("T2:",dna(a,False)); print(f"xG {xh:.2f}-{xa:.2f} Over {ov*100:.0f}% 1X2 {p1:.0f}/{px:.0f}/{p2:.0f}"); print("Top:",",".join([f"{hh}-{aa} {pp*100:.1f}%" for (hh,aa),pp in top(xh,xa)]))
