import csv, json, collections
rows=list(csv.DictReader(open("data/sigma_history.csv", encoding="utf-8")))
from collections import defaultdict
sc=defaultdict(list); cc=defaultdict(list); home_sc=defaultdict(list); away_sc=defaultdict(list); home_cc=defaultdict(list); away_cc=defaultdict(list)
for r in rows:
 h=r["home"]; a=r["away"]; hg=int(r["home_goals"]); ag=int(r["away_goals"])
 sc[h].append(hg); cc[h].append(ag); sc[a].append(ag); cc[a].append(hg)
 home_sc[h].append(hg); home_cc[h].append(ag); away_sc[a].append(ag); away_cc[a].append(hg)
out={}
for t in sc:
 n=len(sc[t]); btts=sum(1 for i in range(n) if sc[t][i]>0 and cc[t][i]>0)/n*100
 over=sum(1 for i in range(n) if sc[t][i]+cc[t][i]>=3)/n*100
 out[t]={"n":n,"scored_avg":round(sum(sc[t])/n,2),"conceded_avg":round(sum(cc[t])/n,2),"home_scored_avg":round(sum(home_sc[t])/max(1,len(home_sc[t])),2),"away_scored_avg":round(sum(away_sc[t])/max(1,len(away_sc[t])),2),"home_conceded_avg":round(sum(home_cc[t])/max(1,len(home_cc[t])),2),"away_conceded_avg":round(sum(away_cc[t])/max(1,len(away_cc[t])),2),"btts_rate":round(btts,1),"over25_rate":round(over,1)}
json.dump(out, open("data/sigma_team_stats.json","w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"Team Stats Real: {len(out)} teams - من التاريخ الحقيقي مش 2")
print(f"Top: {sorted(out.items(), key=lambda x: x[1]['scored_avg']-x[1]['conceded_avg'], reverse=True)[:3]}")
