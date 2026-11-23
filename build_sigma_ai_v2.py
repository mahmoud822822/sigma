# build_sigma_ai_v2.py - Sigma AI Full System
# Data -> Elo -> Llama(delta +-3) -> Validator(caps) -> Brier + Log
import json, os, sys, re, datetime, math, urllib.request

CAP_DC=86; CAP_1X2=75; CAP_1X2_UNKNOWN=52; RISK=13; MAX_DELTA=3.0

def clean(s):
    if not isinstance(s,str): return s
    s=re.sub(r"【entity-[^¦]*¦canonical_name=([^】]+)】", r"\1", s)
    s=re.sub(r"【entity-([^】¦]+)(¦[^】]*)?】", r"\1", s)
    return s.strip()

def elo_probs(elo_h, elo_a):
    diff=(elo_h+65-elo_a)/400
    p1=1/(1+10**(-diff))
    p1_pct=p1*100
    pX=max(18, 30-abs(elo_h-elo_a)/40)
    p2=max(5, 100-p1_pct-pX)
    return round(p1_pct,1), round(pX,1), round(p2,1)

def call_llama(home, away, league, date, p1, pX, p2, elo_h, elo_a):
    groq=os.environ.get("GROQ_API_KEY","").strip()
    if not groq: return 0.0, "no-key-elo-only"
    prompt=f"""You are Sigma analyst. Do NOT decide final probability.
Match {home} vs {away}, league {league}, date {date}, Elo p1={p1} pX={pX} p2={p2}, elo {elo_h} vs {elo_a}.
Return ONLY JSON: {{"delta": -2.0, "injuries_note": "short", "form_note": "short"}}
delta between -3 and +3. Small adjustment for injuries/form only."""
    payload=json.dumps({"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":prompt}],"temperature":0.2,"max_tokens":250}).encode()
    try:
        req=urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=payload, headers={"Authorization":f"Bearer {groq}","Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            out=json.loads(r.read().decode())
        txt=out["choices"][0]["message"]["content"]
        m=re.search(r"\{.*\}", txt, re.S)
        if m:
            j=json.loads(m.group(0))
            d=max(-MAX_DELTA, min(MAX_DELTA, float(j.get("delta",0))))
            note=f"{j.get('injuries_note','')} | {j.get('form_note','')}".strip()
            return d, note
    except Exception as e:
        print("Llama fail", home, e)
        return 0.0, f"llama-fail:{e}"
    return 0.0, ""

def validate(m, base, delta):
    conf=base+delta
    vals=[m.get("elo_home"), m.get("elo_away")]
    unknown=any(v is None or float(v)==0 or float(v)==1500 for v in vals if v is not None)
    market=str(m.get("market","") or "").upper()
    if unknown:
        conf=min(conf, CAP_1X2_UNKNOWN if "1X2" in market else CAP_DC)
    elif "1X2" in market:
        conf=min(conf, CAP_1X2)
    else:
        conf=min(conf, CAP_DC)
    if "dc_prob" in m:
        try:
            m["dc_prob_original"]=float(m["dc_prob"])
            m["dc_prob_capped"]=min(86, float(m["dc_prob"]))
            m["dc_prob"]=m["dc_prob_capped"]
        except: pass
    return round(conf,1)

def calc_brier(matches, results):
    # Brier = mean((prob - outcome)^2) - كل ما قل كل ما كان احسن
    # results: dict key -> result "1" or "X" or "2"
    vals=[]
    for m in matches:
        k=m.get("key")
        if k not in results: continue
        res=results[k]
        p1=m.get("p1",33)/100; pX=m.get("pX",33)/100; p2=m.get("p2",33)/100
        o1=1 if res=="1" else 0; oX=1 if res=="X" else 0; o2=1 if res=="2" else 0
        b=((p1-o1)**2 + (pX-oX)**2 + (p2-o2)**2)/3
        vals.append(b)
    if not vals: return None
    return round(sum(vals)/len(vals),4)

def backtest_delta(matches):
    # هل delta بتاع Llama كان بيحسن ولا بيبوظ؟ نجربه على الماتشات اللي خلصت
    # لو مفيش نتائج، ارجع 0
    return {"tested": 0, "note": "needs recent_results with outcomes"}

def fetch_espn(day, ymd):
    out=[]
    UA={"User-Agent":"Mozilla/5.0"}
    for lg in ["egy.1","eng.1","esp.1","ita.1","ger.1","fra.1","sau.1"]:
        url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard?dates={ymd}"
        try:
            req=urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=15) as r:
                data=json.loads(r.read().decode())
            for ev in data.get("events",[]) or []:
                comps=ev.get("competitions",[{}])[0].get("competitors",[])
                home=away=""
                for c in comps:
                    nm=clean(c.get("team",{}).get("displayName",""))
                    if c.get("homeAway")=="home": home=nm
                    elif c.get("homeAway")=="away": away=nm
                if home and away:
                    out.append({"home":home,"away":away,"date":day,"league":lg})
        except Exception as e:
            print("ESPN fail",lg,day,e)
            continue
    return out

def main():
    p="data/sigma_site.json"
    d=json.load(open(p, encoding="utf-8"))
    matches=d.get("matches",[])
    if not matches:
        print("REFUSE: matches==0")
        sys.exit(2)
    log={"run_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "added":0, "llama_used":0, "llama_skipped":0, "validator_capped":0, "errors":[]}
    seen=set((clean(str(m.get("home",""))).lower(), clean(str(m.get("away",""))).lower(), str(m.get("date",""))) for m in matches)
    today=datetime.date.today().isoformat()
    tomorrow=(datetime.date.today()+datetime.timedelta(days=1)).isoformat()
    for day, ymd in [(today, today.replace("-","")), (tomorrow, tomorrow.replace("-",""))]:
        for nm in fetch_espn(day, ymd):
            key=(nm["home"].lower(), nm["away"].lower(), nm["date"])
            if key in seen: continue
            elo_h, elo_a=1500,1500
            p1,pX,p2=elo_probs(elo_h, elo_a)
            base=52.0
            delta, note=call_llama(nm["home"], nm["away"], nm["league"], nm["date"], p1,pX,p2, elo_h, elo_a)
            if "no-key" in note or "llama-fail" in note:
                log["llama_skipped"]+=1
            else:
                log["llama_used"]+=1
            new={"key": f"{nm['date']}|{nm['home'].lower().replace(' ','-')}|{nm['away'].lower().replace(' ','-')}",
                 "date": nm["date"], "league": nm["league"], "league_name": nm["league"],
                 "home": nm["home"], "home_team": nm["home"], "away": nm["away"], "away_team": nm["away"],
                 "elo_home": elo_h, "elo_away": elo_a, "elo": elo_h,
                 "p1": p1, "pX": pX, "p2": p2,
                 "conf": 52.0, "confidence": 52.0, "prob": 52.0,
                 "pick": "1" if p1>=p2 else "2", "dc_pick": "1X" if p1>=p2 else "X2",
                 "dc_prob": 80.0, "dc_prob_capped": 80, "market": "DC", "status": "upcoming", "kickoff": "20:00",
                 "over25": 50.0, "btts": 45.0, "golden": False,
                 "reasons": [f"AI Agent: {note}"] if note else [], "h_logo": "", "a_logo": ""}
            final=validate(new, base, delta)
            if final < base+delta:
                log["validator_capped"]+=1
            new["conf"]=final; new["confidence"]=final; new["prob"]=final
            matches.append(new); seen.add(key); log["added"]+=1
            print("ADDED", nm["home"], "vs", nm["away"], "base", base, "delta", delta, "final", final)
    # Brier من النتائج القديمة لو موجودة
    results={}
    for r in d.get("recent_results",[]) or []:
        if r.get("key") and r.get("result"):
            results[r["key"]]=r["result"]
    brier=calc_brier(matches, results)
    if brier is not None:
        d["brier_score"]=brier
        print("Brier", brier)
    d["matches"]=matches; d["cap"]=86; d["risk"]=13
    d["generated_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    d["stats"]["upcoming"]=len(matches)
    json.dump(d, open(p,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    # Observability log - append
    try:
        logs=[]
        if os.path.exists("data/sigma_log.json"):
            logs=json.load(open("data/sigma_log.json", encoding="utf-8"))
        logs.append(log)
        logs=logs[-50:]  # اخر 50 تشغيل بس
        json.dump(logs, open("data/sigma_log.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    except Exception as e:
        print("log fail", e)
    print("saved", p, "matches", len(matches), "cap 86 risk 13", "log", log)

if __name__=="__main__":
    main()
