import json
d = json.load(open('data/sigma_site.json'))
m = d.get('matches', [])
w = [x for x in m if any(k in str(x.get('league','')).lower() for k in ["liga-f","women","female","wsl","frauen","feminine"])]
k = [x for x in m if x not in w]
print(f"قبل: {len(m)} | بعد: {len(k)} رجال | {len(w)} سيدات")
for x in w:
    print(f" - اتنقل: {x.get('home')} vs {x.get('away')} | {x.get('league')}")
d['matches'] = k
json.dump(d, open('data/sigma_site.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump({"matches": w}, open('data/sigma_site_women.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
