#!/usr/bin/env python3
# Sigma V48 ADD POSTERS + BASKETBALL - Merged on V46+V47 - Mahmoud Emad
# User posters (2 images) audited 11 Nov 2026 vs UEFA/CAF/Sportradar/FotMob:
# VERDICT: Most FIXTURES are REAL, but CONFIDENCE + ODDS in posters are FAKE.
#  - Poster says green check + "very high confidence" for ALL matches = FALSE.
#    Example Sabah vs Barcelona: one model 80% Barca, another 34% Barca - models disagree.
#    Lille vs Bayern, Man City vs Napoli are NOT sure wins.
#  - Poster odds (1.07-1.13 etc) NOT verified market odds. DO NOT USE.
#  - Poster accumulator 3.24 is cherry-picked: lower odds product = 2.65, upper = 3.28.
#    3.24 uses upper bounds to inflate.
#  - Home/away SWAP: Return leg 17 Nov is MALAWI home vs Egypt, NOT Egypt home.
#    Poster writes "Egypt x Malawi" - readers read Egypt home. CORRECTED to Malawi vs Egypt.
#  - Missing returns: Morocco vs Niger 17 Nov (BOTH in Morocco, Niger cannot host),
#    Togo vs Algeria 17 Nov (Togo home). Added.
#  - Al Ahli vs Al Nassr 20 Nov: reported as postponed MD9 moved from 15 Oct, NEED_RECHECK.
# BASKETBALL: YES, but SEPARATE file + SEPARATE model. Football Dixon-Coles Poisson
# does NOT apply to basketball (points, not goals). Basketball = BETA, NO prediction
# until points-based Elo is built. Do NOT merge basketball into football bulk.
# Stdlib only. Run AFTER V47: python3 sigma_v48_add_posters_basketball.py
import json, re
from pathlib import Path
BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

def norm(s):
    s = str(s or "").strip().lower()
    s = re.sub(r"[^a-z0-9 ]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    a = {"al ahly": "al ahly", "al ahli": "al ahli", "al nassr": "al nassr",
         "losc": "lille", "lille osc": "lille", "man city": "manchester city",
         "man utd": "manchester united", "man united": "manchester united",
         "psv": "psv eindhoven", "psv eindhoven": "psv eindhoven",
         "real madrid": "real madrid", "atletico": "atletico madrid",
         "atletico madrid": "atletico madrid", "borussia dortmund": "borussia dortmund",
         "dortmund": "borussia dortmund", "bvb": "borussia dortmund"}
    return a.get(s, s)

def clean(s):
    return re.sub(r"\s+", " ", str(s).replace("【", "").replace("】", "")).strip()

# Verified poster matches - DO NOT add poster odds/confidence
VERIFIED = [
    {"home": "Egypt", "away": "Malawi", "date": "2026-11-13", "league": "AFCON Qualification", "poster": "Poster1 #1 + Poster2 #2", "note": "REAL. Egypt HOME Cairo. Poster odds/confidence FAKE - do not use."},
    {"home": "Malawi", "away": "Egypt", "date": "2026-11-17", "league": "AFCON Qualification", "poster": "Poster1 #4 CORRECTED", "note": "REAL but HOME SWAP: real home is Malawi (Lilongwe), NOT Egypt. Poster wrote Egypt x Malawi."},
    {"home": "Morocco", "away": "Niger", "date": "2026-11-13", "league": "AFCON Qualification", "poster": "Poster1 #2", "note": "REAL. Morocco HOME Casablanca."},
    {"home": "Morocco", "away": "Niger", "date": "2026-11-17", "league": "AFCON Qualification", "poster": "Missing in poster - ADDED", "note": "REAL return. BOTH legs in Morocco - Niger cannot host (no approved stadium)."},
    {"home": "Algeria", "away": "Togo", "date": "2026-11-14", "league": "AFCON Qualification", "poster": "Poster1 #3", "note": "REAL. Algeria HOME Tizi Ouzou."},
    {"home": "Togo", "away": "Algeria", "date": "2026-11-17", "league": "AFCON Qualification", "poster": "Missing in poster - ADDED", "note": "REAL return. Togo HOME Lome."},
    {"home": "Real Madrid", "away": "PSV Eindhoven", "date": "2026-11-24", "league": "UEFA Champions League", "poster": "Poster1 #5 + Poster2 #4", "note": "REAL UCL MD5. Poster confidence FAKE."},
    {"home": "Sabah", "away": "Barcelona", "date": "2026-11-25", "league": "UEFA Champions League", "poster": "Poster1 #6 + Poster2 #1", "note": "REAL UCL MD5 Baku. Poster 'very high' FAKE: models disagree 80% vs 34% Barca."},
    {"home": "Atletico Madrid", "away": "Viking", "date": "2026-11-25", "league": "UEFA Champions League", "poster": "Poster1 #7 + Poster2 #8", "note": "REAL UCL MD5. Viking drew Bayern 3-3, beat Sabah 4-1 - NOT sure win."},
    {"home": "Lille", "away": "Bayern Munich", "date": "2026-11-25", "league": "UEFA Champions League", "poster": "Poster2 #3", "note": "REAL UCL MD5. LOSC=Lille. Poster 'very high' FAKE."},
    {"home": "Arsenal", "away": "Borussia Dortmund", "date": "2026-11-24", "league": "UEFA Champions League", "poster": "Poster2 #6", "note": "REAL UCL MD5."},
    {"home": "Manchester City", "away": "Napoli", "date": "2026-11-24", "league": "UEFA Champions League", "poster": "Poster2 #7", "note": "REAL UCL MD5. City ~69% per one model, NOT 100%."},
    {"home": "Arsenal", "away": "Manchester City", "date": "2026-11-29", "league": "Premier League", "poster": "Poster2 #5", "note": "REAL EPL MD12 Emirates. Moved from 28 to 29 Nov."},
    {"home": "Liverpool", "away": "Manchester United", "date": "2026-11-22", "league": "Premier League", "poster": "Poster2 #11", "note": "REAL EPL MD11 Anfield."},
    {"home": "Al Ahli", "away": "Al Nassr", "date": "2026-11-20", "league": "Saudi Pro League", "poster": "Poster2 #12", "note": "REPORTED postponed MD9 moved from 15 Oct. NEED_RECHECK - conflicting reports on confirmation. Time 19:30 Cairo = 20:30 Saudi."},
    # Already in V47 UNL set - do NOT duplicate, just audit
    {"home": "Spain", "away": "England", "date": "2026-11-15", "league": "UEFA Nations League", "poster": "Poster2 #9", "note": "REAL UNL MD6, already in V47. Poster 'medium-high' is honest for once."},
    {"home": "Italy", "away": "France", "date": "2026-11-12", "league": "UEFA Nations League", "poster": "Poster2 #10", "note": "REAL UNL MD5, already in V47."},
]

BASKETBALL = [
    # EuroLeague Round 11 - verified via Sportradar / Forebet / EuroLeague
    {"home": "Partizan Belgrade", "away": "Baskonia", "date": "2026-11-11", "league": "EuroLeague", "note": "Round 11 Belgrade 20:45 CET"},
    {"home": "Paris Basketball", "away": "Fenerbahce", "date": "2026-11-11", "league": "EuroLeague", "note": "Round 11 Paris 20:45 CET"},
    {"home": "Maccabi Tel Aviv", "away": "Hapoel Tel Aviv", "date": "2026-11-12", "league": "EuroLeague", "note": "Round 11"},
    {"home": "Olympiacos", "away": "Dubai Basketball", "date": "2026-11-12", "league": "EuroLeague", "note": "Round 11"},
    {"home": "Olimpia Milano", "away": "Zalgiris Kaunas", "date": "2026-11-12", "league": "EuroLeague", "note": "Round 11"},
    {"home": "Valencia", "away": "Bayern Munich", "date": "2026-11-12", "league": "EuroLeague", "note": "Round 11 - basketball Bayern, NOT football"},
    {"home": "Real Madrid", "away": "Crvena Zvezda", "date": "2026-11-12", "league": "EuroLeague", "note": "Round 11 Madrid - basketball Real, NOT football"},
    {"home": "Anadolu Efes", "away": "Virtus Bologna", "date": "2026-11-13", "league": "EuroLeague", "note": "Round 11"},
    {"home": "Panathinaikos", "away": "Barcelona", "date": "2026-11-13", "league": "EuroLeague", "note": "Round 11 - basketball Barca, NOT football"},
    {"home": "Lyon-Villeurbanne", "away": "Besiktas", "date": "2026-11-13", "league": "EuroLeague", "note": "Round 11"},
    # NBA - verified, times are US ET date 11 Nov evening = 12 Nov 02:00 Cairo
    {"home": "Indiana Pacers", "away": "Washington Wizards", "date": "2026-11-12", "league": "NBA", "note": "02:00 Cairo (11 Nov 19:00 ET) Gainbridge"},
    {"home": "New York Knicks", "away": "Cleveland Cavaliers", "date": "2026-11-12", "league": "NBA", "note": "02:00 Cairo (11 Nov 19:00 ET) MSG"},
]

def main():
    print("Sigma V48 ADD POSTERS + BASKETBALL (on top of V47)")
    print("Poster audit: fixtures mostly REAL, confidence + odds FAKE - stripped.")
    print("Basketball: SEPARATE file, NO football model, BETA.")
    print("=" * 60)
    # Accumulator check
    import math
    low = [1.07, 1.15, 1.18, 1.19, 1.20, 1.10, 1.16]
    high = [1.13, 1.20, 1.22, 1.22, 1.24, 1.12, 1.17]
    pl = 1.0; ph = 1.0
    for a, b in zip(low, high):
        pl *= a; ph *= b
    print(f"Poster accumulator claim 3.24 | lower-odds product = {pl:.2f} | upper-odds product = {ph:.2f}")
    print("-> 3.24 uses UPPER bounds to inflate. Honest range is 2.65-3.28, NOT a single 3.24.")
    added = 0; exists = 0
    for fname in ["sigma_bulk_predictions.json", "sigma_bulk_predictions_v44.json", "sigma_universal_fixtures.json"]:
        for cand in [DATA / fname, Path(__file__).parent / fname]:
            if not cand.exists():
                continue
            try:
                obj = json.loads(cand.read_text(encoding="utf-8"))
                rows = obj if isinstance(obj, list) else obj.get("matches", [])
                keys = set()
                for mm in rows:
                    m = str(mm.get("match", ""))
                    if " vs " in m:
                        h, a = m.split(" vs ", 1)
                        keys.add((norm(h), norm(a), str(mm.get("date", ""))[:10]))
                for v in VERIFIED:
                    k = (norm(v["home"]), norm(v["away"]), v["date"])
                    if k in keys:
                        exists += 1
                        # tag existing, strip poster odds if any
                        for mm in rows:
                            mm_m = str(mm.get("match", ""))
                            if " vs " in mm_m:
                                h, a = mm_m.split(" vs ", 1)
                                if (norm(h), norm(a), str(mm.get("date", ""))[:10]) == k:
                                    mm["verified"] = "V48-poster-verified"
                                    mm.pop("odds", None); mm.pop("poster_odds", None)
                                    mm["odds_note"] = "POSTER ODDS NOT VERIFIED - DO NOT USE"
                        continue
                    rows.append({
                        "match": f"{v['home']} vs {v['away']}",
                        "date": v["date"], "league": v["league"],
                        "sport": "football", "status": "SCHEDULED",
                        "verified": "V48-poster-verified",
                        "source_note": v["note"],
                        "odds_note": "POSTER ODDS NOT VERIFIED - DO NOT USE",
                        "poster_confidence": "FAKE - stripped, use model only",
                        "is_default": 0,
                        "needs_recheck": 1 if "NEED_RECHECK" in v["note"] else 0,
                    })
                    keys.add(k); added += 1
                if isinstance(obj, list):
                    cand.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
                else:
                    obj["matches"] = rows; obj["total_matches"] = len(rows)
                    cand.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"{fname}: +{added} new poster matches, {exists} already present")
                added = 0; exists = 0
            except Exception as e:
                print(f"Skip {cand}: {e}")
    # Basketball - SEPARATE file, never merged into football bulk
    bb = []
    for b in BASKETBALL:
        bb.append({"match": f"{b['home']} vs {b['away']}", "date": b["date"], "league": b["league"],
                   "sport": "basketball", "status": "SCHEDULED",
                   "prediction": "NONE - BETA, no model yet",
                   "model": "DO NOT USE football Dixon-Coles - basketball needs points-based Elo",
                   "verified": "V48-basketball-verified", "note": b["note"]})
    (DATA / "sigma_basketball_fixtures.json").write_text(json.dumps({"sport": "basketball", "total": len(bb), "warning": "BETA - no predictions. Show fixtures only until points-Elo is built.", "matches": bb}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Basketball: {len(bb)} fixtures -> data/sigma_basketball_fixtures.json (SEPARATE, BETA, NO predictions)")
    # Audit file
    audit = {"poster1_accumulator_claim": 3.24, "lower_product": round(pl, 2), "upper_product": round(ph, 2),
             "verdict": "Fixtures REAL, confidence FAKE, odds NOT VERIFIED, accumulator INFLATED",
             "fake_items": [
                 "All green checks + 'very high confidence' for every match - FALSE, no sure wins",
                 "Odds ranges (1.07-1.13 etc) - NOT verified market odds",
                 "Accumulator 3.24 - uses upper bounds, honest range 2.65-3.28",
                 "Egypt home vs Malawi 17 Nov - WRONG, real home is Malawi",
                 "Missing returns: Morocco-Niger 17 Nov, Togo-Algeria 17 Nov - added",
             ],
             "verified_matches": VERIFIED, "basketball": BASKETBALL}
    (DATA / "sigma_poster_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Audit -> data/sigma_poster_audit.json")
    print("Next: python3 sigma_v46_final.py (re-predict football ONLY) - do NOT run it on basketball file.")

if __name__ == "__main__":
    main()
