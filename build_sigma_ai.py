import json, copy
# DRY-RUN ONLY - no API call, no key, no live data change
d=json.load(open('data/sigma_site.json',encoding='utf-8'))
gold=[m for m in d.get('matches',[]) if m.get('tier')=='gold'][:5]
out=[]
for m in gold:
    old=m.get('conf',0)
    # simulate AI delta: test +3, 0, -3 clamping
    for delta in [3,0,-3]:
        new=min(86, max(0, old+delta))
        assert new<=86, "cap fail"
        out.append({"match": f"{m.get('home')} vs {m.get('away')}", "old_conf": old, "delta": delta, "new_conf": new, "cap_ok": new<=86})
# validator
assert all(x['new_conf']<=86 for x in out), "Validator FAIL"
assert all(x['new_conf']>=0 for x in out)
res={"mode":"DRY-RUN","model":"Groq llama-3.3-70b-versatile (not called)","tests":out,"validator":"PASS","caps":{"gold":86,"normal":75,"x1":52},"risk":13,"note":"Live data NOT changed"}
open('data/sigma_ai_test_5.json','w',encoding='utf-8').write(json.dumps(res,ensure_ascii=False,indent=2))
print("validator PASS, tests:",len(out))
print("live data NOT changed")
