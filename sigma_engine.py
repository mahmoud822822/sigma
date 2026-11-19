import base64
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
def norm(s):
    s = re.sub(r"(fc|cf|sc|ac|as|cd|ud|fk|sk|bk|if|ik|afc|rfc|club|de|la|el|al|sporting|athletic)", " ", (s or "").lower())
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    mp = {
        "internazionale":"inter","inter milan":"inter","ac milan":"milan","as roma":"roma","ss lazio":"lazio","hellas verona":"verona",
        "paris saint germain":"psg","olympique marseille":"marseille","olympique lyonnais":"lyon","as monaco":"monaco",
        "wolverhampton wanderers":"wolves","brighton hove albion":"brighton","tottenham hotspur":"tottenham","nottingham forest":"nottm forest",
        "west ham united":"west ham","newcastle united":"newcastle","manchester united":"man united","manchester city":"man city",
        "bayern munich":"bayern","bayer leverkusen":"leverkusen","borussia dortmund":"dortmund","rb leipzig":"leipzig",
        "eintracht frankfurt":"ein frankfurt","borussia monchengladbach":"mgladbach","vfb stuttgart":"stuttgart",
        "atletico madrid":"atletico","athletic bilbao":"ath bilbao","real sociedad":"sociedad","real betis":"betis","celta vigo":"celta",
        "sporting cp":"sporting lisbon","ahly cairo":"ahly","al ahly":"ahly","zamalek":"zamalek","hilal":"hilal","nassr":"nassr","ittihad":"ittihad"
    }
    for k, v in mp.items():
        if k in s: return v
    return s or (s or "").lower().strip()

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
    cf = bp
    scores.sort(reverse=True)
    return {
        "p1": p1, "pX": pX, "p2": p2, "conf": cf, "pick": pk,
        "ov15": ov15, "over25": ov25, "btts": btts,
        "dc_pick": dc_pick, "dc_prob": dc_prob,
        "top_scores": [sc for _, sc in scores[:3]]
    }


def fetch(t):
    base = base64.b64decode("aHR0cHM6Ly9zaXRlLmFwaS5lc3BuLmNvbS9hcGlzL3NpdGUvdjIvc3BvcnRzL3NvY2Nlcg==").decode()
    leagues = {
        "eng.1","eng.2","eng.3","eng.4","eng.5","eng.fa","eng.league_cup","eng.trophy","sco.1","sco.2","sco.3","sco.fa","wal.1","nir.1","irl.1",
        "esp.1","esp.2","esp.copa_del_rey","ita.1","ita.2","ita.coppa_italia","ger.1","ger.2","ger.3","ger.dfb_pokal","fra.1","fra.2","fra.coupe_de_france",
        "por.1","por.2","por.taca","ned.1","ned.2","ned.knvb_beker","bel.1","bel.2","tur.1","tur.2","tur.cup","gre.1","gre.2","sui.1","sui.2",
        "aut.1","aut.2","den.1","den.2","swe.1","swe.2","nor.1","nor.2","fin.1","fin.2","isl.1","pol.1","pol.2","cze.1","cze.2","hun.1","rou.1",
        "cro.1","srb.1","bul.1","svk.1","svn.1","bih.1","mkd.1","alb.1","cyp.1","isr.1","rus.1","ukr.1","blr.1","kaz.1","aze.1","arm.1","geo.1",
        "uefa.champions","uefa.europa","uefa.europa.conf","uefa.nations","uefa.euroq","uefa.euro","uefa.youth","uefa.super_cup",
        "egy.1","egypt.1","egy.cup","ksa.1","sau.1","saudi.1","ksa.2","ksa.kings_cup","uae.1","uae.cup","qat.1","qatar.1","qat.cup","mar.1","morocco.1","mar.cup","tun.1","tunisia.1","tun.cup","alg.1","algeria.1","alg.cup","kuw.1","bhr.1","jor.1","irq.1","oma.1","lbn.1","sdn.1","lby.1","caf.champions","caf.confed","caf.nations","caf.nations_qual","afc.champions","afc.champions_two","afc.asian_cup","afc.cup","fifa.worldq.caf","fifa.worldq.afc","egypt.1","egy.cup","ksa.1","sau.1","saudi.1","ksa.2","ksa.kings_cup","uae.1","uae.cup","qat.1","qatar.1","qat.cup","mar.1","morocco.1","mar.cup","tun.1","tunisia.1","tun.cup","alg.1","algeria.1","alg.cup","kuw.1","bhr.1","jor.1","irq.1","oma.1","lbn.1","sdn.1","lby.1","caf.champions","caf.confed","caf.nations","caf.nations_qual","afc.champions","afc.champions_two","afc.asian_cup","afc.cup","fifa.worldq.caf","fifa.worldq.afc",
        "kuw.1","bhr.1","jor.1","irq.1","oma.1","lbn.1","sdn.1","lby.1","caf.champions","caf.confed","caf.nations","caf.nations_qual","caf.super_cup",
        "rsa.1","rsa.2","nga.1","gha.1","ken.1","tan.1","uga.1","zam.1","zim.1","eth.1","cmr.1","civ.1","sen.1",
        "jpn.1","jpn.2","jpn.3","jpn.cup","kor.1","kor.2","kor.cup","chn.1","chn.2","aus.1","aus.cup","nzl.1","ind.1","ind.2","idn.1","tha.1",
        "mys.1","vnm.1","sgp.1","irn.1","uzb.1","afc.champions","afc.champions_two","afc.asian_cup","afc.cup",
        "bra.1","bra.2","bra.3","bra.copa_do_brasil","arg.1","arg.2","arg.copa","col.1","col.2","chi.1","chi.2","per.1","uru.1","ecu.1","par.1",
        "bol.1","ven.1","conmebol.libertadores","conmebol.sudamericana","conmebol.recopa","conmebol.america",
        "usa.1","usa.usl.1","usa.open","mex.1","mex.2","mex.copa","can.1","crc.1","hon.1","slv.1","gua.1","pan.1","jam.1","concacaf.champions","concacaf.gold","concacaf.nations.league",
        "fifa.world","fifa.worldq.uefa","fifa.worldq.caf","fifa.worldq.conmebol","fifa.worldq.afc","fifa.worldq.concacaf","fifa.worldq.ofc","fifa.friendly","fifa.cwc","fifa.olympics"
    }
    days = [(t + timedelta(days=i)).strftime("%Y%m%d") for i in range(-2, 15)]
    out_fx, out_rs, seen = [], [], set()
    def parse_ev(ev, lg_hint=""):
        comp = next(iter(ev.get("competitions", [])), {})
        c = comp.get("competitors", [])
        if len(c) < 2: return None, None
        hm = next((x for x in c if x.get("homeAway") == "home"), c)
        aw = next((x for x in c if x.get("homeAway") == "away"), c[-1])
        h, a = hm["team"]["displayName"], aw["team"]["displayName"]
        h_logo = hm["team"].get("logo", "")
        a_logo = aw["team"].get("logo", "")
        lg_slug = ev.get("season", {}).get("slug") or lg_hint or "global"
        lg_name = comp.get("league", {}).get("name") or ev.get("league", {}).get("name") or lg_hint
        d = date.fromisoformat(ev["date"][:10])
        st = ev.get("status", {}).get("type", {}).get("state", "")
        if st == "post":
            return None, {"kickoff": (lambda dt: f"{(int(dt[11:13])+2)%24:02d}:{dt[14:16]}" if len(dt)>=16 else "20:00")(str(ev.get("date",""))), "date": d, "home": h, "away": a, "hg": int(hm.get("score", 0) or 0), "ag": int(aw.get("score", 0) or 0), "league": lg_hint or lg_slug}
        elif st == "pre":
            return {"id": str(ev.get("id", "")), "kickoff": (lambda dt: f"{(int(dt[11:13])+2)%24:02d}:{dt[14:16]}" if len(dt)>=16 else "20:00")(str(ev.get("date",""))), "date": d, "home": h, "away": a, "h_logo": h_logo, "a_logo": a_logo, "hid": str(hm["team"].get("id", "")), "aid": str(aw["team"].get("id", "")), "league": lg_hint or lg_slug, "tier": detect_tier(m["home"], m["away"], m.get("league_name", m.get("league",""))), "lgrade": detect_league_grade(m.get("league",""), m.get("league_name","")), "ctx_tags": detect_context_tags(m["home"], m["away"], m.get("league",""), m.get("league_name",""), round(get_base_elo(norm(m["home"]), R["elo"])), round(get_base_elo(norm(m["away"]), R["elo"]))), "league_name": lg_name}, None
        return None, None

    # 1. Auto-discover active global fixtures first
    for ds in days[:7]:
        gdata = hjson(f"{base}/all/scoreboard?dates={ds}&limit=300")
        if gdata:
            for ev in gdata.get("events", []):
                lg_s = ev.get("league", {}).get("slug", "")
                if lg_s: leagues.add(lg_s)
                fx_i, rs_i = parse_ev(ev, lg_s)
                if fx_i:
                    k = (fx_i["date"], fx_i["home"], fx_i["away"])
                    if k not in seen: seen.add(k); out_fx.append(fx_i)
                if rs_i:
                    k = (rs_i["date"], rs_i["home"], rs_i["away"])
                    if k not in seen: seen.add(k); out_rs.append(rs_i)

    # 2. Sweep all 220+ leagues across full window
    tasks = [(lg, ds) for lg in sorted(leagues) for ds in days]
    def pull(item):
        lg, ds = item
        data = hjson(f"{base}/{lg}/scoreboard?dates={ds}")
        if not data: return [], []
        lg_title = next((x.get("name", "") for x in data.get("leagues", [])), lg)
        fx_l, rs_l = [], []
        for ev in data.get("events", []):
            fx_i, rs_i = parse_ev(ev, lg)
            if fx_i:
                if lg_title: fx_i["league_name"] = lg_title
                fx_l.append(fx_i)
            if rs_i: rs_l.append(rs_i)
        return fx_l, rs_l

    with ThreadPoolExecutor(max_workers=14) as ex:
        for fx_l, rs_l in ex.map(pull, tasks):
            for x in fx_l:
                k = (x["date"], x["home"], x["away"])
                if k not in seen: seen.add(k); out_fx.append(x)
            for x in rs_l:
                k = (x["date"], x["home"], x["away"])
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
    cf = bp
    scores.sort(reverse=True)
    return {"p1": p1, "pX": pX, "p2": p2, "conf": cf, "pick": pk, "ov15": ov15, "over25": ov25, "btts": btts, "dc_pick": dc_pick, "dc_prob": dc_prob, "corners": round(max(6.4, min(13.6, 5.8 + (lh + la) * 1.45 + abs(lh - la) * 0.9)), 1), "top_scores": [sc for _, sc in scores[:3]]}

STOP_W = {"united","city","club","sporting","athletic","atletico","real","union","national","olympic","youth","academica","rovers","wanderers","albion","villa","town","county","fc","sc","ac","cf","cd","ud","sd","al","el"}
def resolve_team(name, pool):
    if is_reserve(name):
        return norm(name)
    n = norm(name)
    if n in pool: return n
    toks = [w for w in n.split() if len(w) > 3 and w not in STOP_W]
    for k in pool:
        if n in k or k in n or any(t in k.split() for t in toks):
            return k
    return n

ARAB_ELO = {
    "al hilal": 1745, "hilal": 1745, "al nassr": 1715, "nassr": 1715,
    "al ittihad": 1695, "ittihad": 1695, "al ahli": 1680, "ahli jeddah": 1680,
    "al qadsiah": 1625, "al shabab": 1615, "al ettifaq": 1595, "al taawoun": 1605,
    "al fateh": 1560, "al fayha": 1550, "al khaleej": 1545, "al riyadh": 1530,
    "abha": 1510, "al hazem": 1495, "al kholood": 1515, "diriyah": 1470, "neom": 1540,
    "al ahly": 1735, "zamalek": 1670, "pyramids": 1665, "masry": 1590, "ceramica": 1575,
    "ismaily": 1540, "enppi": 1545, "smouha": 1550, "zed": 1560, "modern": 1555,
    "raja": 1655, "wydad": 1650, "far rabat": 1640, "berkane": 1630,
    "esperance": 1665, "etoile": 1615, "club africain": 1610, "sfaxien": 1595,
    "usm alger": 1625, "mc alger": 1630, "belouizdad": 1635, "kabylie": 1605,
    "al ain": 1675, "shabab al ahli": 1655, "al wasl": 1650, "al jazira": 1615, "sharjah": 1625,
    "al sadd": 1670, "al duhail": 1655, "al rayyan": 1615, "al gharafa": 1610,
    "sundowns": 1700, "orlando pirates": 1635, "kaizer chiefs": 1600, "persepolis": 1645, "esteghlal": 1635, "ulsan": 1660, "jeonbuk": 1645, "vissel kobe": 1665, "yokohama": 1650
}
RESERVE_TAGS = (" u17"," u18"," u19"," u20"," u21"," u23"," women"," (w)"," wfc"," feminino"," ladies"," reserves"," castilla"," ii"," b")



DERBY_PAIRS = [
    ("ahly","zamalek"),("hilal","nassr"),("ittihad","ahli"),("inter","milan"),
    ("real madrid","atletico"),("real madrid","barcelona"),("liverpool","everton"),
    ("arsenal","tottenham"),("manchester united","manchester city"),("boca","river"),
    ("raja","wydad"),("esperance","club africain"),("galatasaray","fenerbahce"),
    ("celtic","rangers"),("roma","lazio"),("dortmund","bayern")
]

def detect_context_tags(h, a, slug, lname, elo_h, elo_a):
    tags = []
    tx = f" {slug} {lname} ".lower()
    hl, al = h.lower(), a.lower()
    if "final" in tx and "semi" not in tx and "quarter" not in tx:
        tags.append("👑 نهائي")
    elif any(k in tx for k in ["semi","quarter","round of 16","knockout","eliminat"]):
        tags.append("⚔️ خروج مغلوب")
    elif "group" in tx or "league-phase" in tx:
        tags.append("🔢 مجموعات")
    if "1st leg" in tx or "leg 1" in tx: tags.append("🔄 ذهاب")
    elif "2nd leg" in tx or "leg 2" in tx: tags.append("🔥 إياب")
    if any((x in hl and y in al) or (y in hl and x in al) for x, y in DERBY_PAIRS):
        tags.append("🔥 ديربي")
    elif abs(elo_h - elo_a) <= 35:
        tags.append("⚖️ متكافئة")
    return " • ".join(tags)

def detect_league_grade(slug, lname):
    tx = f" {slug} {lname} ".lower()
    if any(k in tx for k in ["friendly","friendlies","club.friendly","club friendly"]):
        return "🤝 مباراة ودية"
    if any(k in tx for k in ["super cup","supercup","supercopa","supercoppa","community shield","trophée des champions","dfl-supercup"]):
        return "⚡ كأس السوبر"
    if any(k in tx for k in ["playoff","play-off","relegation","promotion"]):
        return "⚔️ ملحق فاصل"
    if any(k in tx for k in ["worldq","qualif","wcq","afconq","euroq"]):
        return "🎯 تصفيات دولية"
    if any(k in tx for k in ["fifa.","world cup","nations league","euro 20","copa america","afcon","asian cup","gold cup"]):
        return "🌐 بطولة منتخبات"
    if any(k in tx for k in ["champions","europa","conference","libertadores","sudamericana","caf.","afc.","concacaf","leagues cup","arab club"]):
        return "🌍 بطولة قارية"
    if any(k in tx for k in ["cup","pokal","copa","coupe","coppa","trophy","shield","taça","beker","kupa"]):
        return "🏆 كأس محلي"
    if any(k in tx for k in [".4","league two","league-two","serie d","3. liga"]):
        return "4️⃣ دوري درجة 4"
    if any(k in tx for k in [".3","league one","league-one","serie c","primera rfef","national league"]):
        return "🥉 دوري درجة 3"
    if any(k in tx for k in [".2","championship","serie-b","serie b","segunda","2. bundesliga","2-bundesliga","ligue 2","ligue-2","eerste","challenger"]):
        return "🥈 دوري درجة 2"
    if any(k in tx for k in ["regional","amateur","non-league","oberliga","tercera"]):
        return "🏟️ دوري إقليمي"
    return "🥇 دوري ممتاز"

def detect_tier(home, away, league):
    txt = f" {home} {away} {league} ".lower()
    if any(k in txt for k in ["women","wfc","feminino","femenil","femminile","frauen","ladies","(w)","uwcl","nwsl","wsl"]):
        return "👩 سيدات"
    for u in ["u17","u18","u19","u20","u21","u23"]:
        if f" {u} " in txt or f"-{u}" in txt or f"({u})" in txt:
            return f"👦 {u.upper()}"
    if any(f" {home.lower()} ".endswith(x) or f" {away.lower()} ".endswith(x) for x in [" b "," ii "," reserves "," castilla "]) or "jong " in txt:
        return "🔁 رديف B"
    return ""

def is_reserve(name, league=""):
    if detect_tier(name, "", league) != "": return True
    ln = " " + name.lower().strip()
    return any(ln.endswith(t) or (t + " ") in ln for t in RESERVE_TAGS)

def get_base_elo(n, pool):
    if n in pool: return pool[n]
    for k, v in ARAB_ELO.items():
        if n == k: return v
    h_val = sum(ord(c) * (idx + 1) for idx, c in enumerate(n)) % 115
    return 1470.0 + h_val


def fetch_standings_stakes(leagues):
    stakes = {}
    for lg in list(set(leagues))[:28]:
        try:
            d = hjson(f"https://espn.com{lg}/standings")
            entries = d.get("children", [{}])[0].get("standings", {}).get("entries", [])
            n_tm = len(entries)
            if n_tm < 6: continue
            for idx, ent in enumerate(entries):
                tn = norm(ent.get("team", {}).get("displayName", ""))
                pos = idx + 1
                if pos <= 3:
                    stakes[tn] = (18, "🏆 صراع القمة واللقب")
                elif pos >= n_tm - 2:
                    stakes[tn] = (16, "🔥 معركة الهروب من الهبوط")
        except Exception:
            pass
    return stakes

def send_telegram_alerts(matches):
    tok = os.getenv("TELEGRAM_TOKEN", "").strip()
    cid = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not tok or not cid: return
    top = [m for m in matches if m.get("golden")][:5]
    if not top: return
    lines = ["👑 *SIGMA AI V300-SINGULARITY — أقوى الفرص الذهبية*\n"]
    for m in top:
        pk = f"فوز {m['home']}" if m["pick"]=="1" else (f"فوز {m['away']}" if m["pick"]=="2" else "تعادل")
        lines.append(f"⚽ *{m['home']} vs {m['away']}*\n🏆 {m.get('league_name',m['league'])} | 📅 {m['date']}\n🎯 التوقع: *{pk}* ({m['conf']}%) | 🛡️ أمان: {m['dc_pick']} ({m['dc_prob']}%)\n")
    try:
        req = urllib.request.Request(
            f"https://telegram.org{tok}/sendMessage",
            data=json.dumps({"chat_id": cid, "text": "\n".join(lines), "parse_mode": "Markdown"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=8)
    except Exception:
        pass


def sync_elo_memory(R):
    mp = "data/elo_memory.json"
    os.makedirs("data", exist_ok=True)
    saved = {}
    if os.path.exists(mp):
        try: saved = json.load(open(mp, encoding="utf-8"))
        except Exception: saved = {}
    for k, v in saved.items():
        if k not in R["elo"]: R["elo"][k] = float(v)
        else: R["elo"][k] = round(0.75 * R["elo"][k] + 0.25 * float(v), 2)
    json.dump({k: round(v, 2) for k, v in R["elo"].items()}, open(mp, "w", encoding="utf-8"))

def pred(h, a, R, w, lg=""):
    nh, na = resolve_team(h, R["elo"]), resolve_team(a, R["elo"])
    diff = (get_base_elo(nh, R["elo"]) + 32.0) - get_base_elo(na, R["elo"])
    ef = math.exp(max(-0.75, min(0.75, diff * 0.00125)))
    lf = R.get("lg_factor", {}).get(lg, 1.0)
    att_h, dfn_h = R["att"].get(nh, 1.32), R["dfn"].get(nh, 1.32)
    att_a, dfn_a = R["att"].get(na, 1.24), R["dfn"].get(na, 1.32)
    lh = max(0.42, min(2.9, ((att_h + dfn_a) / 2.10) * ef * lf))
    la = max(0.38, min(2.6, (((att_a + dfn_h) / 2.10) / ef) * lf))
    res = calc_poisson(lh, la, w.get("rho", -0.06))
    qu = "full" if (nh in R["elo"] or na in R["elo"]) else "prior"
    is_gold = (res["conf"] >= 56.0) or (res["over25"] >= 61.0 and res["conf"] >= 48.0)
    return {**res, "xg_home": round(lh, 2), "xg_away": round(la, 2), "elo_home": round(get_base_elo(nh, R["elo"])), "elo_away": round(get_base_elo(nh, R["elo"])), "grade": "A+" if res["conf"] >= 65 else "A" if res["conf"] >= 56 else "B" if res["conf"] >= 48 else "C", "quality": qu, "golden": is_gold}

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
            w_csv.writerow({"kickoff": (lambda dt: f"{(int(dt[11:13])+2)%24:02d}:{dt[14:16]}" if len(dt)>=16 else "20:00")(str(ev.get("date",""))), "date": r["d"].isoformat(), "league": r["league"], "home": r["home"], "away": r["away"], "hg": r["hg"], "ag": r["ag"]})
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
            row = {"key": k, "kickoff": (lambda dt: f"{(int(dt[11:13])+2)%24:02d}:{dt[14:16]}" if len(dt)>=16 else "20:00")(str(ev.get("date",""))), "date": m["date"].isoformat(), "league": m["league"], "tier": detect_tier(m["home"], m["away"], m.get("league_name", m.get("league",""))), "lgrade": detect_league_grade(m.get("league",""), m.get("league_name","")), "ctx_tags": detect_context_tags(m["home"], m["away"], m.get("league",""), m.get("league_name",""), round(get_base_elo(norm(m["home"]), R["elo"])), round(get_base_elo(norm(m["away"]), R["elo"]))), "league_name": m.get("league_name", m["league"]), "home": m["home"], "away": m["away"], "h_logo": m.get("h_logo", ""), "a_logo": m.get("a_logo", ""), **pr}
            up.append(row)
            if k not in log: log[k] = {**row, "result": None, "outcome": None, "hit": None}
    LF.write_text(json.dumps(log, ensure_ascii=False))
    gr = [e for e in log.values() if e.get("result")]
    gr = []
    if True:
        for r in sorted(hist, key=lambda x: x["d"], reverse=True)[:60]:
            pr = pred(r["home"], r["away"], R, w, r.get("league", ""))
            out = "1" if r["hg"] > r["ag"] else "X" if r["hg"] == r["ag"] else "2"
            gr.append({"kickoff": (lambda dt: f"{(int(dt[11:13])+2)%24:02d}:{dt[14:16]}" if len(dt)>=16 else "20:00")(str(ev.get("date",""))), "date": r["d"].isoformat(), "league": r["league"], "home": r["home"], "away": r["away"], "pick": pr["pick"], "conf": pr["conf"], "over25": pr["over25"], "golden": pr["golden"], "dc_pick": pr["dc_pick"], "result": f"{r['hg']}-{r['ag']}", "outcome": out, "hit": (pr["pick"] == out)})
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
