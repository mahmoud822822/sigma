# Sigma Collect V19 - Multi Source Real Only - Mahmoud Emad
# Sources: football-data.co.uk CSV + football-data.org API + API-Football + Understat
# No scraping of SofaScore/Flashscore - TOS
# Every row has source column - No invented data
import os, csv, json, urllib.request, urllib.error, time
from pathlib import Path
BASE=Path(__file__).parent; DATA=BASE/"data"; DATA.mkdir(exist_ok=True)
def save(rows, name):
    if not rows: print(f"{name}: 0 rows - skipped, no fake"); return
    p=DATA/name
    with open(p,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"Saved {name}: {len(rows)} real rows")
def fetch_co_uk():
    # football-data.co.uk - free CSV - E0=England, SP1=Spain, I1=Italy, B1=Germany, F1=France
    urls=[("E0","2425"),("E0","2324"),("SP1","2425"),("I1","2425"),("B1","2425"),("F1","2425")]
    rows=[]
    for code,season in urls:
        url=f"https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
        try:
            with urllib.request.urlopen(url,timeout=20) as r:
                txt=r.read().decode(errors="ignore").splitlines()
                rd=list(csv.DictReader(txt))
                for x in rd:
                    if not x.get("HomeTeam") or not x.get("AwayTeam"): continue
                    rows.append({"date":x.get("Date",""),"home":x.get("HomeTeam",""),"away":x.get("AwayTeam",""),"home_goals":x.get("FTHG",""),"away_goals":x.get("FTAG",""),"league":code,"season":season,"source":"football-data.co.uk","status":"FINISHED"})
            print(f"co.uk {code} {season}: ok")
        except Exception as e: print(f"co.uk {code} fail {e}")
        time.sleep(0.5)
    save(rows,"sigma_co_uk.csv")
    return rows
def fetch_understat():
    # Understat - no official API, JSON embedded in page - 6 leagues, 2014-2025
    # We fetch team xG per season - if blocked, we skip, no fake
    leagues=["epl","la_liga","bundesliga","serie_a","ligue_1"]
    rows=[]
    for lg in leagues:
        url=f"https://understat.com/league/{lg}/2024"
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=20) as r:
                html=r.read().decode(errors="ignore")
                # Understat puts data in <script> JSON - we only extract if found, else skip
                if "teamsData" in html:
                    print(f"Understat {lg}: page ok - parse manually in notebook, no fake rows yet")
                else:
                    print(f"Understat {lg}: no teamsData - skipped")
        except Exception as e: print(f"Understat {lg} fail {e} - skipped, no fake")
        time.sleep(1)
    print("Understat: manual parse needed - see note below, no invented xG")
    return rows
def fetch_football_data_org():
    token=os.environ.get("FOOTBALL_DATA_TOKEN","").strip()
    if len(token)!=32:
        print("football-data.org: no token - skip. Get free token from football-data.org - no fake")
        return []
    from datetime import date, timedelta
    today=date.today(); nxt=today+timedelta(days=14)
    url=f"https://api.football-data.org/v4/matches?dateFrom={today}&dateTo={nxt}&competitions=2021,2014,2019,2002,2015,2003,2017,2004"
    req=urllib.request.Request(url,headers={"X-Auth-Token":token})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            ms=json.loads(r.read().decode()).get("matches",[])
        rows=[]
        for m in ms:
            rows.append({"date":m["utcDate"][:10],"home":m["homeTeam"]["name"],"away":m["awayTeam"]["name"],"home_goals":(m["score"]["fullTime"]["home"] if m["score"]["fullTime"] else ""),"away_goals":(m["score"]["fullTime"]["away"] if m["score"]["fullTime"] else ""),"league":m["competition"]["name"],"season":"","source":"football-data.org","status":m["status"]})
        save(rows,"sigma_api_org.csv")
        return rows
    except Exception as e: print(f"football-data.org fail {e}"); return []
def fetch_api_football():
    key=os.environ.get("API_FOOTBALL_KEY","").strip()
    if not key:
        print("API-Football: no key - skip. Get free 100/day from api-football.com - no fake")
        return []
    # API-Football v3 - fixtures next 14 days - free 100/day
    import urllib.parse
    from datetime import date, timedelta
    today=date.today(); rows=[]
    for i in range(0,14,7):
        d=today+timedelta(days=i)
        url=f"https://v3.football.api-sports.io/fixtures?date={d.isoformat()}&league=39&season=2024"
        req=urllib.request.Request(url,headers={"x-apisports-key":key})
        try:
            with urllib.request.urlopen(req,timeout=20) as r:
                data=json.loads(r.read().decode())
                for f in data.get("response",[]):
                    rows.append({"date":f["fixture"]["date"][:10],"home":f["teams"]["home"]["name"],"away":f["teams"]["away"]["name"],"home_goals":f["goals"]["home"],"away_goals":f["goals"]["away"],"league":f["league"]["name"],"season":str(f["league"]["season"]),"source":"api-football","status":f["fixture"]["status"]["short"]})
            print(f"API-Football {d}: ok")
        except Exception as e: print(f"API-Football fail {e}")
        time.sleep(1)
    save(rows,"sigma_api_football.csv")
    return rows
def main():
    print("Sigma Collect V19 - Real Only")
    a=fetch_co_uk(); b=fetch_football_data_org(); c=fetch_api_football(); fetch_understat()
    allr=a+b+c
    if allr:
        # dedupe by date+home+away, keep first source
        seen=set(); uniq=[]
        for r in allr:
            k=(r["date"],r["home"],r["away"])
            if k not in seen: seen.add(k); uniq.append(r)
        save(uniq,"sigma_merged.csv")
        print(f"Merged total real: {len(uniq)} - sources kept in source column")
    else:
        print("No source available - check tokens / internet - no fake file created")
if __name__=="__main__": main()
