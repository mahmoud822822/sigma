import re

p = "sigma_engine.py"
s = open(p).read()

s = s.replace('VERSION = "V75"', 'VERSION = "V80-REAL-INTEL"')

intel_fn = '''def get_real_intel(lg, ev_id, h_id, a_id, h_name, a_name, hist):
    base = "https://espn.com"
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

'''

if "def get_real_intel(" not in s:
    s = s.replace("def pred(", intel_fn + "def pred(")

# Store event id & team ids in fetch
s = s.replace(
    'out_fx.append({"date": d, "home": h, "away": a, "league": lg})',
    'hid = next(x["team"]["id"] for x in c if x["homeAway"] == "home"); aid = next(x["team"]["id"] for x in c if x["homeAway"] == "away"); out_fx.append({"id": ev.get("id",""), "date": d, "home": h, "away": a, "hid": hid, "aid": aid, "league": lg})'
)

# Apply real intel in run() loop for upcoming matches (top 180 nearest matches for speed + full rest)
old_loop = '''    up=[]
    for m in fx:
        pr=pred(m["home"],m["away"],R,w)'''

new_loop = '''    from concurrent.futures import ThreadPoolExecutor
    fx_sorted = sorted(fx, key=lambda x: x["date"])
    def enrich(idx_m):
        idx, m = idx_m
        pr = pred(m["home"], m["away"], R, w)
        if idx < 180 and m.get("id"):
            intel = get_real_intel(m["league"], m["id"], m.get("hid",""), m.get("aid",""), m["home"], m["away"], hist)
            adj_h = max(0.75, 1.0 - intel["inj_h"]*0.035 + (intel["fh"]-1.5)*0.08)
            adj_a = max(0.75, 1.0 - intel["inj_a"]*0.035 + (intel["fa"]-1.5)*0.08)
            pr["xg_home"] = round(pr["xg_home"] * adj_h, 2)
            pr["xg_away"] = round(pr["xg_away"] * adj_a, 2)
            if intel["mkt"][0]:
                mp1, mpx, mp2 = intel["mkt"]
                pr["p1"] = round(pr["p1"]*0.65 + mp1*0.35, 1)
                pr["pX"] = round(pr["pX"]*0.65 + mpx*0.35, 1)
                pr["p2"] = round(pr["p2"]*0.65 + mp2*0.35, 1)
                bp, pk = max((pr["p1"],"1"),(pr["pX"],"X"),(pr["p2"],"2"))
                pr["pick"], pr["conf"] = pk, min(88.0, bp)
                pr["golden"] = (pr["conf"] >= 58.0) or (pr["over25"] >= 64.0 and pr["conf"] >= 50.0)
            pr["intel"] = intel["notes"]
        else:
            pr["intel"] = "📊 تحليل Elo + Poisson"
        return m, pr
    up=[]
    with ThreadPoolExecutor(max_workers=20) as ex:
        enriched = list(ex.map(enrich, enumerate(fx_sorted)))
    for m, pr in enriched:'''

assert old_loop in s, "Loop pattern not found"
s = s.replace(old_loop, new_loop)
open(p, "w").write(s)

# Update index.html to display real-world intel bar under each match
h = open("index.html").read()
if "m.intel" not in h:
    h = h.replace(
        '<div class="met">',
        '<div style="font-size:.72rem;color:#38bdf8;margin-bottom:6px;background:#0f172a;padding:5px 8px;border-radius:7px">${m.intel||"📊 تحليل Elo + Poisson"}</div><div class="met">'
    )
    open("index.html", "w").write(h)

print("SIGMA V80 REAL-WORLD INTEL UPGRADED OK")
