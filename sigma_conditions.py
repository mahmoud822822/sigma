import csv, json, math, pathlib
def poisson(lam,g):
    return (math.exp(-lam)*lam**g)/math.factorial(g)
# متوسط ركنيات الدوري - من احصائيات عامة
LEAGUE_CORNER={"England":(5.8,4.8),"Spain":(5.5,4.7),"Italy":(5.3,4.5),"Germany":(6.0,5.1),"Netherlands":(6.1,5.2),"France":(5.4,4.6),"Portugal":(5.4,4.5),"Belgium":(5.6,4.8),"Default":(5.5,4.7)}
def load_stats():
    p=pathlib.Path("data/sigma_team_stats.json")
    if p.exists():
        try: return json.load(open(p, encoding="utf-8"))
        except: return {}
    return {}
STATS=load_stats()
def find_team(name):
    low=name.lower().strip()
    for k in STATS:
        if k.lower()==low: return k
    for k in STATS:
        if low in k.lower() or k.lower() in low: return k
    return None
def team_attack(team, is_home):
    k=find_team(team)
    s=STATS.get(k, {}) if k else {}
    if s: return s.get("home_scored_avg" if is_home else "away_scored_avg", 1.4)
    return 1.55 if is_home else 1.25
def predict_conditions(home, away, league="Default"):
    ch, ca = LEAGUE_CORNER.get(league, LEAGUE_CORNER["Default"])
    # ظروف: هجوم الفريق / دفاع الخصم
    ha=team_attack(home, True); aa=team_attack(away, False)
    xg_h=round(max(0.2,min(3.5, ha*1.08)),2); xg_a=round(max(0.2,min(3.5, aa)),2)
    # 1X2 بال Poisson
    hw=x=d=aw=0.0
    for x in range(11):
        for y in range(11):
            p=poisson(xg_h,x)*poisson(xg_a,y)
            if x>y: hw+=p
            elif x==y: d+=p
            else: aw+=p
    # ركنيات: هجوم + دفاع
    cor_h=round(max(2,min(11, ch*(0.75+0.25*(ha/1.55)))),1); cor_a=round(max(2,min(11, ca*(0.75+0.25*(aa/1.25)))),1)
    tot_c=round(cor_h+cor_a,1)
    # رميات تماس - تقدير مش داتا حقيقية
    thr_h=round(max(12,min(35, 23*(0.8+0.2*(ha/1.55)))),1); thr_a=round(max(10,min(32, 19*(0.8+0.2*(aa/1.25)))),1)
    print(f"{home} vs {away} [{league}]")
    print(f"xG: {xg_h}-{xg_a}  1:{hw*100:.1f}% X:{d*100:.1f}% 2:{aw*100:.1f}%")
    print(f"Corners: Home {cor_h} - Away {cor_a} - Total {tot_c} - Over 9.5: {'Yes' if tot_c>9.5 else 'No'}")
    print(f"Throw-ins (ESTIMATE): Home {thr_h} - Away {thr_a} - Total {round(thr_h+thr_a,1)}")
    return xg_h, xg_a, cor_h, cor_a, thr_h, thr_a
if __name__=="__main__":
    h=input("Home: ").strip(); a=input("Away: ").strip(); lg=input("League (England/Spain/...): ").strip() or "Default"
    predict_conditions(h,a,lg)
def predict_conditions(home, away, league="Default"):
    ch, ca = LEAGUE_CORNER.get(league, LEAGUE_CORNER["Default"])
    ha=team_attack(home, True); aa=team_attack(away, False)
    xg_h=round(max(0.2,min(3.5, ha*1.08)),2); xg_a=round(max(0.2,min(3.5, aa)),2)
    hw=d=aw=0.0
    for x in range(11):
        for y in range(11):
            p=poisson(xg_h,x)*poisson(xg_a,y)
            if x>y: hw+=p
            elif x==y: d+=p
            else: aw+=p
    cor_h=round(max(2,min(11, ch*(0.75+0.25*(ha/1.55)))),1); cor_a=round(max(2,min(11, ca*(0.75+0.25*(aa/1.25)))),1)
    tot_c=round(cor_h+cor_a,1)
    thr_h=round(max(12,min(35, 23*(0.8+0.2*(ha/1.55)))),1); thr_a=round(max(10,min(32, 19*(0.8+0.2*(aa/1.25)))),1)
    print(f"{home} vs {away} [{league}]")
    print(f"xG: {xg_h}-{xg_a}  1:{hw*100:.1f}% X:{d*100:.1f}% 2:{aw*100:.1f}%")
    print(f"Corners: Home {cor_h} - Away {cor_a} - Total {tot_c} - Over 9.5: {'Yes' if tot_c>9.5 else 'No'}")
    print(f"Throw-ins (ESTIMATE): Home {thr_h} - Away {thr_a} - Total {round(thr_h+thr_a,1)}")
