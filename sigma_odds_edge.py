import urllib.request, csv, math
from pathlib import Path
def poisson(lam,g): return (math.exp(-lam)*lam**g)/math.factorial(g)
url="https://www.football-data.co.uk/mmz4281/2425/E0.csv"
try:
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    txt=urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")
    rows=list(csv.DictReader(txt.splitlines()))
    edges=[]
    for r in rows:
        try:
            hg=int(r["FTHG"]); ag=int(r["FTAG"]); oh=float(r["B365H"]); od=float(r["B365D"]); oa=float(r["B365A"])
        except: continue
        hxg=1.55; axg=1.25
        hw=d=aw=0
        for x in range(6):
            for y in range(6):
                p=poisson(hxg,x)*poisson(axg,y)
                if x>y: hw+=p
                elif x==y: d+=p
                else: aw+=p
        tot=hw+d+aw; hw/=tot; d/=tot; aw/=tot
        for prob, odds, label in [(hw,oh,"1"),(d,od,"X"),(aw,oa,"2")]:
            edge=prob*odds-1
            if edge>0.05:
                edges.append({"match":f"{r['HomeTeam']} vs {r['AwayTeam']}","pick":label,"model_prob":round(prob*100,1),"odds":odds,"edge":round(edge*100,1)})
    print(f"Real odds checked: {len(rows)} matches - Value edges >5%: {len(edges)}")
    for e in edges[:10]: print(e)
    Path("data/sigma_edge.csv").write_text("match,pick,model_prob,odds,edge\n"+"\n".join([f"{e['match']},{e['pick']},{e['model_prob']},{e['odds']},{e['edge']}" for e in edges]), encoding="utf-8")
    print("Saved: data/sigma_edge.csv - Rule: Bet only if Edge >5%")
except Exception as e: print(f"Odds fetch error: {e}")
