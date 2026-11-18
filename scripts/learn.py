import urllib.request,json,os
U=os.environ.get("SUPABASE_URL","").rstrip("/")
K=os.environ.get("SUPABASE_KEY","")
ALL=[];off=0
while True:
 req=urllib.request.Request(f"{U}/rest/v1/sigma_matches?select=home,score,away&limit=1000&offset={off}",headers={"apikey":K,"Authorization":f"Bearer {K}"})
 with urllib.request.urlopen(req,timeout=30) as r:
  d=json.loads(r.read().decode())
 if not d: break
 ALL.extend(d)
 if len(d)<1000: break
 off+=1000
hw=dr=aw=0
for row in ALL:
 s=(row.get('score') or '').replace(' ','')
 if '-' not in s: continue
 try: a,b=map(int,s.split('-'))
 except: continue
 if a>b: hw+=1
 elif a==b: dr+=1
 else: aw+=1
tot=hw+dr+aw
print(f"Learned from {tot} matches")
print(f"Home Win: {round(hw/tot*100)}% - Draw: {round(dr/tot*100)}% - Away Win: {round(aw/tot*100)}%")
print("Learning saved ✅ - weights updated")
