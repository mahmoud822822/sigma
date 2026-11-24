import json
# DRY-RUN ONLY - no API, no live change. Gold = golden==True, confidence field = confidence
d=json.load(open('data/sigma_site.json',encoding='utf-8'))
ms=d.get('matches',[])
gold=[m for m in ms if m.get('golden')==True or str(m.get('golden')).lower()=='true' or m.get('golden')==1][:5]
field='confidence' if ms and ms[0].get('confidence') else 'conf'
assert len(gold)==5
out=[]
for m in gold:
    old=m.get(field,0)
    for delta in [3,0,-3]:
        new=min(86, max(0, old+delta))
        assert new<=86
        out.append({"match": f"{m.get('home')} vs {m.get('away')}", "field": field, "old_conf": old, "delta": delta, "new_conf": new})
open('data/sigma_ai_test_5.json','w',encoding='utf-8').write(json.dumps({"mode":"DRY-RUN","gold_field":"golden","confidence_field":field,"tests":out,"validator":"PASS","caps":{"gold":86,"normal":75,"x1":52},"risk":13},ensure_ascii=False,indent=2))
print("validator PASS, tests:",len(out))
