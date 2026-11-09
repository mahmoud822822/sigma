import csv, pathlib, collections
p = pathlib.Path("data/sigma_history.csv")
if not p.exists():
    print("missing data/sigma_history.csv - run 7 History first")
    raise SystemExit
rows = list(csv.DictReader(open(p, encoding="utf-8")))
print(f"History loaded: {len(rows)} matches")
# اكتشاف اسماء الاعمدة اوتوماتيك
print("Columns:", list(rows[0].keys()))
def get(r, *names):
    for n in names:
        if n in r and r[n] != "" and r[n] is not None:
            return r[n]
    return None
def num(v):
    try: return int(float(str(v).strip()))
    except: return None
stats = collections.Counter()
league = collections.defaultdict(collections.Counter)
bets = collections.Counter()
bets_hit = collections.Counter()
for r in rows:
    hg = num(get(r, "home_goals","home_score","hg","homeGoals","home"))
    ag = num(get(r, "away_goals","away_score","ag","awayGoals","away"))
    lg = get(r, "league","competition","league_name") or "All"
    if hg is None or ag is None: continue
    total = hg + ag
    stats["n"] += 1
    stats["goals"] += total
    if hg > ag: stats["home_win"] += 1
    elif hg == ag: stats["draw"] += 1
    else: stats["away_win"] += 1
    if hg>0 and ag>0: stats["btts"] += 1
    if total>2.5: stats["over25"] += 1
    if total>1.5: stats["over15"] += 1
    if total<2.5: stats["under25"] += 1
    # اقوى الرهانات - بنفس تعريف البرنامج
    for name, hit in [("Home Win", hg>ag), ("Draw", hg==ag), ("Away Win", hg<ag), ("BTTS Yes", hg>0 and ag>0), ("BTTS No", not (hg>0 and ag>0)), ("Over 2.5", total>2.5), ("Under 2.5", total<2.5), ("Over 1.5", total>1.5), ("Home + Over 1.5", hg>ag and total>1.5)]:
        bets[name] += 1
        if hit: bets_hit[name] += 1
    league[lg]["n"] += 1
    league[lg]["goals"] += total
    if hg>0 and ag>0: league[lg]["btts"] += 1
n = stats["n"] or 1
out = []
out.append("Sigma Learn - 1500+ Real History - Mahmoud Emad")
out.append(f"Total: {n} matches")
out.append(f"Avg goals: {stats['goals']/n:.2f}  Home Win: {stats['home_win']/n*100:.1f}%  Draw: {stats['draw']/n*100:.1f}%  Away Win: {stats['away_win']/n*100:.1f}%")
out.append(f"BTTS: {stats['btts']/n*100:.1f}%  Over 2.5: {stats['over25']/n*100:.1f}%  Over 1.5: {stats['over15']/n*100:.1f}%  Under 2.5: {stats['under25']/n*100:.1f}%")
out.append("")
out.append("All Bets - Ranked by Hit Rate (n>=100):")
ranked = sorted(bets.keys(), key=lambda k: bets_hit[k]/bets[k] if bets[k] else 0, reverse=True)
for k in ranked:
    if bets[k]>=100:
        out.append(f"{k}: {bets_hit[k]}/{bets[k]} = {bets_hit[k]/bets[k]*100:.1f}%")
out.append("")
out.append("Strongest = highest hit rate above. Safest = high hit + large n. No bet is 100%.")
out.append("Per League:")
for lg, c in sorted(league.items()):
    if c["n"]>=50:
        out.append(f"{lg}: n={c['n']} Avg={c['goals']/c['n']:.2f} BTTS={c['btts']/c['n']*100:.1f}%")
out.append("")
out.append("Next: Run 9 Update All + 6 Predict All to make future predictions from this learning.")
txt = "\n".join(out)
print(txt)
pathlib.Path("LEARN_1500_REPORT.txt").write_text(txt, encoding="utf-8")
print("Saved: LEARN_1500_REPORT.txt")
