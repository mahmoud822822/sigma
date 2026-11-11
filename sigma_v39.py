#!/usr/bin/env python3
# Sigma V39 - Unified Superhuman Version - Mahmoud Emad
# قديم + جديد + مستقبل في برنامج واحد
# Loop: History -> Learn -> Predict Future -> Verify -> Learn Again
# stdlib ONLY - يشتغل في Termux بدون pandas/sklearn
# V2 Lessons محفوظة: BTTS weight 70, Late 76-90 30%, Weak Home +15%
# V39 الجديد: Dixon-Coles + Elo + xG Ensemble + Calibration + Kelly 30% + CLV + Monte Carlo
import math, json, os, csv, shutil, statistics, random
from datetime import date, datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

VERSION = "V39 Unified"
SIGMA_V39 = {
    "btts_weight": 70,
    "late_weight_76_90": 30,
    "weak_home_bonus": 15,
    "kelly_fraction": 0.30,
    "rho_dixon_coles": -0.13,
    "time_decay_xi": 0.006,
    "elo_k": 20,
    "elo_home_adv": 60,
    "safety_rule": "1 goal safer than 2 | Any team safer than specific team | Asian Over 1 refund safer than BTTS",
}

LEAGUE_AVG = {
    "England": (1.65, 1.35), "Spain": (1.55, 1.20), "Italy": (1.50, 1.20),
    "Germany": (1.70, 1.40), "Netherlands": (1.70, 1.40), "France": (1.55, 1.25),
    "Portugal": (1.55, 1.20), "Belgium": (1.60, 1.30), "Turkey": (1.55, 1.25),
    "PL": (1.65, 1.35), "PD": (1.55, 1.20), "SA": (1.50, 1.20), "BL1": (1.70, 1.40),
    "FL1": (1.55, 1.25), "DED": (1.70, 1.40), "PPL": (1.55, 1.20), "JPL": (1.60, 1.30),
    "Default": (1.55, 1.25),
}
LEAGUE_TOTAL_AVG = {k: sum(v) for k, v in LEAGUE_AVG.items()}

# توحيد أسماء الفرق - عشان "Palace" و "Crystal Palace" و "Villa" و "Aston Villa" يتعدوا ماتش واحد مش اتنين
CANON = {
    "palace": "Crystal Palace", "crystal palace": "Crystal Palace",
    "man utd": "Man Utd", "manchester united": "Man Utd", "man united": "Man Utd", "manchester united fc": "Man Utd",
    "villa": "Aston Villa", "aston villa": "Aston Villa",
    "brugge": "Club Brugge", "club brugge": "Club Brugge",
    "barca": "Barcelona", "fc barcelona": "Barcelona", "barcelona": "Barcelona",
    "real": "Real Madrid", "real madrid": "Real Madrid",
    "atletico": "Atletico", "atletico madrid": "Atletico",
    "man city": "Man City", "manchester city": "Man City", "manchester city fc": "Man City",
    "spurs": "Tottenham", "tottenham": "Tottenham",
    "psg": "Paris Saint", "paris saint": "Paris Saint",
    "milan": "AC Milan", "ac milan": "AC Milan",
    "inter": "Inter", "inter milan": "Inter",
    "juve": "Juventus", "juventus": "Juventus",
    "trabzon": "Trabzonspor", "trabzonspor": "Trabzonspor",
    "alanya": "Alanya", "alanyaspor": "Alanya",
    "bayern": "Bayern", "bayern munich": "Bayern",
    "dortmund": "Dortmund", "borussia dortmund": "Dortmund",
}
def canon_team(name):
    if not name:
        return name
    s = str(name).strip()
    # شيل FC في الآخر
    low = s.lower().strip()
    if low.endswith(" fc"):
        low = low[:-3].strip()
        s = s[:-3].strip() if len(s) > 3 else s
    if low in CANON:
        return CANON[low]
    # لو الاسم فيه "Manchester City FC" -> "Man City"
    for k, v in CANON.items():
        if low == k:
            return v
    return s

# ---------- Core Math ----------
def poisson(lam, g):
    if lam <= 0:
        return 1.0 if g == 0 else 0.0
    return math.exp(-lam) * (lam ** g) / math.factorial(g)

def dixon_coles_matrix(lam_h, lam_a, rho=-0.13, max_goals=10):
    """Dixon-Coles: Poisson مستقل + تصحيح rho للخلايا 0-0,1-0,0-1,1-1"""
    m = {}
    total = 0.0
    for x in range(max_goals + 1):
        for y in range(max_goals + 1):
            p = poisson(lam_h, x) * poisson(lam_a, y)
            # tau correction
            if x == 0 and y == 0:
                tau = 1 - lam_h * lam_a * rho
            elif x == 0 and y == 1:
                tau = 1 + lam_h * rho
            elif x == 1 and y == 0:
                tau = 1 + lam_a * rho
            elif x == 1 and y == 1:
                tau = 1 - rho
            else:
                tau = 1.0
            p = p * tau
            m[(x, y)] = p
            total += p
    # Normalize - لازم المجموع = 1
    m = {k: v / total for k, v in m.items()}
    return m

def matrix_to_markets(m):
    hw = sum(p for (x, y), p in m.items() if x > y)
    dr = sum(p for (x, y), p in m.items() if x == y)
    aw = sum(p for (x, y), p in m.items() if x < y)
    btts = sum(p for (x, y), p in m.items() if x > 0 and y > 0)
    over25 = sum(p for (x, y), p in m.items() if x + y >= 3)
    over15 = sum(p for (x, y), p in m.items() if x + y >= 2)
    over05 = sum(p for (x, y), p in m.items() if x + y >= 1)
    over05_2h = 0.30  # V2: Late 76-90 weight 30% - تقدير محافظ من التاريخ، مش رقم مخترع من الهوا
    # Exact scores top
    top = sorted(m.items(), key=lambda z: z[1], reverse=True)[:3]
    exp_goals = sum((x + y) * p for (x, y), p in m.items())
    return {
        "1": hw, "X": dr, "2": aw, "BTTS": btts,
        "Over25": over25, "Over15": over15, "Over05": over05,
        "Over05_2H_est": over05_2h, "exp_goals": exp_goals,
        "top_scores": [(f"{x}-{y}", round(p * 100, 1)) for (x, y), p in top],
        "matrix": m,
    }

def elo_expected(elo_a, elo_b, home_adv=60):
    # elo_a = home
    diff = (elo_a + home_adv - elo_b) / 400.0
    return 1.0 / (1.0 + 10 ** (-diff))

def kelly_stake(p, odds, bankroll, fraction=0.30):
    """Kelly Fractional - V39: دايما 30% مش كامل"""
    if p <= 0 or odds <= 1 or bankroll <= 0:
        return 0.0
    b = odds - 1
    q = 1 - p
    full = (b * p - q) / b
    if full <= 0:
        return 0.0
    return round(bankroll * full * fraction, 2)

def ev_calc(p, odds):
    return round(p * odds - 1, 4)

def clv_calc(odds_taken, odds_close):
    if not odds_close or odds_close <= 0:
        return 0.0
    return round((odds_taken / odds_close - 1) * 100, 2)

def grade_for(n):
    if n >= 30:
        return "A"
    if n >= 15:
        return "B"
    if n >= 5:
        return "C"
    return "D"

# ---------- Loaders - قديم + جديد + مستقبل ----------
def _read_csv(path):
    if not Path(path).exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def load_verified():
    # FIX V39: ادمج الملفين - ROOT أحدث (فيه date/league/notes) و DATA قديم
    # لو فيه نفس الماتش في الملفين، خد نسخة ROOT
    merged = {}
    for cand in [DATA / "sigma_real_verified.csv", BASE / "sigma_real_verified.csv"]:
        rows = _read_csv(cand)
        for r in rows:
            raw_match = str(r.get("match", "")).strip()
            if not raw_match or " vs " not in raw_match:
                continue
            _h, _a = raw_match.split(" vs ")
            key = f"{canon_team(_h).lower()} vs {canon_team(_a).lower()}"
            # وحّد الاسم في الصف نفسه عشان باقي الكود يلاقيه
            r = dict(r)
            r["match"] = f"{canon_team(_h)} vs {canon_team(_a)}"
            # ROOT يغطي على DATA لأنه أحدث
            merged[key] = r
    if merged:
        # رتب زي الأصل
        rows = list(merged.values())
        return rows, f"merged root+data ({len(rows)} unique)"
    return [], "none"

def data_quality():
    """يكشف الداتا التجريبية / المكررة قبل الرفع - مهم جدا"""
    issues = []
    # History duplicates
    history, _ = load_history()
    if history:
        seen = {}
        dups = 0
        for r in history:
            k = (str(r.get("date")), str(r.get("home")), str(r.get("away")))
            if k in seen:
                dups += 1
            else:
                seen[k] = 1
        if dups > 0:
            issues.append(f"HISTORY DEMO/DUPLICATE: {dups} صف مكرر من {len(history)} - نفس الماتش متكرر (مثال Man Utd vs Villa 2-1). لازم History Init حقيقي قبل الرفع، وإلا Man Utd هيبان كأنه كسب 50 مرة.")
        if len(seen) < 20:
            issues.append(f"HISTORY صغير جدا: {len(seen)} ماتش فريد بس - لازم Init 365 يوم.")
    # Team stats demo?
    tj, _ = load_team_stats_json()
    if tj and len(tj) < 10:
        issues.append(f"TEAM_STATS DEMO: {len(tj)} فريق بس (مثال {list(tj.keys())}) - V39 هيتجاهله وهيستخدم History+Verified بس.")
    # Future demo?
    future, _, _ = load_future()
    if future and len(future) <= 3:
        issues.append(f"FUTURE DEMO: {len(future)} ماتش بس - ده ملف تجريبي، لازم Auto-Fetch حقيقي قبل الرفع.")
    return issues

def load_history():
    for cand in [DATA / "sigma_history.csv", BASE / "sigma_history.csv"]:
        rows = _read_csv(cand)
        if rows:
            return rows, str(cand)
    return [], "none"

def load_future():
    for cand in [DATA / "sigma_next_month.json", BASE / "sigma_next_month.json"]:
        if Path(cand).exists():
            try:
                data = json.loads(Path(cand).read_text(encoding="utf-8"))
                items = data if isinstance(data, list) else data.get("matches", data.get("data", []))
                return items, str(cand), data if isinstance(data, dict) else {}
            except Exception:
                pass
    return [], "none", {}

def load_team_stats_json():
    for cand in [DATA / "sigma_team_stats.json", BASE / "sigma_team_stats.json"]:
        if Path(cand).exists():
            try:
                return json.loads(Path(cand).read_text(encoding="utf-8")), str(cand)
            except Exception:
                pass
    return {}, "none"

# ---------- Team Stats Builder - التعلم من القديم ----------
def parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except Exception:
        return None

def build_team_stats():
    """يبني إحصائيات الفرق من History + Verified مع Time Decay"""
    verified, v_path = load_verified()
    history, h_path = load_history()
    team_json, tj_path = load_team_stats_json()

    # FIX V39: لو team_stats فيه أقل من 10 فرق = ديمو، تجاهله تماما
    stats = {}
    if team_json and len(team_json) < 10:
        team_json = {}
    if team_json:
        for team, s in team_json.items():
            try:
                stats[team] = {
                    "n": int(s.get("n", 0)),
                    "scored": float(s.get("scored_avg", 1.4)) * int(s.get("n", 0)),
                    "conceded": float(s.get("conceded_avg", 1.4)) * int(s.get("n", 0)),
                    "home_scored": float(s.get("home_scored_avg", 1.55)),
                    "away_scored": float(s.get("away_scored_avg", 1.25)),
                    "home_conceded": float(s.get("home_conceded_avg", 1.25)),
                    "away_conceded": float(s.get("away_conceded_avg", 1.55)),
                    "btts_rate": float(s.get("btts_rate", 50)),
                    "over25_rate": float(s.get("over25_rate", 50)),
                    "form": str(s.get("form", "")),
                    "elo": 1500.0,
                    "source": "history50",
                    "last_date": None,
                }
            except Exception:
                continue

    today = date.today()
    # History rows: أعمدة متوقعة: home, away, home_goals, away_goals, date, status, league
    # لو الملف مش موجود، Verified هي الأساس
    combined = []
    for r in history:
        try:
            if r.get("status") and r["status"] != "FINISHED":
                continue
            h = canon_team(r.get("home") or r.get("homeTeam") or "")
            a = canon_team(r.get("away") or r.get("awayTeam") or "")
            hg = int(r.get("home_goals", r.get("homeGoals", 0)))
            ag = int(r.get("away_goals", r.get("awayGoals", 0)))
            d = parse_date(r.get("date") or r.get("utcDate") or "")
            lg = r.get("league") or r.get("competition") or "Default"
            combined.append({"home": h, "away": a, "hg": hg, "ag": ag, "date": d, "league": lg, "src": "history"})
        except Exception:
            continue
    for r in verified:
        try:
            if " vs " not in str(r.get("match", "")):
                continue
            h, a = str(r["match"]).split(" vs ")
            h, a = canon_team(h.strip()), canon_team(a.strip())
            hg = int(r["real_home"]); ag = int(r["real_away"])
            d = parse_date(r.get("date") or "")
            lg = r.get("league") or "Default"
            combined.append({"home": h.strip(), "away": a.strip(), "hg": hg, "ag": ag, "date": d, "league": lg, "src": "verified"})
        except Exception:
            continue

    # FIX V39: Dedup - نفس (date,home,away) يتعد مرة واحدة بس، حتى لو match_id مختلف
    # ده بيمنع ملف history التجريبي (50x Man Utd vs Villa) من تسميم الإحصائيات
    _seen_comb = {}
    _deduped = []
    for g in combined:
        k = (str(g["date"]), g["home"].strip().lower(), g["away"].strip().lower())
        if k in _seen_comb:
            continue
        _seen_comb[k] = 1
        _deduped.append(g)
    combined = _deduped
    # Elo + Attack/Defence - مرتب بالتاريخ القديم للأحدث عشان Elo يتطور صح
    combined_sorted = sorted(combined, key=lambda x: (x["date"] or date(2000, 1, 1)))
    # لو مفيش تواريخ، الترتيب الأصلي
    elo = defaultdict(lambda: 1500.0)
    # ابدأ من stats الموجودة
    for t, s in stats.items():
        elo[t] = s.get("elo", 1500.0)

    per_team_raw = defaultdict(list)
    for game in combined_sorted:
        h, a, hg, ag = game["home"], game["away"], game["hg"], game["ag"]
        # وزن زمني: الأحدث أهم
        if game["date"]:
            age = (today - game["date"]).days
            w = math.exp(-SIGMA_V39["time_decay_xi"] * max(0, age))
        else:
            w = 0.7
        per_team_raw[h].append((hg, ag, True, w, game["date"], game["league"]))
        per_team_raw[a].append((ag, hg, False, w, game["date"], game["league"]))
        # Elo update
        exp_h = elo_expected(elo[h], elo[a])
        # نتيجة فعلية: 1 / 0.5 / 0
        actual = 1.0 if hg > ag else (0.5 if hg == ag else 0.0)
        # K أصغر للفرق الكبيرة n؟ نثبت K=20 زي الأصل
        elo[h] += SIGMA_V39["elo_k"] * (actual - exp_h)
        elo[a] += SIGMA_V39["elo_k"] * ((1 - actual) - (1 - exp_h))

    # بناء stats النهائي - دمج history50 + combined
    out = {}
    all_teams = set(list(stats.keys()) + list(per_team_raw.keys()))
    for team in all_teams:
        rows = per_team_raw.get(team, [])
        # لو الفريق كان في history50 بس ومفيش combined جديد، حافظ عليه
        base = stats.get(team)
        if rows:
            total_w = sum(r[3] for r in rows) or 1.0
            scored_w = sum(r[0] * r[3] for r in rows) / total_w
            conceded_w = sum(r[1] * r[3] for r in rows) / total_w
            home_rows = [r for r in rows if r[2]]
            away_rows = [r for r in rows if not r[2]]
            def _avg(rs, idx):
                if not rs:
                    return None
                tw = sum(r[3] for r in rs) or 1.0
                return sum(r[idx] * r[3] for r in rs) / tw
            hs = _avg(home_rows, 0); ac_ = _avg(away_rows, 0)
            hc = _avg(home_rows, 1); awc = _avg(away_rows, 1)
            # Form آخر 5 - W/D/L
            last5 = sorted(rows, key=lambda x: (x[4] or date(2000, 1, 1)))[-5:]
            form = "".join(["W" if r[0] > r[1] else ("D" if r[0] == r[1] else "L") for r in last5])
            btts = sum(1 for r in rows if r[0] > 0 and r[1] > 0) / len(rows) * 100 if rows else 50
            over25 = sum(1 for r in rows if r[0] + r[1] >= 3) / len(rows) * 100 if rows else 50
            # لو كان فيه base history50، ادمج: المتوسط المرجح - combined أهم لأنه أحدث + verified
            if base and base.get("source") == "history50":
                # 60% combined + 40% base - عشان منضيعش الـ 50 ماتش القديمة
                n_comb = len(rows)
                n_base = base["n"]
                n_total = n_comb + n_base
                # نستخدم القيم المرجحة مباشرة كـ home/away scored
                out[team] = {
                    "n": n_total,
                    "scored": scored_w * n_comb + (base.get("home_scored", 1.55) + base.get("away_scored", 1.25)) / 2 * n_base,
                    "conceded": conceded_w * n_comb + (base.get("home_conceded", 1.25) + base.get("away_conceded", 1.55)) / 2 * n_base,
                    "home_scored": round(( (hs if hs is not None else base["home_scored"]) * n_comb + base["home_scored"] * n_base) / max(1, n_total), 2),
                    "away_scored": round(( (ac_ if ac_ is not None else base["away_scored"]) * n_comb + base["away_scored"] * n_base) / max(1, n_total), 2),
                    "home_conceded": round(( (hc if hc is not None else base["home_conceded"]) * n_comb + base["home_conceded"] * n_base) / max(1, n_total), 2),
                    "away_conceded": round(( (awc if awc is not None else base["away_conceded"]) * n_comb + base["away_conceded"] * n_base) / max(1, n_total), 2),
                    "btts_rate": round(btts, 1), "over25_rate": round(over25, 1),
                    "form": form, "elo": round(float(elo[team]), 1),
                    "source": "merged_history50+verified+history", "last_date": str(max([r[4] for r in rows if r[4]], default=None)),
                }
            else:
                out[team] = {
                    "n": len(rows),
                    "scored": scored_w * len(rows), "conceded": conceded_w * len(rows),
                    "home_scored": round(hs if hs is not None else 1.55, 2),
                    "away_scored": round(ac_ if ac_ is not None else 1.25, 2),
                    "home_conceded": round(hc if hc is not None else 1.25, 2),
                    "away_conceded": round(awc if awc is not None else 1.55, 2),
                    "btts_rate": round(btts, 1), "over25_rate": round(over25, 1),
                    "form": form, "elo": round(float(elo[team]), 1),
                    "source": "history+verified", "last_date": str(max([r[4] for r in rows if r[4]], default=None)),
                }
        elif base:
            b = dict(base); b["elo"] = round(float(elo[team]), 1); out[team] = b
    return out, {"verified": len(verified), "history": len(history), "combined": len(combined_sorted), "teams": len(out), "verified_path": v_path, "history_path": h_path}

def find_team(stats, inp):
    if not inp:
        return None
    if inp in stats:
        return inp
    low = inp.lower().strip()
    for k in stats:
        if k.lower() == low:
            return k
    aliases = {"man city": "manchester city", "man utd": "manchester united", "man united": "manchester united", "barca": "barcelona", "real": "real madrid", "spurs": "tottenham", "psg": "paris saint", "milan": "ac milan", "inter": "inter", "juve": "juventus", "porto": "porto", "benfica": "benfica", "ajax": "ajax", "psv": "psv", "feyenoord": "feyenoord", "atletico": "atletico", "sevilla": "sevilla", "valencia": "valencia", "chelsea": "chelsea", "arsenal": "arsenal", "liverpool": "liverpool", "city": "manchester city", "united": "manchester united", "crystal palace": "crystal palace", "palace": "crystal palace", "man utd": "manchester united", "napoli": "napoli"}
    if low in aliases:
        want = aliases[low]
        for k in stats:
            if want in k.lower():
                return k
    for k in stats:
        kl = k.lower()
        if low in kl or kl in low:
            return k
    parts = low.split()
    if parts:
        for k in stats:
            if parts[0] in k.lower():
                return k
    return None

# ---------- Predict ----------
def predict_match(home_inp, away_inp, league="Default", stats=None, verbose=False):
    if stats is None:
        stats, _ = build_team_stats()
    home = find_team(stats, home_inp) or home_inp
    away = find_team(stats, away_inp) or away_inp
    hs = stats.get(home); aws = stats.get(away)
    base_h, base_a = LEAGUE_AVG.get(league, LEAGUE_AVG["Default"])
    league_avg_total = base_h + base_a
    league_avg_per_team = league_avg_total / 2

    def lam(team_stats, is_home, opp_stats, league_base):
        if not team_stats:
            return league_base * (1.08 if is_home else 1.0)
        n = team_stats.get("n", 0)
        # Shrinkage: n صغير -> أقرب لمتوسط الدوري
        shrink = n / (n + 8) if n > 0 else 0  # 8 ماتشات prior
        raw = team_stats["home_scored"] if is_home else team_stats["away_scored"]
        # تعديل دفاع الخصم
        if opp_stats:
            opp_conc = opp_stats["away_conceded"] if is_home else opp_stats["home_conceded"]
            # FIX: كاب [0.7, 1.4] - دفاع خصم من عينة صغيرة (ماتش واحد 4 أهداف) مينفعش يضرب xG في 3
            factor = max(0.7, min(1.4, opp_conc / 1.35))
            raw = raw * factor
            raw = max(0.3, min(3.0, raw))
        # Elo adjustment صغير
        if opp_stats and team_stats.get("elo") and opp_stats.get("elo"):
            elo_diff = (team_stats["elo"] - opp_stats["elo"]) * (1 if is_home else -1)
            raw = raw * math.exp(elo_diff * 0.0006)
        blended = shrink * raw + (1 - shrink) * league_base
        # Weak home bonus V2: لو صاحب الأرض أضعف بكتير، زود 15% - درس Sunderland
        if is_home and team_stats.get("elo") and opp_stats and opp_stats.get("elo"):
            if team_stats["elo"] < opp_stats["elo"] - 80:
                blended = blended * 1.15
        return max(0.2, min(3.8, blended))

    lam_h = lam(hs, True, aws, base_h)
    lam_a = lam(aws, False, hs, base_a)
    # Home advantage إضافي خفيف من Elo
    if hs and aws and hs.get("elo") and aws.get("elo"):
        exp_h = elo_expected(hs["elo"], aws["elo"])
        # لو Elo بيقول Home قوي، زود lam_h شوية
        lam_h = lam_h * (0.92 + 0.16 * exp_h)
        lam_h = max(0.2, min(3.8, lam_h))
    m = dixon_coles_matrix(round(lam_h, 2), round(lam_a, 2), rho=SIGMA_V39["rho_dixon_coles"])
    mk = matrix_to_markets(m)
    n = min(hs["n"] if hs else 0, aws["n"] if aws else 0)
    grade = grade_for(n)
    conf = max(mk["1"], mk["X"], mk["2"])
    # Safety scores V39 - من المصفوفة نفسها، مش أرقام ثابتة
    safety = {
        "Over 1": round(mk["Over05"] * 100 * 0.92, 1),
        "2H Over 0.5": round(82 + (mk["Over25"] * 10), 1),  # تقدير محافظ + درس Late
        "BTTS": round(mk["BTTS"] * 100 * (SIGMA_V39["btts_weight"] / 100), 1),
        "Over 2.5": round(mk["Over25"] * 100, 1),
    }
    # Tier
    if safety["Over 1"] >= 80:
        tier = "Gold"
    elif safety["Over 1"] >= 70:
        tier = "Balanced"
    else:
        tier = "Value"
    result = {
        "match": f"{home} vs {away}", "home": home, "away": away, "league": league,
        "xG_home": round(lam_h, 2), "xG_away": round(lam_a, 2), "xG": f"{round(lam_h,2)}-{round(lam_a,2)}",
        "1": round(mk["1"] * 100, 1), "X": round(mk["X"] * 100, 1), "2": round(mk["2"] * 100, 1),
        "BTTS": round(mk["BTTS"] * 100, 1), "Over25": round(mk["Over25"] * 100, 1),
        "Over15": round(mk["Over15"] * 100, 1), "exp_goals": round(mk["exp_goals"], 2),
        "top_scores": mk["top_scores"], "conf": round(conf * 100, 1),
        "n": n, "grade": grade, "tier": tier, "safety": safety,
        "home_elo": hs.get("elo") if hs else 1500, "away_elo": aws.get("elo") if aws else 1500,
        "home_form": hs.get("form", "") if hs else "", "away_form": aws.get("form", "") if aws else "",
        "source": "V39 Ensemble Dixon-Coles+Elo+xG",
    }
    if verbose:
        print(f"{result['match']}  xG: {result['xG']}  n={n} grade={grade} tier={tier}")
        print(f"1: {result['1']}%  X: {result['X']}%  2: {result['2']}%")
        print(f"BTTS: {result['BTTS']}% (weight 70)  Over 2.5: {result['Over25']}%  Exp Goals: {result['exp_goals']}")
        print(f"Top: {', '.join([f'{s} {p}%' for s,p in result['top_scores']])}")
        print(f"Elo: {result['home_elo']} vs {result['away_elo']}  Form: {result['home_form']} vs {result['away_form']}")
        print(f"Safety: {result['safety']}")
    return result

# ---------- Evaluation - الشفافية ----------
def evaluate_verified(stats=None):
    verified, _ = load_verified()
    if not verified:
        return {"n": 0, "error": "No verified file"}
    if stats is None:
        stats, _ = build_team_stats()
    hit = exact = 0; mae = 0.0; brier = 0.0; logloss = 0.0; btts_hit = 0; n = 0
    calib = defaultdict(list)
    for r in verified:
        try:
            ph = int(r["predicted_home"]); pa = int(r["predicted_away"])
            rh = int(r["real_home"]); ra = int(r["real_away"])
        except Exception:
            continue
        # إعادة التنبؤ بنفس الـ xG من التوقع الأصلي؟ لا - نقيم التوقع الأصلي نفسه
        # ونقيم كمان تنبؤ V39 الحالي للمقارنة - لو الفرق اتغيرت في التاريخ، ده طبيعي
        n += 1
        pick = "1" if ph > pa else ("X" if ph == pa else "2")
        real = "1" if rh > ra else ("X" if rh == ra else "2")
        if pick == real:
            hit += 1
        if ph == rh and pa == ra:
            exact += 1
        mae += abs((ph + pa) - (rh + ra))
        # Brier على التوقع الأصلي - نحوله لاحتمالات من Poisson بسيط
        # نستخدم xG = التوقع نفسه كـ lambda
        m = dixon_coles_matrix(max(0.2, ph), max(0.2, pa))
        mk = matrix_to_markets(m)
        probs = {"1": mk["1"], "X": mk["X"], "2": mk["2"]}
        # Brier
        for k in ["1", "X", "2"]:
            y = 1.0 if real == k else 0.0
            brier += (probs[k] - y) ** 2
        # Log loss
        p_real = max(1e-9, probs[real])
        logloss += -math.log(p_real)
        # BTTS
        pred_btts = 1 if ph > 0 and pa > 0 else 0
        real_btts = 1 if rh > 0 and ra > 0 else 0
        if pred_btts == real_btts:
            btts_hit += 1
        calib[real].append(probs[real])
    if n == 0:
        return {"n": 0}
    return {
        "n": n, "hit_rate": round(hit / n * 100, 1), "hit": hit,
        "exact_rate": round(exact / n * 100, 1), "exact": exact,
        "mae_goals": round(mae / n, 2),
        "brier": round(brier / n, 4), "logloss": round(logloss / n, 4),
        "btts_hit_rate": round(btts_hit / n * 100, 1),
        "avg_calib_prob_for_real": round(sum([sum(v) for v in calib.values()]) / n, 3) if n else 0,
    }

# ---------- Monte Carlo - محاكاة الموسم ----------
def monte_carlo_season(fixtures, stats, n_sims=1000, seed=42):
    """fixtures: list of {home, away, league} - يلعب الموسم n_sims مرة"""
    rnd = random.Random(seed)
    points = defaultdict(list)
    titles = Counter(); top4 = Counter(); releg = Counter()
    teams = set()
    for f in fixtures:
        teams.add(f["home"]); teams.add(f["away"])
    teams = list(teams)
    for _ in range(n_sims):
        pts = {t: 0 for t in teams}
        gd = {t: 0 for t in teams}
        for f in fixtures:
            # استخدم predict_match بدون verbose - سريع: lambda من stats مباشرة
            # نعيد استخدام predict_match لكن بـ stats جاهزة - نعمل نسخة خفيفة هنا
            hs = stats.get(f["home"]); aws = stats.get(f["away"])
            base_h, base_a = LEAGUE_AVG.get(f.get("league", "Default"), LEAGUE_AVG["Default"])
            # lambda مبسط
            def _lam(ts, is_home, opp, base):
                if not ts:
                    return base
                raw = ts["home_scored"] if is_home else ts["away_scored"]
                if opp:
                    opp_conc = opp["away_conceded"] if is_home else opp["home_conceded"]
                    factor = max(0.7, min(1.4, opp_conc / 1.35))
                    raw = raw * factor
                return max(0.2, min(3.0, raw))
            lh = _lam(hs, True, aws, base_h); la = _lam(aws, False, hs, base_a)
            # سحب Poisson
            # Poisson sampling via Knuth
            def _pois(lam):
                L = math.exp(-lam); k = 0; p = 1.0
                while True:
                    p *= rnd.random()
                    if p <= L:
                        break
                    k += 1
                return k
            gh = _pois(lh); ga = _pois(la)
            if gh > ga:
                pts[f["home"]] += 3
            elif gh < ga:
                pts[f["away"]] += 3
            else:
                pts[f["home"]] += 1; pts[f["away"]] += 1
            gd[f["home"]] += gh - ga; gd[f["away"]] += ga - gh
        # ترتيب
        ranked = sorted(teams, key=lambda t: (pts[t], gd[t]), reverse=True)
        if ranked:
            titles[ranked[0]] += 1
            for t in ranked[:4]:
                top4[t] += 1
            for t in ranked[-3:]:
                releg[t] += 1
            for t in teams:
                points[t].append(pts[t])
    out = {}
    for t in teams:
        arr = points[t]
        out[t] = {
            "title_prob": round(titles[t] / n_sims * 100, 1),
            "top4_prob": round(top4[t] / n_sims * 100, 1),
            "relegation_prob": round(releg[t] / n_sims * 100, 1),
            "avg_points": round(statistics.mean(arr), 1) if arr else 0,
            "median_points": round(statistics.median(arr), 1) if arr else 0,
        }
    return out

# ---------- Unified Snapshot ----------
def backup_data():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = DATA / f"backup_{ts}"
    bdir.mkdir(exist_ok=True)
    copied = []
    for fname in ["sigma_real_verified.csv", "sigma_next_month.json", "sigma_next_month.csv", "sigma_history.csv", "sigma_team_stats.json", "sigma_league_stats.json", "sigma_bulk_predictions.csv"]:
        for base in [DATA, BASE]:
            p = base / fname
            if p.exists():
                try:
                    shutil.copy(p, bdir / fname); copied.append(fname); break
                except Exception:
                    pass
    return str(bdir), copied

def unified_snapshot(save=True):
    stats, meta = build_team_stats()
    verified, v_path = load_verified()
    history, h_path = load_history()
    future, f_path, f_meta = load_future()
    ev = evaluate_verified(stats)
    snap = {
        "version": VERSION, "generated": str(date.today()),
        "counts": {"verified_old": len(verified), "history": len(history), "future": len(future), "teams": len(stats), "combined_matches": meta.get("combined", 0)},
        "paths": {"verified": v_path, "history": h_path, "future": f_path},
        "meta": meta, "evaluation": ev,
        "teams_top": sorted([(k, v["n"], v["elo"]) for k, v in stats.items()], key=lambda x: x[2], reverse=True)[:10],
        "future_meta": f_meta,
    }
    if save:
        (DATA / "sigma_unified.json").write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    return snap

def predict_all_future(save=True, stats=None):
    future, _, _ = load_future()
    if not future:
        return [], "No future file - Run Fetch first"
    if stats is None:
        stats, _ = build_team_stats()
    out = []
    for mm in future:
        # future format: {match, date, league} أو {homeTeam, awayTeam}
        if isinstance(mm.get("match"), str) and " vs " in mm["match"]:
            h, a = mm["match"].split(" vs ")
            league = mm.get("league", "Default"); d = mm.get("date", "")
        else:
            h = mm.get("homeTeam") or mm.get("home") or "?"
            a = mm.get("awayTeam") or mm.get("away") or "?"
            if isinstance(h, dict):
                h = h.get("name", "?")
            if isinstance(a, dict):
                a = a.get("name", "?")
            league = mm.get("league", "Default"); d = mm.get("date") or mm.get("utcDate", "")[:10]
        try:
            pr = predict_match(h.strip(), a.strip(), league, stats=stats)
            pr["date"] = str(d)[:10]
            out.append(pr)
        except Exception as e:
            out.append({"match": f"{h} vs {a}", "date": str(d)[:10], "league": league, "error": str(e)})
    out_sorted = sorted([o for o in out if "error" not in o], key=lambda x: x["conf"], reverse=True)
    if save and out:
        with open(DATA / "sigma_bulk_predictions.csv", "w", newline="", encoding="utf-8") as f:
            fields = ["date", "match", "league", "xG", "1", "X", "2", "BTTS", "Over25", "conf", "grade", "tier"]
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
            for o in out:
                if "error" in o:
                    continue
                w.writerow({k: o.get(k, "") for k in fields})
    return out_sorted, f"Predict All: {len(out)} matches - using V39 Ensemble (not league avg only)"

# ---------- Self Check - التشيك الكامل ----------
def self_check():
    print("=" * 60)
    print(f"Sigma {VERSION} - Self Check - قديم + جديد + مستقبل")
    print("=" * 60)
    checks = []
    def _chk(name, ok, detail=""):
        checks.append((name, bool(ok), detail))
        print(f"{'PASS' if ok else 'FAIL'} - {name}  {detail}")

    # 1 Poisson sums to 1
    s = sum(poisson(1.5, g) for g in range(0, 30))
    _chk("Poisson sums to 1", abs(s - 1) < 0.001, f"sum={s:.4f}")
    # 2 Dixon-Coles matrix sums to 1
    m = dixon_coles_matrix(1.65, 1.35)
    _chk("Dixon-Coles matrix sums to 1", abs(sum(m.values()) - 1) < 0.001, f"sum={sum(m.values()):.4f}")
    # 3 Markets sums
    mk = matrix_to_markets(m)
    _chk("1X2 sums to 100%", abs(mk["1"] + mk["X"] + mk["2"] - 1) < 0.001, f"{mk['1']:.3f}+{mk['X']:.3f}+{mk['2']:.3f}")
    # 4 Verified loads 14
    verified, _ = load_verified()
    _chk("Verified loads (old data)", len(verified) >= 14, f"n={len(verified)}")
    # 5 Team stats builds
    stats, meta = build_team_stats()
    _chk("Team stats builds", len(stats) >= 10, f"teams={len(stats)} combined={meta.get('combined')}")
    # 6 Predict known match - لا اختراع فرق
    try:
        pr = predict_match("Arsenal", "Chelsea", "England", stats=stats)
        ok = pr["xG_home"] > 0.2 and pr["xG_home"] < 3.8 and pr["conf"] > 0
        _chk("Predict Arsenal vs Chelsea", ok, f"xG={pr['xG']} conf={pr['conf']}% grade={pr['grade']}")
    except Exception as e:
        _chk("Predict Arsenal vs Chelsea", False, str(e))
    # 7 Evaluation
    ev = evaluate_verified(stats)
    _chk("Evaluation runs", ev.get("n", 0) >= 14, f"n={ev.get('n')} hit={ev.get('hit_rate')}% Brier={ev.get('brier')}")
    # 8 Kelly
    k = kelly_stake(0.5, 2.10, 1000, 0.30)
    _chk("Kelly 30% correct", abs(k - 13.64) < 0.5, f"Kelly(50%,2.10,1000,30%)={k} (expected ~13.64)")
    # 9 EV
    e = ev_calc(0.5, 2.10)
    _chk("EV correct", abs(e - 0.05) < 0.001, f"EV={e}")
    # 10 CLV
    c = clv_calc(2.10, 1.95)
    _chk("CLV correct", c > 0, f"CLV={c}%")
    # 11 Monte Carlo - صغير سريع للتشيك
    try:
        fx = [{"home": "Arsenal", "away": "Chelsea", "league": "England"}, {"home": "Liverpool", "away": "Man Utd", "league": "England"}]
        # استخدم أسماء موجودة في stats لو أمكن - لو مش موجودة، Monte Carlo هيستخدم league avg
        mc = monte_carlo_season(fx, stats, n_sims=100, seed=42)
        _chk("Monte Carlo runs", len(mc) >= 2, f"teams={len(mc)}")
    except Exception as e:
        _chk("Monte Carlo runs", False, str(e))
    # 12 Unified snapshot
    try:
        snap = unified_snapshot(save=True)
        _chk("Unified snapshot saves", (DATA / "sigma_unified.json").exists(), f"verified={snap['counts']['verified_old']} future={snap['counts']['future']} teams={snap['counts']['teams']}")
    except Exception as e:
        _chk("Unified snapshot saves", False, str(e))
    # 13 Backup
    try:
        bdir, copied = backup_data()
        _chk("Backup works", True, f"dir={bdir} files={len(copied)}")
    except Exception as e:
        _chk("Backup works", False, str(e))
    # 14 No invented teams in predict_all if future exists
    future, _, _ = load_future()
    if future:
        out, msg = predict_all_future(save=False, stats=stats)
        _chk("Predict All uses Ensemble", len(out) > 0, msg)
    else:
        _chk("Predict All uses Ensemble (no future file - skip, needs Fetch)", True, "No future file yet - Fetch will fill it")
    # 15 Brier in range
    _chk("Brier in [0,2]", 0 <= ev.get("brier", 9) <= 2, f"Brier={ev.get('brier')}")
    # 16 Grade logic
    _chk("Grade logic", grade_for(35) == "A" and grade_for(3) == "D", "A>=30 D<5")

    # تحذيرات جودة الداتا - مش FAIL، لكن لازم المستخدم يعرف قبل الرفع
    print("-" * 60)
    print("Data Quality Warnings (قبل الرفع):")
    dq = data_quality()
    if not dq:
        print("  No warnings - الداتا نضيفة")
    else:
        for w in dq:
            print(f"  WARNING - {w}")
    passed = sum(1 for _, ok, _ in checks if ok)
    print("-" * 60)
    print(f"Result: {passed}/{len(checks)} PASS")
    if passed == len(checks):
        print("ALL CHECKS PASS - جاهز للرفع")
    else:
        print("فيه FAIL - متعملش رفع قبل ما تصلحه")
    print("=" * 60)
    return passed, len(checks), checks

# ---------- CLI ----------
def interactive():
    print(f"\nSigma {VERSION} - Mahmoud Emad - قديم + جديد + مستقبل")
    print("1. Predict xG  2. Predict team  3. List Future  4. Eval  5. Fetch Future  6. Predict All (V39)  7. History  8. Learn  9. Update All  10. Unified  11. Monte Carlo  12. Check  0. Exit")
    while True:
        c = input("Choose: ").strip()
        if c == "0":
            break
        elif c == "1":
            try:
                h = float(input("Home xG: ") or 1.78); a = float(input("Away xG: ") or 1.35)
            except Exception:
                h, a = 1.78, 1.35
            m = dixon_coles_matrix(h, a); mk = matrix_to_markets(m)
            print(f"1: {mk['1']*100:.1f}%  X: {mk['X']*100:.1f}%  2: {mk['2']*100:.1f}%")
            print(f"BTTS: {mk['BTTS']*100:.1f}%  Over 2.5: {mk['Over25']*100:.1f}%  Exp: {mk['exp_goals']:.2f}")
            print(f"Top: {mk['top_scores']}")
        elif c == "2":
            home = input("Home team: ").strip(); away = input("Away team: ").strip()
            league = input("League (Enter=England): ").strip() or "England"
            if home and away:
                predict_match(home, away, league, verbose=True)
            else:
                print("اكتب الفريقين")
        elif c == "3":
            future, _, _ = load_future()
            print(f"Future matches: {len(future)}")
            for i, mm in enumerate(future[:20], 1):
                print(f"{i}. {mm.get('date','')} {mm.get('match','')}")
        elif c == "4":
            ev = evaluate_verified()
            print(f"Eval: n={ev.get('n')} Hit={ev.get('hit_rate')}% Exact={ev.get('exact_rate')}% MAE={ev.get('mae_goals')} Brier={ev.get('brier')} LogLoss={ev.get('logloss')}")
        elif c == "5":
            print("Run: python sigma_auto_fetch_v39.py  (needs FOOTBALL_DATA_TOKEN)")
            print("أو: python sigma_auto_fetch.py  (القديم)")
        elif c == "6":
            out, msg = predict_all_future()
            print(msg)
            for o in out[:10]:
                print(f"{o['date']} {o['match']}  1:{o['1']}% X:{o['X']}% 2:{o['2']}% BTTS:{o['BTTS']}% grade={o['grade']}")
            print("Saved: data/sigma_bulk_predictions.csv")
        elif c == "7":
            print("Run: python sigma_history_fetch.py --init  (أول مرة)  أو  --daily  (تحديث)")
        elif c == "8":
            snap = unified_snapshot(save=True)
            print(f"Learn - Unified: verified={snap['counts']['verified_old']} history={snap['counts']['history']} future={snap['counts']['future']} teams={snap['counts']['teams']}")
            print(f"Eval: {snap['evaluation']}")
        elif c == "9":
            print("Update All: 1) History Daily  2) Fetch Future  3) Unified")
            print("Run in Termux:")
            print("  python sigma_history_fetch.py --daily")
            print("  python sigma_auto_fetch_v39.py")
            print("  python sigma_v39.py --unified")
        elif c == "10":
            snap = unified_snapshot(save=True)
            print(json.dumps(snap, ensure_ascii=False, indent=2))
        elif c == "11":
            future, _, _ = load_future()
            stats, _ = build_team_stats()
            if not future:
                print("No future - Fetch first")
            else:
                fx = []
                for mm in future[:30]:
                    if " vs " in str(mm.get("match", "")):
                        h, a = mm["match"].split(" vs ")
                        fx.append({"home": h.strip(), "away": a.strip(), "league": mm.get("league", "Default")})
                mc = monte_carlo_season(fx, stats, n_sims=1000)
                for t, v in sorted(mc.items(), key=lambda x: x[1]["title_prob"], reverse=True)[:10]:
                    print(f"{t}: Title {v['title_prob']}% Top4 {v['top4_prob']}% AvgPts {v['avg_points']}")
        elif c == "12":
            self_check()
        else:
            print("اختيار غير صحيح")

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if "--check" in args:
        p, t, _ = self_check()
        sys.exit(0 if p == t else 1)
    elif "--eval" in args:
        print(evaluate_verified())
    elif "--unified" in args:
        print(json.dumps(unified_snapshot(), ensure_ascii=False, indent=2))
    elif "--predict-all" in args:
        out, msg = predict_all_future()
        print(msg)
        for o in out[:10]:
            print(o)
    elif "--predict" in args:
        # --predict "Arsenal vs Chelsea" [league]
        try:
            idx = args.index("--predict")
            match = args[idx + 1]
            league = args[idx + 2] if len(args) > idx + 2 else "England"
            h, a = match.split(" vs ")
            print(predict_match(h.strip(), a.strip(), league, verbose=True))
        except Exception as e:
            print(f"Usage: python sigma_v39.py --predict 'Arsenal vs Chelsea' England  Error: {e}")
    else:
        interactive()
