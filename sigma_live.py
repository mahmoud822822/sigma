import csv, os, json, math, urllib.request, pathlib, time, sys
TOKEN=os.environ.get("FOOTBALL_DATA_TOKEN","")
def pois(l,k): return math.exp(-l)*l**k/math.factorial(k) if l>0 else 1.0 if k==0 else 0
def live_prob(ch,ca,xh,xa,minute):
  rem=max(0,(90-minute)/90)
  xh_rem=xh*rem*1.05; xa_rem=xa*rem*1.05
  ph=[pois(xh_rem,k) for k in range(7)]; pa=[pois(xa_rem,k) for k in range(7)]
  p1=px=p2=0
  for i in range(7):
    for j in range(7):
      fh=ch+i; fa=ca+j; p=ph[i]*pa[j]
      if fh>fa: p1+=p
      elif fh==fa: px+=p
      else: p2+=p
  tot=p1+px+p2
  nxt_h=xh_rem/(xh_rem+xa_rem)*100 if xh_rem+xa_rem>0 else 50
  return round(p1/tot*100,1),round(px/tot*100,1),round(p2/tot*100,1),round(nxt_h,1),round(xh_rem,2),round(xa_rem,2)
pred={}
try:
 for r in csv.DictReader(open("data/sigma_mega_golden.csv", encoding="utf-8")):
  try: xh,xa=[float(x) for x in r.get("xG","0-0").split("-")]
  except: continue
  pred[r["match"]]=(xh,xa)
except: pass
print(f"Pre-match xG loaded: {len(pred)}")
def fetch_live():
  if not TOKEN: return []
  try:
    req=urllib.request.Request("https://api.football-data.org/v4/matches?status=LIVE", headers={"X-Auth-Token":TOKEN})
    data=json.loads(urllib.request.urlopen(req, timeout=15).read())
    return data.get("matches",[])
  except Exception as e:
    print(f"API fail: {e}"); return []
def main():
  matches=fetch_live(); out=[]
  for m in matches:
    h=m["homeTeam"]["name"]; a=m["awayTeam"]["name"]; key=f"{h} vs {a}"
    xh,xa=1.4,1.1
    for k,(vxh,vxa) in pred.items():
      if h[:5].lower() in k.lower() or a[:5].lower() in k.lower(): xh,xa=vxh,vxa; break
    minute=m.get("minute") or 0
    ch=m["score"]["fullTime"]["home"] or 0; ca=m["score"]["fullTime"]["away"] or 0
    p1,px,p2,nxt,xhr,xar=live_prob(ch,ca,xh,xa,minute)
    out.append({"match":key,"minute":minute,"score":f"{ch}-{ca}","Live1":p1,"LiveX":px,"Live2":p2,"NextGoal_H":nxt,"xG_Rem":f"{xhr}-{xar}","status":m.get("status","LIVE")})
    print(f"LIVE {minute}' {key} {ch}-{ca} -> 1:{p1}% X:{px}% 2:{p2}% NextGoal Home {nxt}%")
  pathlib.Path("data").mkdir(exist_ok=True)
  with open("data/sigma_live.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=["match","minute","score","Live1","LiveX","Live2","NextGoal_H","xG_Rem","status"]); w.writeheader(); w.writerows(out)
  print(f"Live saved: {len(out)} - No live now means break until 2026-11-20" if not out else f"Live: {len(out)}")
if __name__=="__main__":
  if "--loop" in sys.argv:
    while True: main(); print("Sleep 5 min..."); time.sleep(300)
  else: main()
