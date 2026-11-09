import csv, json
ver=list(csv.DictReader(open("data/sigma_real_verified.csv", encoding="utf-8")))
hit=sum(1 for r in ver if r.get("bet_result")=="correct")
print(f"=== VERIFIED: {hit}/{len(ver)} = {hit/len(ver)*100:.1f}% ===")
m=json.load(open("data/sigma_super_model.json", encoding="utf-8"))
print(f"MODEL: HA={m.get('best_home_adv')} SH={m.get('best_shrink')} ELO={m.get('best_elo_w')} Brier={round(m.get('brier',0),3)} Hit={round(m.get('hit',0)*100,1)}% n={m.get('n')} hist={m.get('total_history')}")
pred=list(csv.DictReader(open("data/sigma_mega_predictions.csv", encoding="utf-8")))
print(f"\nFORWARD: {len(pred)} matches - Top 10:")
for p in pred[:10]:
    print(f"{p['date']} {p['match']} xG {p['xG']} 1:{p['1']}% X:{p['X']}% 2:{p['2']}% BTTS {p['BTTS']}% Over {p['Over25']}% Top {p['top']}")
