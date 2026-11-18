import json,urllib.request,os,sys
U=os.environ.get("SUPABASE_URL","").rstrip("/")
K=os.environ.get("SUPABASE_KEY","")
h=sys.argv[1] if len(sys.argv)>1 else "Germany"
a=sys.argv[2] if len(sys.argv)>2 else "Netherlands"
print("Predict:",h,"vs",a)
ALL=[]
off=0
while True:
 req=urllib.request.Request(f"{U}/rest/v1/sigma_matches?select=home,score,away&limit=1000&offset={off}",headers={"apikey":K,"Authorization":f"Bearer {K}"})
 with urllib.request.urlopen(req,timeout=30) as r:
  d=json.loads(r.read().decode())
 if not d: break
 ALL.extend(d)
 if len(d)<1000: break
 off+=1000
print("Analyzed:",len(ALL))
elo={};form={};games={}
def get(t):
 if t not in elo:
  elo[t]=1500;form[t]=[];games[t]=0
 return elo[t]
for row in ALL:
 H=row.get('home','');A=row.get('away','')
 s=(row.get('score') or '').replace(' ','')
 if '-' not in s: continue
 try: gh,ga=map(int,s.split('-'))
 except: continue
 eh=get(H);ea=get(A)
 ex=1/(1+10**((ea-(eh+30))/400))
 sh=1 if gh>ga else 0.5 if gh==ga else 0
 elo[H]=eh+20*(sh-ex)
 elo[A]=ea+20*((1-sh)-(1-ex))
 games[H]+=1;games[A]+=1
 form[H].append('W' if gh>ga else 'D' if gh==ga else 'L')
 form[A].append('W' if ga>gh else 'D' if ga==gh else 'L')
 if len(form[H])>5: form[H].pop(0)
 if len(form[A])>5: form[A].pop(0)
eh=elo.get(h,1500);ea=elo.get(a,1500)
ex=1/(1+10**((ea-(eh+30))/400))
hp=ex*0.76
ap=(1-ex)*0.76
print("---")
print(h,"Elo",round(eh),"Games",games.get(h,0),"Form",' '.join(form.get(h,[])))
print(a,"Elo",round(ea),"Games",games.get(a,0),"Form",' '.join(form.get(a,[])))
print("Home Win:",round(hp*100),"%")
print("Draw: 24%")
print("Away Win:",round(ap*100),"%")
print("Best:",h if hp>=ap else a)
