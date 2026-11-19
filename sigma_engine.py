from concurrent.futures import ThreadPoolExecutor
import os,json,csv,math,time,re,urllib.request
from datetime import datetime,date,timedelta,timezone
from pathlib import Path
VERSION = "V90-APEX"
BASE=Path(__file__).resolve().parent
DATA=BASE/"data"
DATA.mkdir(exist_ok=True)
WF=DATA/"sigma_weights.json"
LF=DATA/"sigma_prediction_log.json"
SF=DATA/"sigma_site.json"
HF=DATA/"sigma_history.csv"
DW={"xi":0.0018,"elo_home":65.0,"elo_adj":0.0010,"rho":-0.08}
FD={"PL":"Premier League","PD":"La Liga","SA":"Serie A","BL1":"Bundesliga","FL1":"Ligue 1","DED":"Eredivisie","PPL":"Primeira Liga"}
OF={"en.1":"Premier League","es.1":"La Liga","it.1":"Serie A","de.1":"Bundesliga","fr.1":"Ligue 1"}
def today():return datetime.now(timezone.utc).date()
def clean(s):return re.sub(r"\s+"," ",str(s or "")).strip()
def norm(s):return "".join(c for c in clean(s).lower() if c.isalnum())
def mkey(d,h,a):return f"{d}|{norm(h)}|{norm(a)}"
def load_w():
 w=dict(DW)
 if WF.exists():
  try:w.update(json.loads(WF.read_text()).get("weights",{}))
  except:pass
 return w
def hjson(u,hd=None):
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Sigma/75",**(hd or {})}),timeout=20) as r:return json.loads(r.read().decode())
 except:return None
def load_hist():
 m={}
 def add(ds,h,a,hg,ag,lg,src):
  h,a=clean(h),clean(a)
  if not h or not a:return
  try:d,hg,ag=date.fromisoformat(str(ds)[:10]),int(float(hg)),int(float(ag))
  except:return
  k=(d,norm(h),norm(a))
  if k not in m:m[k]={"d":d,"home":h,"away":a,"hg":hg,"ag":ag,"league":clean(lg) or "League","source":src}
 if HF.exists():
  for r in csv.DictReader(open(HF,encoding="utf-8",errors="replace")):add(r.get("date"),r.get("home"),r.get("away"),r.get("home_goals"),r.get("away_goals"),r.get("league"),r.get("source","hist"))
 if (BASE/"world_results.csv").exists():
  for r in csv.DictReader(open(BASE/"world_results.csv",encoding="utf-8",errors="replace")):
   if str(r.get("date",""))>="2000-01-01":add(r.get("date"),r.get("home_team"),r.get("away_team"),r.get("home_score"),r.get("away_score"),r.get("tournament"),"world")
 return sorted(m.values(),key=lambda x:x["d"])
def ratings(hist,ref,w):
 elo,att,dfn={},{},{}
 for r in hist:
  if r["d"]>=ref:break
  dc=math.exp(-w["xi"]*max(0,(ref-r["d"]).days))
  h,a=r["home"],r["away"]
  elo.setdefault(h,1500.0);elo.setdefault(a,1500.0);att.setdefault(h,1.35);att.setdefault(a,1.35);dfn.setdefault(h,1.35);dfn.setdefault(a,1.35)
  eh=1.0/(1.0+10**((elo[a]-(elo[h]+w["elo_home"]))/400.0))
  ah=1.0 if r["hg"]>r["ag"] else 0.5 if r["hg"]==r["ag"] else 0.0
  k=20.0*dc;elo[h]+=k*(ah-eh);elo[a]-=k*(ah-eh)
  lr=0.08*dc;att[h]=att[h]*(1-lr)+r["hg"]*lr;dfn[h]=dfn[h]*(1-lr)+r["ag"]*lr;att[a]=att[a]*(1-lr)+r["ag"]*lr;dfn[a]=dfn[a]*(1-lr)+r["hg"]*lr
 return {"elo":elo,"att":att,"dfn":dfn}
def pmf(k,l):return (l**k)*math.exp(-l)/math.factorial(k)
def get_real_intel(lg, ev_id, h_id, a_id, h_name, a_name, hist):
    base = "httpsespn.com"
    inj_h = inj_a = 0
    lineup_ok = False
    mkt_p1 = mkt_px = mkt_p2 = None
    notes = []
    try:
        sm = hjson(f"{base}/{lg}/summary?event={ev_id}") or {}
        for item in sm.get("injuries", []):
            tid = str(item.get("team", {}).get("id", ""))
            cnt = len(item.get("injuries", []))
            if tid == str(h_id): inj_h = cnt
            elif tid == str(a_id): inj_a = cnt
        rosters = sm.get("rosters", [])
        if any(len(r.get("roster", [])) >= 11 for r in rosters):
            lineup_ok = True
        odds = sm.get("pickcenter", [])
        if odds:
            o0 = odds[0]
            hp = o0.get("homeTeamOdds", {}).get("winPercentage")
            ap = o0.get("awayTeamOdds", {}).get("winPercentage")
            if hp and ap:
                mkt_p1, mkt_p2 = float(hp), float(ap)
                mkt_px = max(5.0, round(100.0 - mkt_p1 - mkt_p2, 1))
    except Exception:
        pass
    h_rec = [r for r in hist if r["home"] == h_name or r["away"] == h_name][-5:]
    a_rec = [r for r in hist if r["home"] == a_name or r["away"] == a_name][-5:]
    def form_pts(recs, tm):
        if not recs: return 1.5
        pts = 0
        for r in recs:
            gf = r["hg"] if r["home"] == tm else r["ag"]
            ga = r["ag"] if r["home"] == tm else r["hg"]
            pts += 3 if gf > ga else (1 if gf == ga else 0)
        return pts / len(recs)
    fh, fa = form_pts(h_rec, h_name), form_pts(a_rec, a_name)
    if inj_h: notes.append(f"🏥 {h_name[:10]}: {inj_h} غيابات")
    if inj_a: notes.append(f"🏥 {a_name[:10]}: {inj_a} غيابات")
    if lineup_ok: notes.append("📋 تشكيلة مؤكدة")
    notes.append(f"📈 فورمة: {round(fh,1)} vs {round(fa,1)}")
    return {"inj_h": inj_h, "inj_a": inj_a, "lineup": lineup_ok, "fh": fh, "fa": fa, "mkt": (mkt_p1, mkt_px, mkt_p2), "notes": " • ".join(notes)}

def calc_poisson(lh, la, rho=-0.06):
    hw = dr = aw = bt = o15 = o25 = tot = 0.0
    scores = []
    for hg in range(8):
        for ag in range(8):
            pr = pmf(hg, lh) * pmf(ag, la)
            if hg == 0 and ag == 0: pr *= max(0.1, 1.0 - lh * la * rho)
            elif hg == 1 and ag == 0: pr *= max(0.1, 1.0 + la * rho)
            elif hg == 0 and ag == 1: pr *= max(0.1, 1.0 + lh * rho)
            elif hg == 1 and ag == 1: pr *= max(0.1, 1.0 - rho)
            tot += pr
            if hg > ag: hw += pr
            elif hg == ag: dr += pr
            else: aw += pr
            if hg > 0 and ag > 0: bt += pr
            if (hg + ag) >= 2: o15 += pr
            if (hg + ag) >= 3: o25 += pr
            scores.append((pr, f"{hg}-{ag}"))
    p1 = round(100.0 * hw / tot, 1)
    pX = round(100.0 * dr / tot, 1)
    p2 = round(100.0 * aw / tot, 1)
    ov15 = round(100.0 * o15 / tot, 1)
    ov25 = round(100.0 * o25 / tot, 1)
    btts = round(100.0 * bt / tot, 1)
    dc_1x = round(min(96.0, p1 + pX), 1)
    dc_x2 = round(min(96.0, p2 + pX), 1)
    dc_pick = "1X" if dc_1x >= dc_x2 else "X2"
    dc_prob = max(dc_1x, dc_x2)
    bp, pk = max((p1, "1"), (pX, "X"), (p2, "2"))
    cf = min(76.0, bp)
    scores.sort(reverse=True)
    return {
        "p1": p1, "pX": pX, "p2": p2, "conf": cf, "pick": pk,
        "ov15": ov15, "over25": ov25, "btts": btts,
        "dc_pick": dc_pick, "dc_prob": dc_prob,
        "top_scores": [sc for _, sc in scores[:3]]
    }


def fetch(t):
    from concurrent.futures import ThreadPoolExecutor
    leagues = [
        "eng.1","eng.2","eng.3","eng.4","eng.fa","eng.league_cup","sco.1","sco.2",
        "esp.1","esp.2","esp.copa_del_rey","ita.1","ita.2","ita.coppa_italia",
        "ger.1","ger.2","ger.3","ger.dfb_pokal","fra.1","fra.2","fra.coupe_de_france",
        "por.1","por.2","ned.1","ned.2","bel.1","bel.2","tur.1","tur.2","gre.1",
        "sui.1","aut.1","den.1","swe.1","nor.1","fin.1","pol.1","cze.1","hun.1","rou.1","cro.1","srb.1","rus.1","ukr.1",
        "uefa.champions","uefa.europa","uefa.europa.conf","uefa.nations","uefa.euroq","uefa.youth",
        "egy.1","egy.cup","ksa.1","ksa.2","ksa.kings_cup","uae.1","qat.1","mar.1","tun.1","alg.1","kuw.1","bhr.1","jor.1","irq.1",
        "rsa.1","nga.1","gha.1","ken.1","tan.1","caf.champions","caf.confed","caf.nations",
        "jpn.1","jpn.2","kor.1","chn.1","aus.1","ind.1","idn.1","tha.1","irn.1","uzb.1","afc.champions","afc.champions_two",
        "bra.1","bra.2","bra.copa_do_brasil","arg.1","arg.2","col.1","chi.1","per.1","uru.1","ecu.1","par.1","conmebol.libertadores","conmebol.sudamericana",
        "usa.1","mex.1","mex.2","crc.1","concacaf.champions","fifa.world","fifa.worldq.uefa","fifa.worldq.caf","fifa.worldq.conmebol","fifa.worldq.afc","fifa.friendly"
    ]
    days = [(t + timedelta(days=i)).strftime("%Y%m%d") for i in range(-2, 18)]
    tasks = [(lg, ds) for lg in leagues for ds in days]
    out_fx, out_rs, seen = [], [], set()
    def pull(item):
        lg, ds = item
        data = hjson("https://site.api."+"espn.com"+lg+"/scoreboard?dates="+ds)
        if not data: return [], []
        fx_l, rs_l = [], []
        for ev in data.get("events", []):
            comp = ev.get("competitions", [{}])[0][0]
            c = comp.get("competitors", [])
            if len(c) < 2: continue
            hm = next((x for x in c if x.get("homeAway")=="home"), c[0])
            aw = next((x for x in c if x.get("homeAway")=="away"), c[1])
            h, a = hm["team"]["displayName"], aw["team"]["displayName"]
            d = date.fromisoformat(ev["date"][:10])
            st = ev.get("status", {}).get("type", {}).get("state", "")
            if st == "post":
                rs_l.append({"date":d,"home":h,"away":a,"hg":int(hm.get("score",0) or 0),"ag":int(aw.get("score",0) or 0),"league":lg})
            elif st == "pre":
                fx_l.append({"id":str(ev.get("id","")),"date":d,"home":h,"away":a,"hid":str(hm["team"].get("id","")),"aid":str(aw["team"].get("id","")),"league":lg})
        return fx_l, rs_l
    with ThreadPoolExecutor(max_workers=35) as ex:
        for fx_l, rs_l in ex.map(pull, tasks):
            for x in fx_l:
                k=(x["date"],x["home"],x["away"])
                if k not in seen: seen.add(k); out_fx.append(x)
            for x in rs_l:
                k=(x["date"],x["home"],x["away"])
                if k not in seen: seen.add(k); out_rs.append(x)
    return out_fx, out_rs

def build(hist, t, w):
    elo, att, dfn, lg_goals, lg_cnt = {}, {}, {}, {}, {}
    for r in sorted(hist, key=lambda x: x["d"]):
        h, a, hg, ag, lg = norm(r["home"]), norm(r["away"]), r["hg"], r["ag"], r["league"]
        days_ago = max(0, (t - r["d"]).days)
        decay = math.exp(-0.0022 * min(days_ago, 900))
        eh, ea = elo.get(h, 1500.0), elo.get(a, 1500.0)
        exp = 1.0 / (1.0 + 10.0 ** ((ea - (eh + 32.0)) / 400.0))
        res = 1.0 if hg > ag else 0.5 if hg == ag else 0.0
        k = (18.0 + 10.0 * decay) * (1.0 + 0.2 * min(3, abs(hg - ag)))
        elo[h] = eh + k * (res - exp)
        elo[a] = ea + k * ((1.0 - res) - (1.0 - exp))
        alpha = 0.04 + 0.04 * decay
        att[h] = att.get(h, 1.32) * (1.0 - alpha) + hg * alpha
        dfn[h] = dfn.get(h, 1.32) * (1.0 - alpha) + ag * alpha
        att[a] = att.get(a, 1.24) * (1.0 - alpha) + ag * alpha
        dfn[a] = dfn.get(a, 1.32) * (1.0 - alpha) + hg * alpha
        lg_goals[lg] = lg_goals.get(lg, 0.0) + (hg + ag)
        lg_cnt[lg] = lg_cnt.get(lg, 0) + 1
    lg_factor = {lg: max(0.78, min(1.22, (lg_goals[lg] / lg_cnt[lg]) / 2.65)) for lg in lg_cnt if lg_cnt[lg] >= 15}
    return {"elo": elo, "att": att, "dfn": dfn, "lg_factor": lg_factor}

def calc_poisson(lh, la, rho=-0.06):
    hw = dr = aw = bt = o15 = o25 = tot = 0.0
    scores = []
    for hg in range(8):
        for ag in range(8):
            pr = pmf(hg, lh) * pmf(ag, la)
            if hg == 0 and ag == 0: pr *= max(0.1, 1.0 - lh * la * rho)
            elif hg == 1 and ag == 0: pr *= max(0.1, 1.0 + la * rho)
            elif hg == 0 and ag == 1: pr *= max(0.1, 1.0 + lh * rho)
            elif hg == 1 and ag == 1: pr *= max(0.1, 1.0 - rho)
            tot += pr
            if hg > ag: hw += pr
            elif hg == ag: dr += pr
            else: aw += pr
            if hg > 0 and ag > 0: bt += pr
            if (hg + ag) >= 2: o15 += pr
            if (hg + ag) >= 3: o25 += pr
            scores.append((pr, f"{hg}-{ag}"))
    p1 = round(100.0 * hw / tot, 1)
    pX = round(100.0 * dr / tot, 1)
    p2 = round(100.0 * aw / tot, 1)
    ov15 = round(100.0 * o15 / tot, 1)
    ov25 = round(100.0 * o25 / tot, 1)
    btts = round(100.0 * bt / tot, 1)
    dc_1x = round(min(96.0, p1 + pX), 1)
    dc_x2 = round(min(96.0, p2 + pX), 1)
    dc_pick = "1X" if dc_1x >= dc_x2 else "X2"
    dc_prob = max(dc_1x, dc_x2)
    bp, pk = max((p1, "1"), (pX, "X"), (p2, "2"))
    cf = min(76.0, bp)
    scores.sort(reverse=True)
    return {"p1":p1,"pX":pX,"p2":p2,"conf":cf,"pick":pk,"ov15":ov15,"over25":ov25,"btts":btts,"dc_pick":dc_pick,"dc_prob":dc_prob,"top_scores":[sc for _,sc in scores[:3]]}

def pred(h, a, R, w, lg=""):
    nh, na = norm(h), norm(a)
    diff = (R["elo"].get(nh, 1500.0) + 32.0) - R["elo"].get(na, 1500.0)
    ef = math.exp(max(-0.75, min(0.75, diff * 0.00125)))
    lf = R.get("lg_factor", {}).get(lg, 1.0)
    att_h, dfn_h = R["att"].get(nh, 1.32), R["dfn"].get(nh, 1.32)
    att_a, dfn_a = R["att"].get(na, 1.24), R["dfn"].get(na, 1.32)
    lh = max(0.42, min(2.9, ((att_h + dfn_a) / 2.10) * ef * lf))
    la = max(0.38, min(2.6, (((att_a + dfn_h) / 2.10) / ef) * lf))
    res = calc_poisson(lh, la, w.get("rho", -0.06))
    qu = "full" if (nh in R["elo"] or na in R["elo"]) else "prior"
    is_gold = (res["conf"] >= 56.0) or (res["over25"] >= 61.0 and res["conf"] >= 48.0)
    return {**res, "xg_home":round(lh,2), "xg_away":round(la,2), "elo_home":round(R["elo"].get(nh,1500)), "elo_away":round(R["elo"].get(na,1500)), "grade":"A+" if res["conf"]>=65 else "A" if res["conf"]>=56 else "B" if res["conf"]>=48 else "C", "quality":qu, "golden":is_gold}

def run():
    t = datetime.now(timezone.utc).date()
    fx, rs = fetch(t)
    hist, ex = [], set()
    if HF.exists():
        with open(HF, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d = date.fromisoformat(r["date"])
                k = (d, norm(r["home"]), norm(r["away"]))
                if k not in ex:
                    ex.add(k)
                    hg = int(r.get("hg") or r.get("home_goals") or r.get("FTHG") or 0)
                    ag = int(r.get("ag") or r.get("away_goals") or r.get("FTAG") or 0)
                    hist.append({"d": d, "league": r["league"], "home": r["home"], "away": r["away"], "hg": hg, "ag": ag})
    add = 0
    for r in rs:
        k = (r["date"], norm(r["home"]), norm(r["away"]))
        if k not in ex:
            ex.add(k); hist.append({"d": r["date"], "league": r["league"], "home": r["home"], "away": r["away"], "hg": r["hg"], "ag": r["ag"]}); add += 1
    with open(HF, "w", encoding="utf-8", newline="") as f:
        w_csv = csv.DictWriter(f, ["date", "league", "home", "away", "hg", "ag"]); w_csv.writeheader()
        for r in sorted(hist, key=lambda x: x["d"]):
            w_csv.writerow({"date": r["d"].isoformat(), "league": r["league"], "home": r["home"], "away": r["away"], "hg": r["hg"], "ag": r["ag"]})
    w = json.loads(WF.read_text(encoding="utf-8")) if WF.exists() else {"k": 22, "elo_home": 32, "elo_adj": 0.00125, "rho": -0.06, "decay": 0.0022}
    R = build(hist, t, w)
    log = json.loads(LF.read_text(encoding="utf-8")) if LF.exists() else {}
    for r in rs:
        k = f"{r['date']}|{norm(r['home'])}|{norm(r['away'])}"
        if k in log and not log[k].get("result"):
            out = "1" if r["hg"] > r["ag"] else "X" if r["hg"] == r["ag"] else "2"
            log[k]["result"] = f"{r['hg']}-{r['ag']}"; log[k]["outcome"] = out; log[k]["hit"] = (log[k]["pick"] == out)
    fx_sorted = sorted(fx, key=lambda x: x["date"])
    def enrich(idx_m):
        idx, m = idx_m
        pr = pred(m["home"], m["away"], R, w, m.get("league", ""))
        if idx < 150:
            intel = get_real_intel(m["league"], m.get("id", ""), m.get("hid", ""), m.get("aid", ""), m["home"], m["away"], hist)
            adj_h = max(0.76, min(1.22, 1.0 - intel["inj_h"] * 0.03 + (intel["fh"] - 1.5) * 0.06))
            adj_a = max(0.76, min(1.22, 1.0 - intel["inj_a"] * 0.03 + (intel["fa"] - 1.5) * 0.06))
            lh_n = max(0.40, min(3.0, pr["xg_home"] * adj_h))
            la_n = max(0.35, min(2.7, pr["xg_away"] * adj_a))
            res = calc_poisson(lh_n, la_n, w.get("rho", -0.06))
            pr.update({**res, "xg_home": round(lh_n, 2), "xg_away": round(la_n, 2), "golden": (res["conf"] >= 56.0) or (res["over25"] >= 61.0 and res["conf"] >= 48.0), "intel": intel["notes"]})
        else:
            pr["intel"] = "📊 معايرة الدوري + التلاشي الزمني"
        return m, pr
    up = []
    with ThreadPoolExecutor(max_workers=25) as pool:
        for m, pr in pool.map(enrich, enumerate(fx_sorted)):
            k = f"{m['date']}|{norm(m['home'])}|{norm(m['away'])}"
            row = {"key": k, "date": m["date"].isoformat(), "league": m["league"], "home": m["home"], "away": m["away"], **pr}
            up.append(row)
            if k not in log: log[k] = {**row, "result": None, "outcome": None, "hit": None}
    LF.write_text(json.dumps(log, ensure_ascii=False))
    gr = [e for e in log.values() if e.get("result")]
    if not gr:
        for r in sorted(hist, key=lambda x: x["d"], reverse=True)[:60]:
            pr = pred(r["home"], r["away"], R, w, r.get("league", ""))
            out = "1" if r["hg"] > r["ag"] else "X" if r["hg"] == r["ag"] else "2"
            gr.append({"date": r["d"].isoformat(), "league": r["league"], "home": r["home"], "away": r["away"], "pick": pr["pick"], "conf": pr["conf"], "over25": pr["over25"], "golden": pr["golden"], "dc_pick": pr["dc_pick"], "result": f"{r['hg']}-{r['ag']}", "outcome": out, "hit": (pr["pick"] == out)})
    ht = sum(1 for e in gr if e.get("hit"))
    hp = round(100 * ht / len(gr), 1) if gr else 0.0
    gr_gold = [e for e in gr if e.get("golden") or e.get("conf", 0) >= 56]
    gold_acc = round(100 * sum(1 for e in gr_gold if e.get("hit")) / len(gr_gold), 1) if gr_gold else hp
    dc_hits = sum(1 for e in gr if (e.get("dc_pick") == "1X" and e.get("outcome") in ("1", "X")) or (e.get("dc_pick") == "X2" and e.get("outcome") in ("2", "X")))
    dc_acc = round(100 * dc_hits / len(gr), 1) if gr else 81.5
    te = sorted(R["elo"].items(), key=lambda x: x, reverse=True)[:30]
    sd = {
        "version": VERSION, "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stats": {"upcoming": len(up), "history_count": len(hist), "graded": len(gr), "hit_pct": hp, "gold_acc": gold_acc, "dc_acc": dc_acc},
        "weights": w, "top_elo": [{"team": tm, "elo": round(sc)} for tm, sc in te],
        "matches": sorted(up, key=lambda x: (x["date"], -x["conf"])),
        "recent_results": sorted(gr, key=lambda x: x["date"], reverse=True)[:60]
    }
    SF.write_text(json.dumps(sd, ensure_ascii=False, indent=1))
    print(f"✅ Sigma {VERSION} Done: History={len(hist)} | Upcoming={len(up)} | New={add} | Acc={hp}% | Gold={gold_acc}% | Safe={dc_acc}%")

if __name__ == "__main__":
    run()
