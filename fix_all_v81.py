import re

p = "sigma_engine.py"
s = open(p).read()
s = re.sub(r'VERSION\s*=\s*"[^"]+"', 'VERSION = "V81-PRO"', s)

# Unified Poisson + Elo + Real Intel calculator
core_fn = '''def calc_poisson(lh, la, rho=-0.07):
    p1=px=p2=bt=ov=tot=0.0; sc=[]
    for i in range(8):
        for j in range(8):
            pr=pmf(i,lh)*pmf(j,la)
            if i==0 and j==0: pr*=max(0.1,1.0-lh*la*rho)
            elif i==1 and j==0: pr*=max(0.1,1.0+la*rho)
            elif i==0 and j==1: pr*=max(0.1,1.0+lh*rho)
            elif i==1 and j==1: pr*=max(0.1,1.0-rho)
            tot+=pr
            if i>j: p1+=pr
            elif i==j: px+=pr
            else: p2+=pr
            if i>0 and j>0: bt+=pr
            if i+j>2: ov+=pr
            sc.append((pr,f"{i}-{j}"))
    p1,px,p2=round(100*p1/tot,1),round(100*px/tot,1),round(100*p2/tot,1)
    ov25=round(100*ov/tot,1); btts=round(100*bt/tot,1)
    bp,pk=max((p1,"1"),(px,"X"),(p2,"2")); cf=min(78.0,bp); sc.sort(reverse=True)
    return p1,px,p2,ov25,btts,bp,pk,cf,[x[1] for x in sc[:3]]

def pred(h,a,R,w):
    diff=(R["elo"].get(h,1500)+35.0)-R["elo"].get(a,1500)
    ef=math.exp(max(-0.85,min(0.85,diff*0.00135)))
    att_h,dfn_h=R["att"].get(h,1.32),R["dfn"].get(h,1.32)
    att_a,dfn_a=R["att"].get(a,1.25),R["dfn"].get(a,1.32)
    lh=max(0.45,min(3.1,((att_h+dfn_a)/2.05)*ef))
    la=max(0.40,min(2.8,((att_a+dfn_h)/2.05)/ef))
    p1,px,p2,ov25,btts,bp,pk,cf,top_sc=calc_poisson(lh,la,w.get("rho",-0.07))
    qu="full" if (h in R["elo"] or a in R["elo"]) else "prior"
    is_gold=(cf>=57.0) or (ov25>=62.0 and cf>=50.0)
    return {"p1":p1,"pX":px,"p2":p2,"conf":cf,"btts":btts,"over25":ov25,"xg_home":round(lh,2),"xg_away":round(la,2),"elo_home":round(R["elo"].get(h,1500)),"elo_away":round(R["elo"].get(a,1500)),"pick":pk,"grade":"A+" if cf>=66 else "A" if cf>=57 else "B" if cf>=48 else "C","quality":qu,"golden":is_gold,"top_scores":top_sc}
'''

# Replace old pred() cleanly
s_start = s.find("def pred(h,a,R,w):")
s_end = s.find("def fetch(t):")
assert s_start != -1 and s_end != -1
s = s[:s_start] + core_fn + "\n" + s[s_end:]

# Ensure enrich recalculates probabilities from adjusted xG so xG and Win% NEVER contradict
old_adj = '''            pr["xg_home"] = round(pr["xg_home"] * adj_h, 2)
            pr["xg_away"] = round(pr["xg_away"] * adj_a, 2)'''
new_adj = '''            lh_n = max(0.40, min(3.2, pr["xg_home"] * adj_h))
            la_n = max(0.35, min(2.9, pr["xg_away"] * adj_a))
            p1,px,p2,ov25,btts,bp,pk,cf,top_sc = calc_poisson(lh_n, la_n)
            pr.update({"xg_home":round(lh_n,2),"xg_away":round(la_n,2),"p1":p1,"pX":px,"p2":p2,"over25":ov25,"btts":btts,"pick":pk,"conf":cf,"top_scores":top_sc,"golden":(cf>=57.0) or (ov25>=62.0 and cf>=50.0)})'''
if old_adj in s:
    s = s.replace(old_adj, new_adj)

open(p, "w").write(s)

# Upgrade index.html with clear Home/Away badges & explicit pick banner
h = open("index.html").read()
h = h.replace("SIGMA AI V75", "SIGMA AI V81 PRO")
h = h.replace("<span>${m.home}</span>", "<span>🏟️ ${m.home}</span>")
h = h.replace("<span>${m.away}</span>", "<span>✈️ ${m.away}</span>")
h = h.replace(
    '<div class="probs">',
    '<div style="text-align:center;font-size:.78rem;color:#10b981;font-weight:700;margin-bottom:6px">🎯 الترشيح: ${m.pick==="1"?"فوز "+m.home:m.pick==="2"?"فوز "+m.away:"تعادل"} (${m.conf}%)</div><div class="probs">'
)
open("index.html", "w").write(h)
print("V81 PRO UNIFIED & CALIBRATED OK")
