#!/usr/bin/env python3
# Sigma V47 VERIFY + FIX - Merged on top of V46 - Mahmoud Emad
# Problem found by verification (Nov 11 2026):
#  - Bulk file is a STALE snapshot: finished matches still listed as OPEN/upcoming
#    * Hansa Rostock vs Stuttgart - was 21 Aug 2026, FT 0-4, NOT upcoming
#    * Portugal vs Wales - was 24 Sep 2026, FT 1-0, NOT upcoming
#    * Zamalek vs Al Ahly - was 11 Oct 2026, FT 0-2 Al Ahly win, home=Zamalek, NOT 15 Nov Al Ahly home
#  - MANUAL matches invented wrong date + wrong home/away:
#    * Al Hilal vs Al Nassr 16 Nov - REAL is Al Nassr HOME vs Al Hilal, 10 Dec 2026 (Sportradar/PrimaTips)
#      NOTE: one draft calendar says 1 Jan 2027 - flagged NEED_RECHECK, do NOT trust blindly
#  - UNL: Matchdays 1-4 (24 Sep - 6 Oct) are FINISHED. Only MD5+MD6 (12-17 Nov, 52 matches) are upcoming.
#    Source: UEFA official page 11 Nov 2026 - league phase 24 Sep to 17 Nov, MD5 12 Nov, MD6 15 Nov.
#  - England vs Croatia 12 Nov 19:45 Wembley is CORRECT - kept.
# Rule: NEVER invent a match. If a fixture cannot be verified, REMOVE it from upcoming
# and put it in suspect list. Do NOT guess a new date.
# Stdlib only. No Arabic inside .py. Run: python3 sigma_v47_verify_fix.py
# Run AFTER sigma_v46_final.py (V46 cleans + Dixon-Coles). V47 then verifies + corrects fixtures.
import json, csv, re, math, os, glob
from pathlib import Path
from datetime import date

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
TODAY = date.today().isoformat()  # 2026-11-11 in real run

def norm(s):
    s = str(s or "").strip().lower()
    s = re.sub(r"【[^】]*】", "", s)
    s = re.sub(r"entity-[^,]+", "", s)
    for w in [" sc", " fc", " cf", " sfc", " club", " (egy)", " (ksa)"]:
        if s.endswith(w):
            s = s[:-len(w)]
    s = re.sub(r"[^a-z0-9 ]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    # aliases
    a = {"al ahly": "al ahly", "al ahly sc": "al ahly", "ahly": "al ahly",
         "zamalek": "zamalek", "zamalek sc": "zamalek",
         "al hilal": "al hilal", "al hilal sfc": "al hilal",
         "al nassr": "al nassr", "al nassr club": "al nassr", "al nassr fc": "al nassr",
         "vfb stuttgart": "stuttgart", "stuttgart": "stuttgart",
         "hansa rostock": "hansa rostock", "fc hansa rostock": "hansa rostock",
         "turkiye": "turkiye", "turkey": "turkiye"}
    return a.get(s, s)

def clean_str(s):
    if not isinstance(s, str):
        return s
    t = re.sub(r"【entity-[^】]*?\|canonical_name=([^】]+)】", r"\1", s)
    t = re.sub(r"【entity-([^】|]+)(?:\|[^】]*)?】", r"\1", t)
    return re.sub(r"\s+", " ", t.replace("【", "").replace("】", "")).strip()

# --- VERIFIED DATA (sources in final message) ---
# Finished matches that MUST NOT be in upcoming
KNOWN_FINISHED = {
    ("hansa rostock", "stuttgart"): {"date": "2026-08-21", "result": "0-4", "comp": "DFB Pokal"},
    ("portugal", "wales"): {"date": "2026-09-24", "result": "1-0", "comp": "UEFA Nations League"},
    ("zamalek", "al ahly"): {"date": "2026-10-11", "result": "0-2", "comp": "Egyptian Premier League"},
    # UNL MD1-4 examples - generic date-prune covers all, these are explicit anchors
    ("netherlands", "germany"): {"date": "2026-09-24", "result": "1-1", "comp": "UEFA Nations League"},
    ("england", "spain"): {"date": "2026-09-26", "result": "2-3", "comp": "UEFA Nations League"},
    ("croatia", "england"): {"date": "2026-10-03", "result": "0-7", "comp": "UEFA Nations League"},
    ("spain", "croatia"): {"date": "2026-09-29", "result": "4-1", "comp": "UEFA Nations League"},
}

# Official UNL upcoming: MD5 12-14 Nov + MD6 15-17 Nov = 52 matches (UEFA 11 Nov 2026)
UNL_UPCOMING = {
    ("turkiye","belgium","2026-11-12"), ("armenia","cyprus","2026-11-12"),
    ("italy","france","2026-11-12"), ("czechia","spain","2026-11-12"),
    ("england","croatia","2026-11-12"), ("albania","finland","2026-11-12"),
    ("san marino","belarus","2026-11-12"), ("montenegro","latvia","2026-11-12"),
    ("moldova","kazakhstan","2026-11-13"), ("netherlands","greece","2026-11-13"),
    ("serbia","germany","2026-11-13"), ("scotland","north macedonia","2026-11-13"),
    ("slovenia","switzerland","2026-11-13"), ("slovakia","faroe islands","2026-11-13"),
    ("bulgaria","iceland","2026-11-13"), ("luxembourg","estonia","2026-11-13"),
    ("andorra","gibraltar","2026-11-13"), ("liechtenstein","azerbaijan","2026-11-13"),
    ("kosovo","israel","2026-11-14"), ("norway","wales","2026-11-14"),
    ("georgia","hungary","2026-11-14"), ("portugal","denmark","2026-11-14"),
    ("northern ireland","ukraine","2026-11-14"), ("austria","republic of ireland","2026-11-14"),
    ("romania","poland","2026-11-14"), ("sweden","bosnia and herzegovina","2026-11-14"),
    ("cyprus","montenegro","2026-11-15"), ("latvia","armenia","2026-11-15"),
    ("belarus","albania","2026-11-15"), ("finland","san marino","2026-11-15"),
    ("belgium","italy","2026-11-15"), ("france","turkiye","2026-11-15"),
    ("croatia","czechia","2026-11-15"), ("spain","england","2026-11-15"),
    ("faroe islands","moldova","2026-11-16"), ("kazakhstan","slovakia","2026-11-16"),
    ("estonia","bulgaria","2026-11-16"), ("iceland","luxembourg","2026-11-16"),
    ("lithuania","liechtenstein","2026-11-16"), ("germany","netherlands","2026-11-16"),
    ("greece","serbia","2026-11-16"), ("north macedonia","slovenia","2026-11-16"),
    ("switzerland","scotland","2026-11-16"), ("gibraltar","malta","2026-11-16"),
    ("denmark","norway","2026-11-17"), ("wales","portugal","2026-11-17"),
    ("hungary","northern ireland","2026-11-17"), ("ukraine","georgia","2026-11-17"),
    ("israel","austria","2026-11-17"), ("republic of ireland","kosovo","2026-11-17"),
    ("bosnia and herzegovina","romania","2026-11-17"), ("poland","sweden","2026-11-17"),
}

# MANUAL corrections - verified, NOT invented
MANUAL_CORRECTIONS = {
    # key = (norm_home_wrong, norm_away_wrong) -> corrected
    ("al hilal", "al nassr"): {"home": "Al Nassr", "away": "Al Hilal", "date": "2026-12-10",
        "league": "Saudi Pro League", "note": "CORRECTED home/away + date. CONFLICT: one draft says 1 Jan 2027 - NEED_RECHECK before Dec.",
        "status": "SCHEDULED", "verify": "Sportradar + PrimaTips say 10 Dec"},
    ("al ahly", "zamalek"): {"home": "Zamalek", "away": "Al Ahly", "date": "2026-10-11",
        "league": "Egyptian Premier League", "note": "FINISHED 0-2 Al Ahly win - REMOVE from upcoming, move to archive.",
        "status": "FINISHED", "result": "0-2"},
}

def extract_home_away(mm):
    h = a = None
    if isinstance(mm.get("match"), str) and " vs " in mm["match"]:
        h, a = [clean_str(x) for x in mm["match"].split(" vs ", 1)]
    else:
        for k in ["home", "homeTeam", "home_team"]:
            if mm.get(k):
                h = clean_str(mm[k]["name"] if isinstance(mm[k], dict) else mm[k]); break
        for k in ["away", "awayTeam", "away_team"]:
            if mm.get(k):
                a = clean_str(mm[k]["name"] if isinstance(mm[k], dict) else mm[k]); break
    return h, a

def main():
    print("Sigma V47 VERIFY + FIX (merged on V46)")
    print(f"Today = {TODAY} - any fixture with date < today CANNOT be upcoming")
    print("=" * 60)
    total_before = 0; kept = 0; removed_finished = 0; corrected = 0
    suspect = []; archived = []
    for fname in ["sigma_bulk_predictions.json", "sigma_bulk_predictions_v44.json", "sigma_universal_fixtures.json", "sigma_next_month.json"]:
        for cand in [DATA / fname, BASE / fname]:
            if not cand.exists():
                continue
            try:
                obj = json.loads(cand.read_text(encoding="utf-8"))
                rows = obj if isinstance(obj, list) else obj.get("matches", obj.get("data", []))
                if not isinstance(rows, list) or not rows:
                    continue
                total_before += len(rows)
                new_rows = []
                for mm in rows:
                    h, a = extract_home_away(mm)
                    if not h or not a:
                        suspect.append({"match": str(mm)[:80], "reason": "no home/away"}); continue
                    d = str(mm.get("date", mm.get("utcDate", "")))[:10]
                    league = clean_str(mm.get("league") or mm.get("competition") or "")
                    nh, na = norm(h), norm(a)
                    # 1. MANUAL correction first
                    if (nh, na) in MANUAL_CORRECTIONS:
                        c = MANUAL_CORRECTIONS[(nh, na)]
                        if c["status"] == "FINISHED":
                            archived.append({"date": c["date"], "home": c["home"], "away": c["away"],
                                             "result": c.get("result", ""), "league": c["league"], "note": c["note"]})
                            removed_finished += 1
                            print(f"REMOVE finished MANUAL: {h} vs {a} ({d}) -> real {c['home']} vs {c['away']} {c['date']} {c.get('result','')}")
                            continue
                        else:
                            mm["match"] = f"{c['home']} vs {c['away']}"
                            mm["date"] = c["date"]
                            mm["league"] = c["league"]
                            mm["verify_note"] = c["note"]
                            mm["status"] = "SCHEDULED"
                            mm["is_default"] = 0
                            mm["needs_recheck"] = 1
                            for k in ["home", "homeTeam"]:
                                if k in mm: mm[k] = c["home"]
                            for k in ["away", "awayTeam"]:
                                if k in mm: mm[k] = c["away"]
                            corrected += 1
                            print(f"CORRECTED MANUAL: {h} vs {a} -> {c['home']} vs {c['away']} {c['date']}")
                            h, a = c["home"], c["away"]; d = c["date"]; nh, na = norm(h), norm(a)
                            new_rows.append(mm); kept += 1; continue
                    # 2. Known finished (any date in file) -> remove
                    if (nh, na) in KNOWN_FINISHED:
                        kf = KNOWN_FINISHED[(nh, na)]
                        archived.append({"date": kf["date"], "home": h, "away": a, "result": kf["result"], "league": kf["comp"], "note": "KNOWN_FINISHED"})
                        removed_finished += 1
                        print(f"REMOVE finished: {h} vs {a} -> real {kf['date']} FT {kf['result']}")
                        continue
                    # 3. Past date -> CANNOT be upcoming, remove (stale snapshot bug)
                    if d and d < TODAY:
                        archived.append({"date": d, "home": h, "away": a, "result": "", "league": league, "note": f"PAST date {d} < today - stale snapshot, moved to archive"})
                        removed_finished += 1
                        continue
                    # 4. UNL check: if league is UNL / Nations League, must be in official 52
                    if "nations" in league.lower() or "unl" in league.lower() or "unations" in league.lower():
                        if (nh, na, d) not in UNL_UPCOMING:
                            suspect.append({"match": f"{h} vs {a}", "date": d, "league": league,
                                            "reason": "UNL but NOT in UEFA official 52 upcoming (12-17 Nov) - REMOVE, do not guess"})
                            removed_finished += 1
                            continue
                        else:
                            mm["verified"] = "UEFA-official-11Nov2026"
                    # 5. Basic sanity: home == away, empty date
                    if nh == na:
                        suspect.append({"match": f"{h} vs {a}", "date": d, "reason": "home == away"}); continue
                    if not d:
                        suspect.append({"match": f"{h} vs {a}", "reason": "no date"}); continue
                    # 6. Clean names in place
                    if isinstance(mm.get("match"), str):
                        mm["match"] = f"{clean_str(h)} vs {clean_str(a)}"
                    mm["status"] = "SCHEDULED"
                    mm["is_default"] = 0
                    new_rows.append(mm); kept += 1
                # save back
                if isinstance(obj, list):
                    cand.write_text(json.dumps(new_rows, ensure_ascii=False, indent=1), encoding="utf-8")
                else:
                    obj["matches"] = new_rows
                    obj["total_matches"] = len(new_rows)
                    cand.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"{fname}: kept {len(new_rows)} / was {len(rows)}")
            except Exception as e:
                print(f"Skip {cand}: {e}")
    # archive finished
    if archived:
        ap = DATA / "sigma_finished_archive.csv"
        exists = ap.exists()
        with open(ap, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["date", "home", "away", "result", "league", "note"])
            if not exists: w.writeheader()
            w.writerows(archived)
        print(f"Archived finished: {len(archived)} -> data/sigma_finished_archive.csv")
    if suspect:
        (DATA / "sigma_suspect.json").write_text(json.dumps(suspect, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Suspect removed: {len(suspect)} -> data/sigma_suspect.json (check manually, do NOT re-add without source)")
    print("-" * 60)
    print(f"VERIFICATION SUMMARY: before={total_before} kept_upcoming={kept} removed_finished_or_suspect={removed_finished} corrected_manual={corrected}")
    print("Rule: upcoming = date >= today AND (UNL in UEFA 52 OR non-UNL with valid date). Everything else removed, not guessed.")
    print("Next: re-run sigma_v46_final.py to re-predict ONLY the kept upcoming, then git add + push.")
    print("If kept is 0 or suspiciously low, your fetch file is too old - re-run sigma_v44_fetch.py with fresh FOOTBALL_DATA_TOKEN.")

if __name__ == "__main__":
    main()
