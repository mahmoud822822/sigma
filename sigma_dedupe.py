import re, pathlib
p=pathlib.Path('index.html')
h=p.read_text()
cards=re.findall(r"<div class='card'>.*?</div>", h, flags=re.DOTALL)
seen=set(); uniq=[]
for c in cards:
 k=c[:120]
 if k not in seen:
  seen.add(k); uniq.append(c)
print('before',len(cards),'after',len(uniq))
