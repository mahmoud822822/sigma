# Signature Prediction and Forecast: Sigma - Mahmoud Emad
import math, re, json, os, csv
def poisson(lam,g):
    return (math.exp(-lam)*lam**g)/math.factorial(g)
def get_num(prompt, default):
    s = input(prompt).strip()
    if not s:
        return default
    m = re.search(r"\d+\.\d+|\d+", s)
    if not m:
        return default
    try:
        v = float(m.group(0))
        return v if 0 < v <= 8 else default
    except:
        return default
def pred(h,a, show=True):
    m={}; t=0.0
    for x in range(11):
        for y in range(11):
            p=poisson(h,x)*poisson(a,y)
            m[(x,y)]=p
            t+=p
    m={k:v/t for k,v in m.items()}
    hw=sum(p for (x,y),p in m.items() if x>y)
    d=sum(p for (x,y),p in m.items() if x==y)
    aw=sum(p for (x,y),p in m.items() if x<y)
    if show:
        print(f"1: {hw*100:.1f}%  X: {d*100:.1f}%  2: {aw*100:.1f}%")
        top=sorted(m.items(), key=lambda z:z[1], reverse=True)[:3]
        print("Top:", ", ".join([f"{x}-{y} {p*100:.1f}%" for (x,y),p in top]))
    return hw,d,aw,m
def match_list():
    p1="data/sigma_next_month.json"
    p2="sigma_next_month.json"
    path = p1 if os.path.exists(p1) else p2 if os.path.exists(p2) else None
    if not path:
        print("No file: data/sigma_next_month.json")
        return
    try:
        with open(path, encoding="utf-8") as f:
            data=json.load(f)
        items = data if isinstance(data, list) else data.get("matches", data.get("data", []))
        print(f"Matches: {len(items)}")
        for i,mm in enumerate(items[:20],1):
            date = str(mm.get("date", mm.get("utcDate","")))[:10]
            if "match" in mm and isinstance(mm["match"], str) and " vs " in mm["match"]:
                print(f"{i}. {date} {mm['match']}  [{mm.get('league','')}]")
                continue
            home = mm.get("homeTeam", mm.get("home","?"))
            away = mm.get("awayTeam", mm.get("away","?"))
            if isinstance(home, dict): home=home.get("name", "?")
            if isinstance(away, dict): away=away.get("name", "?")
            print(f"{i}. {date} {home} vs {away}")
        if len(items)>20:
            print(f"... +{len(items)-20} more")
    except Exception as e:
        print("Error:", e)
def evaluation():
    path = None
    for cand in ["data/sigma_real_verified.csv", "sigma_real_verified.csv"]:
        if os.path.exists(cand):
            path = cand
            break
    if not path:
        print("No verified file")
        return
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    hit=0; exact=0; mae=0.0; n=0
    for r in rows:
        try:
            ph=int(r["predicted_home"]); pa=int(r["predicted_away"])
            rh=int(r["real_home"]); ra=int(r["real_away"])
        except:
            continue
        n+=1
        pick = "1" if ph>pa else "X" if ph==pa else "2"
        real = "1" if rh>ra else "X" if rh==ra else "2"
        if pick==real: hit+=1
        if ph==rh and pa==ra: exact+=1
        mae+=abs((ph+pa)-(rh+ra))
    print(f"Evaluation - {n} matches - {path}")
    print(f"Hit: {hit}/{n} = {hit/n*100:.1f}%")
    print(f"Exact: {exact}/{n} = {exact/n*100:.1f}%")
    print(f"MAE goals: {mae/n:.2f}")
def do_fetch():
    import subprocess, sys, os
    if os.path.exists("sigma_auto_fetch.py"):
        print("Running sigma_auto_fetch.py ...")
        r = subprocess.run([sys.executable, "sigma_auto_fetch.py"])
        print(f"Fetch exit: {r.returncode}")
        return
    print("No file: sigma_auto_fetch.py")
while True:
    print("\n1. Predict  2. Match list  3. Evaluation  4. Fetch  0. Exit")
    c=input("Choose: ").strip()
    if c=="0":
        break
    if c=="1":
        h=get_num("Home xG: ", 1.78)
        a=get_num("Away xG: ", 1.35)
        print(f"Using: {h} - {a}")
        pred(h,a)
    elif c=="2":
        match_list()
    elif c=="3":
        evaluation()
    elif c=="4":
        do_fetch()
