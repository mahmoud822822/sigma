import csv, math
def poisson(lam,k):
    return math.exp(-lam)*lam**k/math.factorial(k)
def golden(xh,xa,hw,d,aw):
    tot=xh+xa
    p05=1-poisson(tot,0)
    p15=1-poisson(tot,0)-poisson(tot,1)
    pU45=sum(poisson(tot,k) for k in range(5))
    cands=[("Over 0.5",p05),("1X",1-aw),("X2",1-hw),("12",1-d),("Over 1.5",p15),("Under 4.5",pU45)]
    lab,pr=max(cands, key=lambda x: x[1])
    return lab,pr,1/pr
rows=list(csv.DictReader(open("data/sigma_mega_conditions.csv", encoding="utf-8")))
out=[]
for r in rows:
    try:
        xh,xa=[float(x) for x in r["xG"].split("-")]
        hw=float(r["1"])/100; d=float(r["X"])/100; aw=float(r["2"])/100
    except: continue
    lab,pr,od=golden(xh,xa,hw,d,aw)
    r["Golden"]=f"{lab} {pr*100:.0f}%"; r["GoldenOdds"]=f"{od:.2f}"
    out.append(r)
with open("data/sigma_mega_golden.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print(f"Golden: {len(out)}")
