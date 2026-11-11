import json, pathlib
mp={"PL":"England Premier League","ELC":"England Championship","PD":"Spain La Liga","SA":"Italy Serie A","BL1":"Germany Bundesliga","FL1":"France Ligue 1","DED":"Netherlands Eredivisie","PPL":"Portugal Primeira Liga","BSA":"Brazil Serie A","CL":"Europe Champions League","CLI":"South America Libertadores","WC":"World Cup","EC":"Euro Championship"}
for fn in ["data/sigma_next_month.json","data/sigma_all_13_matches.json"]:
 p=pathlib.Path(fn)
 if not p.exists(): continue
 d=json.loads(p.read_text())
 print(fn, "done")
print(mp["PD"])
