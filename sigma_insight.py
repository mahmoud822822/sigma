import csv, pathlib
def norm(s): return (s or "").lower().strip()
def same(a,b):
    a=norm(a); b=norm(b)
    return a==b or a in b or b in a or (a.split() and a.split()[0] in b)
def load_hist():
    p=pathlib.Path("data/sigma_history.csv")
    if not p.exists(): return []
    rows=list(csv.DictReader(open(p, encoding="utf-8")))
    out=[]
    for r in rows:
        h=r.get("home") or r.get("home_team") or ""
        a=r.get("away") or r.get("away_team") or ""
        try: hg=int(float(r.get("home_goals",0) or 0)); ag=int(float(r.get("away_goals",0) or 0))
        except: continue
        out.append({"date":r.get("date",""),"home":h,"away":a,"hg":hg,"ag":ag})
    return sorted(out, key=lambda x: x["date"], reverse=True)
HIST=load_hist()
print(f"Hist: {len(HIST)}")
def form(team,n=5):
    ms=[r for r in HIST if same(r["home"],team) or same(r["away"],team)][:n]
    s=""; sc=0; cc=0
    for r in ms:
        if same(r["home"],team): gf,ga=r["hg"],r["ag"]
        else: gf,ga=r["ag"],r["hg"]
        sc+=gf; cc+=ga; s+= "W" if gf>ga else "D" if gf==ga else "L"
    return s or "-----", sc, cc
def h2h(h,a,n=5):
    ms=[r for r in HIST if (same(r["home"],h) and same(r["away"],a)) or (same(r["home"],a) and same(r["away"],h))][:n]
    if not ms: return "No H2H"
    txt=""
    for r in ms: txt+=f"{r['home']} {r['hg']}-{r['ag']} {r['away']} ({r['date'][:10]}); "
    return txt
def main():
    rows=list(csv.DictReader(open("data/sigma_mega_golden.csv", encoding="utf-8")))
    out=[]
    for r in rows:
        try: h,a=r["match"].split(" vs ")
        except: continue
        fh,sh,ch=form(h); fa,sa,ca=form(a); hh=h2h(h,a)
        insight=f"{h} Form {fh} ({sh}-{ch}) | {a} Form {fa} ({sa}-{ca}) | H2H: {hh[:80]}"
        r["FormH"]=fh; r["FormA"]=fa; r["H2H"]=hh; r["Insight"]=insight
        out.append(r)
    with open("data/sigma_insight.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print(f"Insight: {len(out)}")
if __name__=="__main__": main()
