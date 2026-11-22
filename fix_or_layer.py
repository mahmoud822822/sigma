import json, collections
print("=== fix_or_layer - تطبيق على اللايف ===")
try:
    d = json.load(open('data/sigma_site.json'))
    matches = d.get('matches', [])
    print(f"قبل: {len(matches)} ماتش")
    over=0; top=[]
    for m in matches:
        dc = float(m.get('dc_prob', 0) or 0)
        pick = m.get('dc_pick', '1X')
        cap = 86 if pick in ["1X","X2","DNB"] else 75
        # لو Elo مجهول، كاب 52%
        if m.get('elo_known') == False or m.get('elo_gap') is None:
            # منسيبش الكاب 52 يبوظ 1X، نطبقه على 1X2 بس لو كان 1X2
            if pick in ["1","X","2"]:
                cap = min(cap, 52)
        capped = min(dc, cap)
        m['dc_prob_capped'] = round(capped,1)
        m['dc_prob_original'] = dc
        if dc > cap: over+=1
        # قرار OR
        if capped >= 86 and pick in ["1X","X2","DNB"]:
            m['or_decision'] = "CANDIDATE-ON-CAP"
            top.append(m)
        else:
            m['or_decision'] = "ABSTAIN"
        # Composite تقديري
        m['value_rating'] = "A" if capped>=86 else "B" if capped>=80 else "C"
    # فلتر التنويع TOP_PICK: 2 لكل دوري / 3 لكل يوم، اقصى 12
    top_sorted = sorted(top, key=lambda x: -x['dc_prob_capped'])
    picked=[]; per_lg=collections.Counter(); per_dt=collections.Counter()
    for m in top_sorted:
        lg=m.get('league','?'); dt=m.get('date','?')
        if per_lg[lg]>=2 or per_dt[dt]>=3: 
            m['TOP_PICK']=False
            continue
        m['TOP_PICK']=True
        picked.append(m); per_lg[lg]+=1; per_dt[dt]+=1
        if len(picked)>=12: break
    for m in matches:
        if 'TOP_PICK' not in m: m['TOP_PICK']=False
    print(f"فوق الكاب: {over} | مرشحين على 86%: {len(top)} | TOP_PICK بعد التنويع: {len(picked)}")
    for p in picked:
        print(f" - TOP_PICK: {p.get('home')} vs {p.get('away')} | {p.get('league')} | {p.get('dc_prob_capped')}% | {p.get('value_rating')}")
    json.dump(d, open('data/sigma_site.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
    print("اتحفظ في data/sigma_site.json - اعمل ريفريش للموقع وشوف الكاب 86%")
except Exception as e:
    print("مشكلة:", e)
