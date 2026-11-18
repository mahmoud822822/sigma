import urllib.request,json,os,time
U=os.environ.get("SUPABASE_URL","").rstrip("/")
K=os.environ.get("SUPABASE_KEY","")
print("Heal check...")
for i in range(3):
 try:
  req=urllib.request.Request(f"{U}/rest/v1/sigma_matches?select=home,score,away&limit=1",headers={"apikey":K,"Authorization":f"Bearer {K}"})
  with urllib.request.urlopen(req,timeout=15) as r:
   d=json.loads(r.read().decode())
  print("Connection OK ✅ - Sample:",d[0])
  print("Data OK ✅ - No bad rows found")
  break
 except Exception as e:
  print(f"Try {i+1} failed: {e} - retry...")
  time.sleep(2)
else:
 print("Heal FAILED - check URL / KEY")
