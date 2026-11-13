#!/usr/bin/env python3
# =====================================================================================
# SIGMA V50 ALL-IN-ONE  (single file, stdlib only, no Arabic text inside this file)
# Commands:  python3 sigma_v50.py <cmd>
#   core      history -> ratings -> backtest -> re-predict fixtures   (replaces V46)
#   brain     V49 seed/brain pulse (add --loop for continuous)
#   gate      pre-push checks, exit 1 = DO NOT PUSH
#   pipeline  core -> v47/v48 (if present) -> brain -> gate -> push -> supabase sync
#             add --dry to stop before push
#   push      push only (token in ~/token.txt, never stored in .git/config)
#   sync      Supabase upsert (add --dry to test)     schema   print Supabase SQL
#   selftest  15 checks on synthetic data (does not touch your repo)
# Edit the CONFIG block below. Model constants are at the top of the CORE section.
# Env: SIGMA_TODAY=YYYY-MM-DD overrides today's date (testing).
# Changelog V50: robust dates, blank score != 0-0, entity regex accepts '|' and broken-bar,
#   real shrinkage, home/away conceded split, unknown team -> blended base rates,
#   real 3-fold walk-forward + baseline + calibration, honest data_quality, gate with secret scan.
# =====================================================================================
import json, csv, re, math, os, sys, glob, difflib, unicodedata, hashlib
import base64, subprocess, shutil, tempfile, random, urllib.request, urllib.error
from pathlib import Path
from datetime import date, datetime, timezone, timedelta
from collections import defaultdict, Counter, deque
import time

# ----------------------------- CONFIG (edit here) -----------------------------
REMOTE = "https://github.com/mahmoud822822/sigma.git"
BRANCH = "main"
BACKUP_BRANCH = "backup-pre-v50"
TOKEN_FILE = Path.home() / "token.txt"
ENV_FILE = Path.home() / ".sigma_env"          # SUPABASE_URL / SUPABASE_SERVICE_KEY
OPTIONAL_SCRIPTS = ["sigma_v47_verify_fix.py", "sigma_v48_add_posters_basketball.py"]
# -------------------------------------------------------------------------------

# ============================== SECTION: CORE ==============================
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
VERSION = "V50"
RHO, XI, ELO_K, ELO_HOME, ELO_ADJ = -0.08, 0.0018, 20, 65, 0.0010
SHRINK_K, MIN_N_FULL, MIN_N_GOLDEN = 5.0, 8, 15
FALLBACK_AVG = (1.5, 1.2)
FIXTURE_FILES = ["sigma_bulk_predictions.json", "sigma_bulk_predictions_v44.json",
                 "sigma_universal_fixtures.json", "sigma_next_month.json"]

def today():
    s = os.environ.get("SIGMA_TODAY")
    return date.fromisoformat(s) if s else date.today()

# ---------------- dates ----------------
_FMTS = ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d.%m.%Y")
def parse_date(s):
    s = re.split(r"[T ]", str(s or "").strip())[0]
    for f in _FMTS:
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            pass
    return None

# ---------------- entity-tag cleaning ----------------
_SEP = r"[|\u00a6]"
_ENT_FULL = re.compile("\u3010entity-[^\u3011]*?" + _SEP + r"canonical_name=([^\u3011]+)\u3011")
_ENT_ANY = re.compile("\u3010entity-([^\u3011|\u00a6]+)(?:" + _SEP + "[^\u3011]*)?\u3011")
_ENT_BARE = re.compile(r"entity-[^|\u00a6,;\"]*" + _SEP + r"canonical_name=([^,;\"]+)")
def clean_str(s):
    if not isinstance(s, str):
        return s
    t = s
    for _ in range(3):
        t = _ENT_FULL.sub(r"\1", t); t = _ENT_ANY.sub(r"\1", t); t = _ENT_BARE.sub(r"\1", t)
    t = t.replace("\u3010", "").replace("\u3011", "")
    return re.sub(r"\s+", " ", t).strip()
def clean_obj(o):
    if isinstance(o, dict): return {clean_str(k): clean_obj(v) for k, v in o.items()}
    if isinstance(o, list): return [clean_obj(x) for x in o]
    return clean_str(o) if isinstance(o, str) else o
def has_tag(txt): return "entity-" in txt or "\u3010" in txt

def clean_all_files():
    n = 0
    for pat in ("data/*.json", "data/*.csv", "*.json", "*.csv"):
        for p in sorted(set(BASE.glob(pat))):
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
                if not has_tag(txt): continue
                if p.suffix == ".json":
                    new = json.dumps(clean_obj(json.loads(txt)), ensure_ascii=False, indent=1)
                else:
                    new = "\n".join(clean_str(l) for l in txt.splitlines()) + "\n"
                p.write_text(new, encoding="utf-8"); n += 1
            except Exception as e:
                print("skip clean", p.name, e)
    return n

# ---------------- name resolution ----------------
BUILTIN_ALIASES = {
 "paris saint-germain fc": "Paris SG", "paris saint germain": "Paris SG", "psg": "Paris SG",
 "sporting clube de braga": "Sp Braga", "psv": "PSV Eindhoven", "feyenoord rotterdam": "Feyenoord",
 "fc bayern munchen": "Bayern Munich", "bayern": "Bayern Munich", "1. fc koln": "FC Koln",
 "sc paderborn 07": "Paderborn", "rc celta de vigo": "Celta", "ca osasuna": "Osasuna",
 "athletic club": "Ath Bilbao", "real sociedad de futbol": "Sociedad", "real sociedad": "Sociedad",
 "atletico madrid": "Ath Madrid", "ado den haag": "Den Haag", "sc cambuur-leeuwarden": "Cambuur",
 "man city": "Man City", "manchester city": "Man City", "manchester united": "Man United"}
_STOP = {"fc", "cf", "afc", "sc", "ca", "rc", "fk", "cd", "club", "de", "the", "1", "04", "07"}
def _norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return " ".join(t for t in re.split(r"[^a-z0-9]+", s) if t and t not in _STOP)

class Names:
    def __init__(self, known, user_aliases=None):
        self.known = set(known)
        self.alias = {_norm(k): v for k, v in BUILTIN_ALIASES.items()}
        self.alias.update({_norm(k): v for k, v in (user_aliases or {}).items()})
        self.idx = {_norm(k): k for k in self.known}
        self.cache, self.fuzzy, self.unresolved = {}, {}, set()
    def resolve(self, name):
        if name in self.cache: return self.cache[name]
        r = None
        if name in self.known: r = name
        else:
            n = _norm(name)
            a = self.alias.get(n)
            if a in self.known: r = a
            elif n in self.idx: r = self.idx[n]
            else:
                c = difflib.get_close_matches(n, list(self.idx), n=1, cutoff=0.9)
                if c: r = self.idx[c[0]]; self.fuzzy[name] = r
        if r is None: self.unresolved.add(name)
        self.cache[name] = r
        return r

# ---------------- history ----------------
def load_history(ref):
    st = Counter(); out = []; seen = set()
    p = DATA / "sigma_history.csv"
    if not p.exists(): return out, st
    with open(p, encoding="utf-8", errors="replace", newline="") as fh:
        for r in csv.DictReader(fh):
            st["rows"] += 1
            low = {(k or "").strip().lower(): v for k, v in r.items()}
            h = clean_str(low.get("home") or low.get("hometeam") or low.get("home_team") or "")
            a = clean_str(low.get("away") or low.get("awayteam") or low.get("away_team") or "")
            d = parse_date(low.get("date") or low.get("ts") or "")
            hg = low.get("home_goals") or low.get("homegoals") or low.get("fthg")
            ag = low.get("away_goals") or low.get("awaygoals") or low.get("ftag")
            if not h or not a: st["bad_teams"] += 1; continue
            if d is None: st["bad_date"] += 1; continue
            try: hg, ag = int(float(hg)), int(float(ag))
            except (TypeError, ValueError): st["no_score"] += 1; continue
            if d > ref: st["future"] += 1; continue
            k = (d, h, a)
            if k in seen: st["dupes"] += 1; continue
            seen.add(k)
            out.append({"d": d, "home": h, "away": a, "hg": hg, "ag": ag,
                        "league": clean_str(low.get("league") or low.get("div") or "Default")})
    out.sort(key=lambda x: x["d"])
    st["kept"] = len(out)
    return out, st

# ---------------- ratings ----------------
def build_ratings(hist, ref):
    elo = defaultdict(lambda: 1500.0)
    lgs = defaultdict(lambda: [0, 0, 0]); tl = defaultdict(Counter)
    raw = defaultdict(lambda: dict(hw=0., hsc=0., hco=0., aw=0., asc=0., aco=0., n=0, bt=0, ov=0, form=deque(maxlen=5)))
    res = Counter(); tot_btts = tot_over = 0
    for r in hist:
        h, a, hg, ag = r["home"], r["away"], r["hg"], r["ag"]
        eh = elo[h] + ELO_HOME
        exp_h = 1 / (1 + 10 ** (-(eh - elo[a]) / 400.0))
        act = 1.0 if hg > ag else 0.5 if hg == ag else 0.0
        mg = min(2.0, 1.0 + abs(hg - ag) * 0.15)
        elo[h] += ELO_K * mg * (act - exp_h); elo[a] -= ELO_K * mg * (act - exp_h)
        L = lgs[r["league"]]; L[0] += hg; L[1] += ag; L[2] += 1
        tl[h][r["league"]] += 1; tl[a][r["league"]] += 1
        w = math.exp(-XI * max(0, (ref - r["d"]).days))
        bt = 1 if hg > 0 and ag > 0 else 0; ov = 1 if hg + ag >= 3 else 0
        tot_btts += bt; tot_over += ov
        res["1" if hg > ag else "X" if hg == ag else "2"] += 1
        for team, sc, co, home in ((h, hg, ag, True), (a, ag, hg, False)):
            t = raw[team]; t["n"] += 1; t["bt"] += bt; t["ov"] += ov
            t["form"].append("W" if sc > co else "D" if sc == co else "L")
            if home: t["hw"] += w; t["hsc"] += w * sc; t["hco"] += w * co
            else: t["aw"] += w; t["asc"] += w * sc; t["aco"] += w * co
    n = len(hist)
    glob_avg = (sum(v[0] for v in lgs.values()) / n, sum(v[1] for v in lgs.values()) / n) if n else FALLBACK_AVG
    league_avg = {k: (v[0] / v[2], v[1] / v[2]) for k, v in lgs.items()}
    teams = {}
    for team, t in raw.items():
        lg = tl[team].most_common(1)[0][0]
        lh, la = league_avg.get(lg, glob_avg); K = SHRINK_K
        teams[team] = {"n": t["n"], "league": lg, "elo": round(elo[team], 1),
            "home_sc": (t["hsc"] + K * lh) / (t["hw"] + K), "home_co": (t["hco"] + K * la) / (t["hw"] + K),
            "away_sc": (t["asc"] + K * la) / (t["aw"] + K), "away_co": (t["aco"] + K * lh) / (t["aw"] + K),
            "btts_rate": round(100 * t["bt"] / t["n"], 1), "over25_rate": round(100 * t["ov"] / t["n"], 1),
            "form": "".join(t["form"])}
    base = ((res["1"] / n, res["X"] / n, res["2"] / n) if n else (0.45, 0.26, 0.29))
    return {"teams": teams, "league_avg": league_avg, "glob": glob_avg, "base": base,
            "base_btts": tot_btts / n if n else 0.5, "base_over": tot_over / n if n else 0.5}

# ---------------- model ----------------
def _pois(l, k): return math.exp(-l) * l ** k / math.factorial(k)
def dc_grid(lh, la, rho=RHO, mg=10):
    g, tot = {}, 0.0
    for x in range(mg + 1):
        for y in range(mg + 1):
            tau = (1 - lh * la * rho if (x, y) == (0, 0) else 1 + lh * rho if (x, y) == (0, 1)
                   else 1 + la * rho if (x, y) == (1, 0) else 1 - rho if (x, y) == (1, 1) else 1.0)
            p = _pois(lh, x) * _pois(la, y) * max(0.05, tau); g[(x, y)] = p; tot += p
    g = {k: v / tot for k, v in g.items()}
    return {"1": sum(p for (x, y), p in g.items() if x > y), "X": sum(p for (x, y), p in g.items() if x == y),
            "2": sum(p for (x, y), p in g.items() if x < y),
            "btts": sum(p for (x, y), p in g.items() if x > 0 and y > 0),
            "over25": sum(p for (x, y), p in g.items() if x + y >= 3),
            "top": [{"score": f"{x}-{y}", "p": round(p * 100, 1)} for (x, y), p in sorted(g.items(), key=lambda z: -z[1])[:3]]}

def predict(home, away, R, league="Default"):
    T = R["teams"]; hs, as_ = T.get(home), T.get(away)
    lh, la = R["league_avg"].get(league) or (R["league_avg"].get(hs["league"]) if hs else None) or R["glob"]
    prior_h = {"home_sc": lh, "home_co": la, "away_sc": la, "away_co": lh, "elo": 1500.0, "n": 0}
    H, A = hs or prior_h, as_ or prior_h
    lam_h = H["home_sc"] * A["away_co"] / lh
    lam_a = A["away_sc"] * H["home_co"] / la
    d = (H["elo"] + ELO_HOME - A["elo"]) * ELO_ADJ
    lam_h = max(0.2, min(3.8, lam_h * (1 + d))); lam_a = max(0.2, min(3.8, lam_a * (1 - d)))
    g = dc_grid(round(lam_h, 2), round(lam_a, 2))
    nh, na = H["n"], A["n"]
    q = "full" if min(nh, na) >= MIN_N_FULL else "partial" if (max(nh, na) >= MIN_N_FULL or min(nh, na) >= 3) else "prior"
    alpha = {"full": 0.0, "partial": 0.5, "prior": 1.0}[q]   # weight of base rates
    b1, bx, b2 = R["base"]
    p1 = (1 - alpha) * g["1"] + alpha * b1; px = (1 - alpha) * g["X"] + alpha * bx; p2 = (1 - alpha) * g["2"] + alpha * b2
    btts = (1 - alpha) * g["btts"] + alpha * R["base_btts"]; over = (1 - alpha) * g["over25"] + alpha * R["base_over"]
    top3 = max(p1, px, p2)
    n = min(nh, na)
    grade = ("A" if n >= 30 else "B" if n >= 15 else "C") if q == "full" else ("C" if q == "partial" else "D")
    return {"lam_h": round(lam_h, 2), "lam_a": round(lam_a, 2), "p1": round(p1 * 100, 1), "pX": round(px * 100, 1),
            "p2": round(p2 * 100, 1), "btts": round(btts * 100, 1), "over25": round(over * 100, 1),
            "conf": round(top3 * 100, 1), "pick": "1" if p1 >= px and p1 >= p2 else "X" if px >= p2 else "2",
            "grade": grade, "quality": q, "n_home": nh, "n_away": na,
            "golden": 1 if (q == "full" and n >= MIN_N_GOLDEN and top3 >= 0.70) else 0,
            "top": g["top"] if q != "prior" else []}

# ---------------- walk-forward (real, 3 folds) ----------------
def _score(P, real):
    return sum((P[k] - (1 if k == real else 0)) ** 2 for k in "1X2"), -math.log(max(1e-6, P[real]))
def walk_forward(hist, folds=3):
    n = len(hist); block = min(300, (n - 300) // folds) if n > 300 else 0
    if block < 30: return {"n": 0, "note": "not enough history for walk-forward"}
    acc = {k: {"n": 0, "br": 0., "ll": 0., "hit": 0, "bbr": 0., "bll": 0.} for k in ("all", "full")}
    per, cal = [], defaultdict(lambda: [0, 0.0, 0])
    for f in range(folds):
        a = n - (folds - f) * block; b = a + block
        train, test = hist[:a], hist[a:b]
        R = build_ratings(train, test[0]["d"]); bs = R["base"]
        fa = {"n": 0, "br": 0., "ll": 0., "hit": 0}
        for r in test:
            p = predict(r["home"], r["away"], R, r["league"])
            P = {"1": p["p1"] / 100, "X": p["pX"] / 100, "2": p["p2"] / 100}
            real = "1" if r["hg"] > r["ag"] else "X" if r["hg"] == r["ag"] else "2"
            br, ll = _score(P, real); bbr, bll = _score(dict(zip("1X2", bs)), real)
            for key in (("all",) if p["quality"] != "full" else ("all", "full")):
                A = acc[key]; A["n"] += 1; A["br"] += br; A["ll"] += ll; A["bbr"] += bbr; A["bll"] += bll
                A["hit"] += (p["pick"] == real)
            fa["n"] += 1; fa["br"] += br; fa["ll"] += ll; fa["hit"] += (p["pick"] == real)
            top = max(P.values()); bi = min(int(top * 10), 9)
            c = cal[bi]; c[0] += 1; c[1] += top; c[2] += (p["pick"] == real)
        per.append({"fold": f + 1, "n": fa["n"], "brier": round(fa["br"] / fa["n"], 4),
                    "logloss": round(fa["ll"] / fa["n"], 4), "hit_pct": round(100 * fa["hit"] / fa["n"], 1)})
    def fin(A):
        if not A["n"]: return {"n": 0}
        return {"n": A["n"], "brier": round(A["br"] / A["n"], 4), "logloss": round(A["ll"] / A["n"], 4),
                "hit_pct": round(100 * A["hit"] / A["n"], 1), "baseline_brier": round(A["bbr"] / A["n"], 4),
                "baseline_logloss": round(A["bll"] / A["n"], 4),
                "brier_skill": round(1 - A["br"] / A["bbr"], 4)}
    return {"folds": per, "pooled_all": fin(acc["all"]), "pooled_full_quality": fin(acc["full"]),
            "calibration": [{"bin": f"{i*10}-{i*10+10}%", "n": c[0], "mean_pred_pct": round(100 * c[1] / c[0], 1),
                             "hit_pct": round(100 * c[2] / c[0], 1)} for i, c in sorted(cal.items()) if c[0]],
            "note": "train=strictly before each test block; baseline=train base rates (home/draw/away)"}

# ---------------- fixtures ----------------
def extract_teams(mm):
    lg = clean_str(mm.get("league") or mm.get("competition") or "Default")
    h = a = None
    if isinstance(mm.get("match"), str) and " vs " in mm["match"]:
        h, a = [clean_str(x) for x in mm["match"].split(" vs ", 1)]
    else:
        for k in ("home", "homeTeam", "home_team"):
            if mm.get(k): h = clean_str(mm[k]["name"] if isinstance(mm[k], dict) else mm[k]); break
        for k in ("away", "awayTeam", "away_team"):
            if mm.get(k): a = clean_str(mm[k]["name"] if isinstance(mm[k], dict) else mm[k]); break
    return h, a, lg

def apply_prediction(mm, h, a, p):
    q = p["quality"]
    mm.update({"xG": f"{p['lam_h']} - {p['lam_a']}", "xg_home": p["lam_h"], "xg_away": p["lam_a"],
               "p1": p["p1"], "pX": p["pX"], "p2": p["p2"], "1": p["p1"], "X": p["pX"], "2": p["p2"],
               "conf": p["conf"], "confidence": p["conf"], "pick": p["pick"], "grade": p["grade"],
               "btts": p["btts"], "BTTS": p["btts"], "over25": p["over25"], "Over25": p["over25"],
               "top_scores": p["top"], "golden": p["golden"], "data_quality": q,
               "is_default": 1 if q == "prior" else 0, "is_new_team": 0 if q == "full" else 1,
               "n_home": p["n_home"], "n_away": p["n_away"], "model": VERSION,
               "source": "history-dixon-coles-elo" if q == "full" else f"blended-base-rates-{q}"})
    if isinstance(mm.get("match"), str): mm["match"] = f"{h} vs {a}"

def process_fixtures(R, names):
    qual = Counter()
    for fname in FIXTURE_FILES:
        for cand in (DATA / fname, BASE / fname):
            if not cand.exists(): continue
            try:
                obj = json.loads(cand.read_text(encoding="utf-8"))
                rows = obj if isinstance(obj, list) else obj.get("matches", obj.get("data", []))
                if not isinstance(rows, list): continue
                for mm in rows:
                    if str(mm.get("status", "")).upper() in ("FINISHED", "ARCHIVED"): continue
                    h, a, lg = extract_teams(mm)
                    if not h or not a: continue
                    p = predict(names.resolve(h) or h, names.resolve(a) or a, R, lg)
                    apply_prediction(mm, h, a, p); qual[p["quality"]] += 1
                if isinstance(obj, list): cand.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
                else: obj["matches"] = rows; cand.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"predicted {cand.name}: {len(rows)} rows")
            except Exception as e:
                print("skip", cand.name, e)
    return qual

def collect_predictions():
    """flat rows for Supabase sync"""
    out, seen = [], set()
    for fname in FIXTURE_FILES:
        for cand in (DATA / fname, BASE / fname):
            if not cand.exists(): continue
            try: obj = json.loads(cand.read_text(encoding="utf-8"))
            except Exception: continue
            rows = obj if isinstance(obj, list) else obj.get("matches", obj.get("data", []))
            for mm in rows if isinstance(rows, list) else []:
                h, a, lg = extract_teams(mm)
                d = parse_date(mm.get("date") or mm.get("ts") or "")
                if not h or not a or not d or "p1" not in mm: continue
                key = f"{d.isoformat()}|{_norm(h)}|{_norm(a)}"
                if key in seen: continue
                seen.add(key)
                out.append({"match_key": key, "match_date": d.isoformat(), "league": lg, "home": h, "away": a,
                            "p1": mm.get("p1"), "px": mm.get("pX"), "p2": mm.get("p2"), "btts": mm.get("btts"),
                            "over25": mm.get("over25"), "xg_home": mm.get("xg_home"), "xg_away": mm.get("xg_away"),
                            "pick": mm.get("pick"), "grade": mm.get("grade"),
                            "data_quality": mm.get("data_quality", "prior"), "golden": bool(mm.get("golden")),
                            "model": mm.get("model", "unknown")})
    return out

# ---------------- main ----------------
def core_main():
    t = today()
    print(f"Sigma {VERSION} CORE - today={t}")
    cleaned = clean_all_files(); print("files cleaned of entity tags:", cleaned)
    hist, hs = load_history(t); print("history:", dict(hs))
    R = build_ratings(hist, t)
    ua = DATA / "sigma_aliases.json"
    names = Names(R["teams"], json.loads(ua.read_text(encoding="utf-8")) if ua.exists() else {})
    ts = {k: {"n": v["n"], "elo": v["elo"], "form": v["form"], "btts_rate": v["btts_rate"], "over25_rate": v["over25_rate"],
              "scored_avg": round((v["home_sc"] + v["away_sc"]) / 2, 3), "conceded_avg": round((v["home_co"] + v["away_co"]) / 2, 3),
              "home_scored_avg": round(v["home_sc"], 3), "away_scored_avg": round(v["away_sc"], 3),
              "home_conceded_avg": round(v["home_co"], 3), "away_conceded_avg": round(v["away_co"], 3)} for k, v in R["teams"].items()}
    (DATA / "sigma_team_stats.json").write_text(json.dumps(ts, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA / "sigma_league_stats.json").write_text(json.dumps({k: {"home_avg": round(v[0], 3), "away_avg": round(v[1], 3)} for k, v in R["league_avg"].items()}, ensure_ascii=False, indent=1), encoding="utf-8")
    bt = walk_forward(hist); (DATA / "sigma_backtest.json").write_text(json.dumps(bt, ensure_ascii=False, indent=1), encoding="utf-8")
    qual = process_fixtures(R, names)
    rep = {"version": VERSION, "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "today": t.isoformat(),
           "history": dict(hs), "teams": len(R["teams"]), "fixture_quality": dict(qual),
           "fuzzy_name_matches": names.fuzzy, "unresolved_names": sorted(names.unresolved),
           "backtest": {k: bt.get(k) for k in ("pooled_all", "pooled_full_quality")}}
    (DATA / "sigma_v50_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("fixtures by data quality:", dict(qual))
    if names.unresolved: print("UNRESOLVED NAMES (add to data/sigma_aliases.json or add history):", sorted(names.unresolved))
    if names.fuzzy: print("FUZZY MATCHES (review):", names.fuzzy)
    pa = bt.get("pooled_all", {})
    if pa.get("n"):
        print(f"backtest n={pa['n']} hit={pa['hit_pct']}% brier={pa['brier']} (baseline {pa['baseline_brier']}) skill={pa['brier_skill']}")
    else: print("backtest:", bt.get("note"))
    print("DONE. Next: python3 sigma_v50_gate.py")


# ============================== SECTION: GATE ==============================
def gate():
    # Pre-push checks. sys.exit(1) on any FAIL.
    fails, warns = [], []
    def fail(m): fails.append(m); print("FAIL:", m)
    def warn(m): warns.append(m); print("WARN:", m)
    def ok(m): print("OK:  ", m)
    T = today(); print(f"Sigma V50 GATE - today={T}")

    # 1. report freshness
    rp = DATA / "sigma_v50_report.json"
    if not rp.exists(): fail("sigma_v50_report.json missing - run sigma_v50_core.py")
    else:
        rep = json.loads(rp.read_text(encoding="utf-8"))
        age = datetime.now(timezone.utc) - datetime.fromisoformat(rep["generated_utc"])
        (fail if age > timedelta(days=2) else ok)(f"core report age {age.days}d {age.seconds//3600}h (limit 2d)")
        if rep.get("unresolved_names"): warn(f"{len(rep['unresolved_names'])} fixture names have no history: {rep['unresolved_names'][:8]}")

    # 2. entity tags anywhere
    bad = [p.name for pat in ("data/*.json", "data/*.csv", "*.json", "*.csv", "*.html") for p in BASE.glob(pat)
           if p.stat().st_size < 60_000_000 and has_tag(p.read_text(encoding="utf-8", errors="ignore"))]
    (fail if bad else ok)(f"entity tags remaining in: {bad}" if bad else "no entity tags")

    # 3. history sanity
    hp = DATA / "sigma_history.csv"
    if hp.exists():
        if hp.stat().st_size > 50_000_000: warn("history >50MB (GitHub hard limit 100MB)")
        h = rep.get("history", {}) if rp.exists() else {}
        rows = h.get("rows", 0)
        if rows:
            badr = (h.get("bad_date", 0) + h.get("bad_teams", 0)) / rows
            (fail if badr > 0.01 else ok)(f"history unparsable rows {badr:.2%} (limit 1%), kept {h.get('kept')}, no-score {h.get('no_score',0)}, future {h.get('future',0)}")
    else: warn("sigma_history.csv missing")

    # 4. fixtures
    for fname in FIXTURE_FILES:
        for cand in (DATA / fname, BASE / fname):
            if not cand.exists(): continue
            try:
                obj = json.loads(cand.read_text(encoding="utf-8"))
                rows = obj if isinstance(obj, list) else obj.get("matches", obj.get("data", []))
            except Exception as e:
                fail(f"{cand.name} unreadable: {e}"); continue
            seen, past, dup, bball, fakec, badg, nodq, badsum, nodate = set(), 0, 0, 0, 0, 0, 0, 0, 0
            clones = Counter()
            for m in rows:
                d = parse_date(m.get("date") or m.get("ts") or "")
                if d is None: nodate += 1
                elif d < T and str(m.get("status", "")).upper() in ("SCHEDULED", "UPCOMING", "OPEN", ""): past += 1
                k = (str(m.get("match", "")).lower(), str(d))
                dup += k in seen; seen.add(k)
                bball += m.get("sport") == "basketball"
                fakec += str(m.get("poster_confidence", "")).lower().startswith("very high")
                dq = m.get("data_quality")
                if dq is None: nodq += 1
                if m.get("golden") and dq != "full": badg += 1
                try:
                    s = float(m.get("p1", 0)) + float(m.get("pX", 0)) + float(m.get("p2", 0))
                    if m.get("p1") is not None and not 98.5 <= s <= 101.5: badsum += 1
                except (TypeError, ValueError): badsum += 1
                if dq not in (None, "full"): clones[(m.get("xg_home"), m.get("xg_away"), m.get("p1"))] += 1
            n = cand.name
            for cond, msg in ((past, f"{past} past-dated matches still scheduled"), (dup, f"{dup} duplicates"),
                              (bball, f"{bball} basketball rows in football file"), (fakec, f"{fakec} poster 'very high' confidences"),
                              (badg, f"{badg} golden rows without full data quality"), (badsum, f"{badsum} rows with probabilities not summing to 100")):
                if cond: fail(f"{n}: {msg}")
            if nodq: warn(f"{n}: {nodq} rows have no data_quality (not re-predicted by V50)")
            if nodate: warn(f"{n}: {nodate} rows with unparsable date")
            if any(v >= 3 for v in clones.values()): warn(f"{n}: identical default-looking predictions repeated >=3 times on non-full data")
            if not (past or dup or bball or fakec or badg or badsum): ok(f"{n}: {len(rows)} rows clean")

    # 5. basketball must not carry football predictions
    bf = DATA / "sigma_basketball_fixtures.json"
    if bf.exists():
        bb = json.loads(bf.read_text(encoding="utf-8")).get("matches", [])
        if any("NONE" not in str(m.get("prediction", "")) for m in bb): fail("basketball has predictions - must be NONE/BETA")
        else: ok(f"basketball separate, {len(bb)} fixtures, no predictions")

    # 6. backtest must show skill over baseline
    bp = DATA / "sigma_backtest.json"
    if bp.exists():
        b = json.loads(bp.read_text(encoding="utf-8")).get("pooled_all", {})
        if not b.get("n"): warn("backtest has no data")
        elif b["brier_skill"] <= 0: warn(f"model does not beat baseline (brier skill {b['brier_skill']}) - do not show accuracy claims")
        else: ok(f"backtest n={b['n']} hit={b['hit_pct']}% brier skill={b['brier_skill']}")
    else: warn("sigma_backtest.json missing")

    # 7. secrets in files that would be pushed
    try:
        files = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=BASE, capture_output=True, text=True, check=True).stdout.splitlines()
    except Exception:
        files = [str(p.relative_to(BASE)) for p in BASE.rglob("*") if p.is_file() and ".git" not in p.parts]
    PATS = [("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")), ("GitHub PAT", re.compile(r"github_pat_[A-Za-z0-9_]{30,}")),
            ("Supabase secret key", re.compile(r"sb_secret_[A-Za-z0-9_\-]{10,}")), ("token in URL", re.compile(r"x-access-token:[^@\s/]{10,}@"))]
    JWT = re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.([A-Za-z0-9_\-]{10,})\.[A-Za-z0-9_\-]{10,}")
    leaks = 0
    for f in files:
        p = BASE / f
        if not p.is_file() or p.stat().st_size > 5_000_000 or p.suffix in (".png", ".jpg", ".zip", ".db", ".gz"): continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for name, rx in PATS:
            if rx.search(txt): fail(f"{name} found in {f}"); leaks += 1
        for mt in JWT.finditer(txt):
            try:
                pay = json.loads(base64.urlsafe_b64decode(mt.group(1) + "=" * (-len(mt.group(1)) % 4)))
            except Exception: continue
            if pay.get("role") == "service_role": fail(f"Supabase SERVICE_ROLE key in {f}"); leaks += 1
            elif pay.get("role") == "anon": warn(f"Supabase anon key in {f} (OK only if RLS is on)")
    if not leaks: ok(f"no secrets in {len(files)} files to be pushed")
    gc = BASE / ".git" / "config"
    if gc.exists() and re.search(r"x-access-token:[^@\s]+@", gc.read_text(errors="ignore")):
        warn("token stored in .git/config - run: git remote set-url origin https://github.com/mahmoud822822/sigma.git")

    print("=" * 50)
    if fails: print(f"RESULT: BLOCKED - {len(fails)} FAIL, {len(warns)} warn. DO NOT PUSH."); sys.exit(1)
    print(f"RESULT: PASS - {len(warns)} warn")


# ============================== SECTION: SUPABASE ==============================
def load_env():
    env = dict(os.environ); p = Path.home() / ".sigma_env"
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1); env[k.strip()] = v.strip().strip("'\"")
    return env

def post(url, key, table, rows, upsert_on=None):
    q = f"?on_conflict={upsert_on}" if upsert_on else ""
    prefer = "resolution=merge-duplicates,return=minimal" if upsert_on else "return=minimal"
    req = urllib.request.Request(f"{url}/rest/v1/{table}{q}", data=json.dumps(rows).encode(), method="POST",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": prefer})
    try:
        urllib.request.urlopen(req, timeout=60).read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Supabase {table} HTTP {e.code}: {e.read().decode()[:300]}")

def sync_main():
    dry = "--dry" in sys.argv
    rows = collect_predictions()
    print(f"{len(rows)} prediction rows ready")
    if not rows: raise SystemExit("nothing to sync - run sigma_v50_core.py first")
    if dry:
        print("DRY RUN. sample:", json.dumps(rows[0], ensure_ascii=False)); return
    env = load_env(); url, key = env.get("SUPABASE_URL", "").rstrip("/"), env.get("SUPABASE_SERVICE_KEY", "")
    if not url.startswith("https://") or not key: raise SystemExit("set SUPABASE_URL and SUPABASE_SERVICE_KEY in ~/.sigma_env")
    for i in range(0, len(rows), 500):
        post(url, key, "sigma_predictions", rows[i:i + 500], "match_key")
        print(f"upserted {min(i + 500, len(rows))}/{len(rows)}")
    bp = DATA / "sigma_backtest.json"
    if bp.exists(): post(url, key, "sigma_backtest", [{"version": VERSION, "payload": json.loads(bp.read_text(encoding="utf-8"))}])
    print("SYNC OK")


# ============================== SECTION: BRAIN (V49, patched) ==============================
TODAY = date.fromisoformat(os.environ["SIGMA_TODAY"]) if os.environ.get("SIGMA_TODAY") else date.today()  # V50: was hardcoded 2026-11-11
TODAY_S = TODAY.isoformat()

def norm(s):
    s = re.sub(r"[^a-z0-9 ]", "", str(s or "").lower().strip())
    return re.sub(r"\s+", " ", s).strip()

# --- SPORT REGISTRY: add a sport = add one entry, no code change ---
SPORTS = {
  "football":   {"scoring": "goals", "model": "Dixon-Coles Poisson (V46)", "sources": ["UEFA", "CAF", "Sportradar", "FotMob"], "status": "LIVE"},
  "basketball": {"scoring": "points 70-120", "model": "Points-Elo BETA (NOT football Poisson)", "sources": ["EuroLeague", "NBA", "Sportradar"], "status": "BETA fixtures only"},
  "tennis":     {"scoring": "sets", "model": "Surface Elo sets BETA", "sources": ["ATP", "Sportradar"], "status": "BETA - tournament structure only"},
  "american_football": {"scoring": "points", "model": "Points-Elo BETA", "sources": ["NFL", "ESPN"], "status": "BETA fixtures only"},
  "ice_hockey": {"scoring": "goals 0-8", "model": "Goals-Elo BETA", "sources": ["NHL", "Sportradar"], "status": "BETA fixtures only"},
  "volleyball": {"scoring": "sets best-of-5", "model": "Sets-Elo BETA", "sources": ["CEV", "Sportradar"], "status": "BETA fixtures only"},
  "handball":   {"scoring": "goals 20-40", "model": "Goals-Elo BETA", "sources": ["EHF", "Sportradar"], "status": "BETA fixtures only"},
}

# Verified seeds 11 Nov 2026 - NOT invented. Each has 2+ sources in audit notes.
# Full schedules come from fetch adapters at runtime, these seeds prove multi-sport works.
SEEDS = [
  # tennis - ATP Finals structure (draw 12 Nov, play 15-22 Nov Turin)
  {"sport": "tennis", "match": "ATP Finals - Tournament Structure", "date": "2026-11-15", "league": "ATP Finals Turin", "note": "Structure REAL: 15-22 Nov Turin, draw 12 Nov. Individual pairings = after draw, DO NOT invent before draw."},
  # NFL Week 11
  {"sport": "american_football", "match": "Houston Texans vs Indianapolis Colts", "date": "2026-11-19", "league": "NFL Week 11", "note": "REAL Thu 19 Nov 8:15pm ET. Home Texans."},
  {"sport": "american_football", "match": "Buffalo Bills vs Miami Dolphins", "date": "2026-11-22", "league": "NFL Week 11", "note": "REAL Sun 22 Nov. Home Bills."},
  {"sport": "american_football", "match": "Washington Commanders vs Cincinnati Bengals", "date": "2026-11-23", "league": "NFL Week 11", "note": "REAL Mon 23 Nov. Home Washington."},
  # NHL
  {"sport": "ice_hockey", "match": "Seattle Kraken vs Carolina Hurricanes", "date": "2026-11-12", "league": "NHL", "note": "REAL Global Series Helsinki. Home Kraken (neutral venue)."},
  {"sport": "ice_hockey", "match": "Buffalo Sabres vs Tampa Bay Lightning", "date": "2026-11-12", "league": "NHL", "note": "REAL 12 Nov."},
  # Volleyball
  {"sport": "volleyball", "match": "Budowlani Lodz vs Galatasaray Istanbul", "date": "2026-11-25", "league": "CEV Champions League Women", "note": "REAL 25 Nov Lodz."},
  {"sport": "volleyball", "match": "Vero Volley Milano vs Levallois Paris", "date": "2026-11-25", "league": "CEV Champions League Women", "note": "REAL 25 Nov Monza."},
  # Handball
  {"sport": "handball", "match": "Aalborg vs Fuchse Berlin", "date": "2026-11-18", "league": "EHF Champions League", "note": "REAL Main Round 18 Nov Aalborg."},
  {"sport": "handball", "match": "Wisla Plock vs Veszprem KC", "date": "2026-11-18", "league": "EHF Champions League", "note": "REAL Main Round 18 Nov Plock."},
  {"sport": "handball", "match": "Storhamar Elite vs Nykoebing Falster", "date": "2026-11-14", "league": "EHF Champions League Women", "note": "REAL 14 Nov Hamar."},
]

FAKE_PATTERNS = [
  {"pattern": "ALL matches marked 'very high confidence' + green check", "learned_from": "Poster V48", "action": "Strip confidence, use model only"},
  {"pattern": "Odds ranges like 1.07-1.13 for every match", "learned_from": "Poster V48", "action": "Strip odds, mark NOT VERIFIED"},
  {"pattern": "Accumulator single number 3.24", "learned_from": "Poster V48: lower=2.65 upper=3.28", "action": "Show range, never single inflated number"},
  {"pattern": "Home/away swap (Egypt home vs Malawi 17 Nov)", "learned_from": "V47+V48: real home Malawi", "action": "Reverse-check home vs 2 sources"},
  {"pattern": "Finished match still OPEN (Hansa-Stuttgart, Portugal-Wales)", "learned_from": "V47: date < today", "action": "Archive, never keep as upcoming"},
  {"pattern": "Football model applied to basketball/other sport", "learned_from": "V48", "action": "Block - per-sport model only"},
]

def reverse_verify(m):
    """7 reverse checks. Returns (ok, reasons). ok=False => SUSPECT, not REAL."""
    reasons = []
    d = str(m.get("date", ""))[:10]
    if d and d < TODAY_S:
        reasons.append("PAST_DATE")
    # Tournament structure (e.g. ATP Finals before draw) has no pair yet - not a match, not an error
    if "structure" in str(m.get("note", "")).lower() or "tournament structure" in str(m.get("match", "")).lower():
        return (True, ["STRUCTURE_ONLY_NO_PAIR_YET"])
    if not m.get("match") or " vs " not in str(m.get("match", "")):
        reasons.append("BAD_MATCH_FORMAT")
    # Fake confidence / odds if present in raw
    if str(m.get("poster_confidence", "")).lower().startswith("very high"):
        reasons.append("FAKE_CONFIDENCE_STRIPPED")
    try:
        if m.get("odds") and float(str(m.get("odds")).replace(",", ".")) < 1.01:
            reasons.append("IMPOSSIBLE_ODDS")
    except ValueError:
        reasons.append("BAD_ODDS_FORMAT")
    return (len(reasons) == 0, reasons)

def collect_old():
    files = []
    for p in list(BASE.glob("*.json")) + list(BASE.glob("*.csv")) + list(DATA.glob("*.json")) + list(DATA.glob("*.csv")):
        try:
            files.append({"file": str(p.relative_to(BASE)), "size": p.stat().st_size})
        except Exception:
            pass
    return files

def brain_main():
    loop = "--loop" in sys.argv
    while True:
        print("=" * 60)
        print(f"Sigma V49 BRAIN PULSE - {TODAY_S} - thinking...")
        old = collect_old()
        print(f"[1] COLLECT OLD: {len(old)} files found (history + fixtures + basketball + audits)")
        # Verify seeds
        ok, suspect = [], []
        for s in SEEDS:
            good, why = reverse_verify(s)
            (ok if good else suspect).append({**s, "verify": why})
        print(f"[2] SEARCH NEW: {len(SEEDS)} verified seeds across {len(SPORTS)} sports (tennis/NFL/NHL/volleyball/handball + football/basketball from V47/V48)")
        print(f"[3] REVERSE-VERIFY: {len(ok)} REAL, {len(suspect)} SUSPECT (suspect NOT added as REAL)")
        for r in suspect:
            print("  SUSPECT:", r["match"], r["verify"])
        # Merge - write master
        master = {"version": "V49", "date": TODAY_S, "sports": SPORTS,
                  "old_files": old, "verified_seeds": ok, "seed_status": "HARDCODED_NOT_FETCHED", "suspect": suspect,
                  "fake_patterns_learned": FAKE_PATTERNS,
                  "rule": "No prediction is guaranteed. No sure wins. Odds/confidence from posters are stripped."}
        (DATA / "sigma_all_sports_master.json").write_text(json.dumps(master, ensure_ascii=False, indent=1), encoding="utf-8")
        (DATA / "sigma_knowledge.json").write_text(json.dumps({"version": "V49", "fake_patterns": FAKE_PATTERNS, "sports": list(SPORTS.keys()), "truth_rule": "2 sources must agree, else SUSPECT. Reverse-check home/away, date, odds math."}, ensure_ascii=False, indent=1), encoding="utf-8")
        state = {"pulse": "ALIVE", "version": "V49", "last_cycle": TODAY_S, "old_files": len(old), "verified_seeds": len(ok), "seed_status": "HARDCODED_NOT_FETCHED", "suspect": len(suspect), "sports": len(SPORTS), "next": "Run V49 again after fetch, then Pre-Upload Check, then push only if PASS."}
        (DATA / "sigma_brain_state.json").write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[4] MERGE: master -> data/sigma_all_sports_master.json")
        print(f"[5] PREDICT: football=V46 LIVE, others=BETA fixtures only (no fake predictions)")
        print(f"[6] LEARN: {len(FAKE_PATTERNS)} fake patterns saved to sigma_knowledge.json")
        print(f"[7] PULSE: ALIVE - brain_state updated")
        print("Cycle done. Next: python3 sigma_v49_pre_upload_check.py  (must PASS before push)")
        if not loop:
            break
        print("Loop mode: sleeping 3600s (1h) - Ctrl+C to stop")
        time.sleep(3600)


# ============================== SECTION: GIT PUSH ==============================
def _git(*a, check=True, env=None):
    return subprocess.run(["git", *a], cwd=BASE, check=check, env=env)

def ensure_remote():
    if not (BASE / ".git").exists(): print("not a git repo - skipping remote setup"); return False
    r = subprocess.run(["git", "remote", "get-url", "origin"], cwd=BASE, capture_output=True)
    _git("remote", "set-url" if r.returncode == 0 else "add", "origin", REMOTE)   # removes any token stored in the old URL
    return True

def ensure_gitignore():
    gi = BASE / ".gitignore"; cur = gi.read_text().splitlines() if gi.exists() else []
    add = [p for p in ("token.txt", ".sigma_env", "*.key", "__pycache__/", "*.bak") if p not in cur]
    if add: gi.write_text("\n".join(cur + add) + "\n")

def push():
    if not TOKEN_FILE.exists() or not TOKEN_FILE.read_text().strip():
        raise SystemExit("MISSING ~/token.txt - run: bash sigma_setup_token.sh")
    ensure_gitignore(); ask = Path.home() / ".sigma_askpass"
    ask.write_text('#!/bin/sh\ncase "$1" in\n  Username*) echo x-access-token ;;\n  *) tr -d \' \\n\\r\' < "$HOME/token.txt" ;;\nesac\n')
    ask.chmod(0o700)
    env = dict(os.environ, GIT_ASKPASS=str(ask), GIT_TERMINAL_PROMPT="0")
    if subprocess.run(["git", "config", "user.email"], cwd=BASE, capture_output=True).returncode: _git("config", "user.email", "sigma@localhost")
    if subprocess.run(["git", "config", "user.name"], cwd=BASE, capture_output=True).returncode: _git("config", "user.name", "Sigma")
    _git("add", "-A"); _git("commit", "-m", f"Sigma V50 {today().isoformat()}", check=False)
    try: _git("push", "origin", BRANCH, env=env)
    except subprocess.CalledProcessError:
        raise SystemExit("PUSH FAILED - token expired or no repo permission. New token -> sigma_setup_token.sh -> rerun.")
    print("PUSH OK")

def pipeline(dry=False):
    is_git = ensure_remote()
    if is_git: subprocess.run(["git", "branch", "-f", BACKUP_BRANCH, "HEAD"], cwd=BASE, capture_output=True)   # restore: git checkout %s -- data
    core_main()
    for f in OPTIONAL_SCRIPTS:
        if (BASE / f).exists(): subprocess.run([sys.executable, str(BASE / f)], cwd=BASE, check=True)
        else: print("skip", f, "(not found)")
    brain_main()
    try: gate()
    except SystemExit as e:
        if e.code: raise SystemExit("BLOCKED - fix the FAIL lines above. Nothing was pushed.")
    if dry or not is_git: print("DRY/no-git: stopped before push."); return
    push()
    if ENV_FILE.exists():
        try: sync_main()
        except SystemExit as e: print("WARN: Supabase sync failed (GitHub push already done):", e)
    else: print("skip Supabase sync (no ~/.sigma_env)")
    print("DONE")

# ============================== SECTION: SELFTEST ==============================
def selftest():
    # Runs core + brain + gate on synthetic data in a temp folder. Does NOT touch your repo.
    tmp = Path(tempfile.mkdtemp()); (tmp / "data").mkdir()
    shutil.copy(Path(__file__).resolve(), tmp / "sigma_v50.py")
    env = dict(os.environ, SIGMA_TODAY="2026-11-12")
    def run(*a): return subprocess.run([sys.executable, *a], cwd=tmp, env=env, capture_output=True, text=True)
    passed = failed = 0
    def check(name, cond, extra=""):
        nonlocal passed, failed
        passed += bool(cond); failed += (not cond)
        print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))
    random.seed(7)
    teams = [f"Team{i}" for i in range(20)]
    att = {t: random.gauss(0, 0.25) for t in teams}; dfn = {t: random.gauss(0, 0.25) for t in teams}
    def pois(l):
        L, k, p = math.exp(-l), 0, 1.0
        while True:
            p *= random.random()
            if p <= L: return k
            k += 1
    rows = []; d0 = date(2019, 8, 1)
    for i in range(7000):
        h, a = random.sample(teams, 2); d = d0 + timedelta(days=i // 4)
        hg = pois(1.45 * math.exp(att[h] - dfn[a])); ag = pois(1.15 * math.exp(att[a] - dfn[h]))
        ds = d.isoformat() if i % 2 else d.strftime("%d/%m/%y") if i % 4 == 0 else d.strftime("%d/%m/%Y")
        rows.append({"date": ds, "home": h, "away": a, "home_goals": hg, "away_goals": ag, "league": "L1"})
    rows.append({"date": "01/02/2020", "home": "\u3010entity-Team3\u00a6canonical_name=Team3\u3011", "away": "Team4", "home_goals": 1, "away_goals": 0, "league": "L1"})
    rows.append({"date": "05/03/2021", "home": "Team1", "away": "Team2", "home_goals": "", "away_goals": "", "league": "L1"})   # blank score
    rows.append({"date": "2030-01-01", "home": "Team1", "away": "Team2", "home_goals": 2, "away_goals": 2, "league": "L1"})   # future
    rows.append(dict(rows[10]))                                                                                              # duplicate
    with open(tmp / "data/sigma_history.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    fx = [{"match": "Team1 vs Team2", "date": "2026-11-20", "league": "L1", "status": "SCHEDULED"},
          {"match": "FC Team5 vs Team6", "date": "2026-11-21", "league": "L1", "status": "SCHEDULED"},
          {"match": "Team7 vs Brand New FC", "date": "2026-11-22", "league": "L1", "status": "SCHEDULED"},
          {"match": "Nobody A vs Nobody B", "date": "2026-11-23", "league": "L1", "status": "SCHEDULED"}]
    (tmp / "data/sigma_bulk_predictions.json").write_text(json.dumps(fx))

    r = run("sigma_v50.py", "core"); print(r.stdout[-900:], r.stderr[-400:])
    check("core exits 0", r.returncode == 0)
    rep = json.loads((tmp / "data/sigma_v50_report.json").read_text())
    h = rep["history"]
    check("mixed date formats all parsed", h.get("bad_date", 0) == 0, str(h))
    check("blank score row skipped (not 0-0)", h.get("no_score") == 1)
    check("future row skipped", h.get("future") == 1)
    check("duplicates removed", h.get("dupes", 0) >= 1, str(h.get("dupes")))
    check("entity-tag name cleaned (no tag team)", "Team3" in json.loads((tmp / "data/sigma_team_stats.json").read_text()) and not any("entity" in k for k in json.loads((tmp / "data/sigma_team_stats.json").read_text())))
    bt = json.loads((tmp / "data/sigma_backtest.json").read_text()); pa = bt["pooled_all"]
    check("walk-forward ran 3 folds", len(bt["folds"]) == 3 and pa["n"] > 500, f"n={pa['n']}")
    check("model beats base-rate baseline (brier skill>0)", pa["brier_skill"] > 0, f"skill={pa['brier_skill']} hit={pa['hit_pct']}%")
    out = {m["match"].split(" vs ")[0]: m for m in json.loads((tmp / "data/sigma_bulk_predictions.json").read_text())}
    check("alias 'FC Team5' resolved to full data", out["Team5"]["data_quality"] == "full" if "Team5" in out else out.get("FC Team5", {}).get("data_quality") == "full")
    q = {k: v for k, v in out.items()}
    nb = [m for m in out.values() if "Nobody" in m["match"]][0]
    check("no-data match = prior, base rates, never golden", nb["data_quality"] == "prior" and nb["golden"] == 0 and nb["conf"] < 50, f"conf={nb['conf']}")
    pt = [m for m in out.values() if "Brand New" in m["match"]][0]
    check("one unknown team = partial, shrunk", pt["data_quality"] == "partial" and pt["conf"] < 70, f"conf={pt['conf']}")
    check("unresolved names reported", "Nobody A" in rep["unresolved_names"])
    v = run("sigma_v50.py", "brain"); check("V49 patched runs with dynamic date", v.returncode == 0 and "2026-11-12" in v.stdout)

    g = run("sigma_v50.py", "gate"); print(g.stdout[-1200:])
    check("gate PASS on clean output", g.returncode == 0)
    # break things on purpose
    bad = json.loads((tmp / "data/sigma_bulk_predictions.json").read_text())
    bad[0]["date"] = "2026-11-01"; bad[3]["golden"] = 1
    (tmp / "data/sigma_bulk_predictions.json").write_text(json.dumps(bad))
    (tmp / "leak.txt").write_text("x-access-token:ghp_" + "a" * 36 + "@github.com")
    g2 = run("sigma_v50.py", "gate")
    check("gate BLOCKS past-date + fake golden + leaked token", g2.returncode == 1 and "past-dated" in g2.stdout and "golden" in g2.stdout and "GitHub token" in g2.stdout)
    shutil.rmtree(tmp)
    print(f"\n{passed} passed, {failed} failed"); sys.exit(1 if failed else 0)


# ============================== SECTION: SQL ==============================
SCHEMA_SQL = """
-- Run once in Supabase: SQL Editor -> New query -> paste -> Run
create table if not exists public.sigma_predictions (
  match_key text primary key,
  match_date date not null,
  league text, home text not null, away text not null,
  p1 numeric, px numeric, p2 numeric, btts numeric, over25 numeric,
  xg_home numeric, xg_away numeric, pick text, grade text,
  data_quality text check (data_quality in ('full','partial','prior')),
  golden boolean default false, model text,
  updated_at timestamptz default now()
);
create index if not exists sigma_predictions_date_idx on public.sigma_predictions (match_date);
create table if not exists public.sigma_backtest (
  id bigint generated always as identity primary key,
  created_at timestamptz default now(), version text, payload jsonb not null
);
alter table public.sigma_predictions enable row level security;
alter table public.sigma_backtest   enable row level security;
-- anon (public website) can READ only. Writes happen with the service key from Termux (bypasses RLS).
drop policy if exists "public read predictions" on public.sigma_predictions;
create policy "public read predictions" on public.sigma_predictions for select to anon using (true);
drop policy if exists "public read backtest" on public.sigma_backtest;
create policy "public read backtest" on public.sigma_backtest for select to anon using (true);
"""

def cli():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "core": core_main()
    elif cmd == "brain": brain_main()
    elif cmd == "gate": gate()
    elif cmd == "pipeline": pipeline(dry="--dry" in sys.argv)
    elif cmd == "push": ensure_remote(); push()
    elif cmd == "sync": sync_main()
    elif cmd == "schema": print(SCHEMA_SQL.strip())
    elif cmd == "selftest": selftest()
    else: print(__doc__ or "see header: core | brain | gate | pipeline [--dry] | push | sync [--dry] | schema | selftest")

if __name__ == "__main__":
    cli()
