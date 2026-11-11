#!/usr/bin/env python3
# Sigma Engine V5 - Multi-Model Ensemble + Explain + Ranking + Learning
# Poisson + Dixon-Coles + Elo + Form -> Ensemble. stdlib only. No invented success rates.
# Mahmoud Emad - Sigma Platform V5 - DO NOT UPLOAD YET - Build & Test First
import math, csv, json, statistics
from pathlib import Path

# ---------- Base ----------
LEAGUE_BASE = {"England":(1.65,1.35),"Spain":(1.55,1.20),"Italy":(1.50,1.20),"Germany":(1.70,1.40),"Netherlands":(1.70,1.40),"France":(1.55,1.25),"Portugal":(1.55,1.20),"Belgium":(1.60,1.30),"Default":(1.55,1.25)}
def poisson(k, lam):
    if lam<=0: return 1.0 if k==0 else 0.0
    return math.exp(-lam)*(lam**k)/math.factorial(k)

def dixon_coles_matrix(lam_h, lam_a, rho=-0.08, max_g=6):
    # Dixon-Coles: تصحيح للنتائج المنخفضة 0-0, 1-0, 0-1, 1-1 - مش Poisson مستقل تماما
    m=[[poisson(i,lam_h)*poisson(j,lam_a) for j in range(max_g+1)] for i in range(max_g+1)]
    # تعديل 4 خلايا فقط
    if rho!=0:
        # tau function
        def tau(x,y):
            if x==0 and y==0: return 1 - lam_h*lam_a*rho
            if x==0 and y==1: return 1 + lam_h*rho
            if x==1 and y==0: return 1 + lam_a*rho
            if x==1 and y==1: return 1 - rho
            return 1.0
        for i,j in [(0,0),(0,1),(1,0),(1,1)]:
            m[i][j]*=tau(i,j)
    # إعادة تطبيع
    s=sum(sum(row) for row in m)
    return [[v/s for v in row] for row in m]

def probs_from_matrix(m):
    ph=pd=pa=over15=over25=over10=btts=0.0
    for i in range(len(m)):
        for j in range(len(m[0])):
            p=m[i][j]
            if i>j: ph+=p
            elif i==j: pd+=p
            else: pa+=p
            tot=i+j
            if tot>1.5: over15+=p
            if tot>2.5: over25+=p
            if tot>1: over10+=p
            if i>0 and j>0: btts+=p
    # 2H Over 0.5 - تقدير محافظ من Late 30% + Poisson 2H
    p2h=min(0.97, over10*0.55+0.30)
    raw={"1":ph,"X":pd,"2":pa,"Over 1.5":over15,"Over 2.5":over25,"Over 1":over10,"BTTS":btts,"2H Over 0.5":p2h,"1X":ph+pd,"X2":pd+pa,"12":ph+pa}
    # Shrink 1X2 نحو 33% لمنع الثقة الزائدة
    for k in ("1","X","2"):
        raw[k]=raw[k]*0.85+0.333*0.15
    s=raw["1"]+raw["X"]+raw["2"]
    for k in ("1","X","2"): raw[k]/=s
    return {k:round(v,3) for k,v in raw.items()}

# ---------- Team Strength + Elo + Form ----------
def build_team_db(verified_rows):
    # من Verified 14: هجوم/دفاع + Elo + فورم
    att={}; df={}; cnt={}; elo={}; form={}
    for r in verified_rows:
        try:
            home,away=[s.strip() for s in r["match"].split(" vs ")]
            rh,ra=int(r["real_home"]),int(r["real_away"])
        except: continue
        for t,sc,co in [(home,rh,ra),(away,ra,rh)]:
            att[t]=att.get(t,0)+sc; df[t]=df.get(t,0)+co; cnt[t]=cnt.get(t,0)+1
            elo.setdefault(t,1500)
        # Elo update K=20
        eh=1/(1+10**((elo[away]-elo[home])/400))
        sa=1 if rh>ra else (0.5 if rh==ra else 0)
        elo[home]+=20*(sa-eh); elo[away]+=20*((1-sa)-(1-eh))
        form.setdefault(home,[]).append("W" if rh>ra else ("D" if rh==ra else "L"))
        form.setdefault(away,[]).append("W" if ra>rh else ("D" if ra==rh else "L"))
    db={}
    for t in cnt:
        n=cnt[t]
        raw_att=att[t]/n; raw_def=df[t]/n
        # Shrinkage: (n*raw + 2*league_avg) / (n+2) - لو لعب ماتش واحد، نرجع 66% للدوري
        shr_att=round((n*raw_att + 2*1.55)/(n+2),2)
        shr_def=round((n*raw_def + 2*1.25)/(n+2),2)
        db[t]={"attack":shr_att,"defense":shr_def,"raw_attack":round(raw_att,2),"raw_defense":round(raw_def,2),"n":n,"elo":round(elo.get(t,1500)),"form":form.get(t,[])[-3:]}
    return db

def elo_probs(elo_h, elo_a):
    # Elo -> 1X2 عبر logistic مع Draw ثابت 0.24 (من التاريخ)
    eh=1/(1+10**((elo_a-elo_h)/400))
    # نحول expected score لـ 1X2: P(Home)= eh*0.76, P(Away)=(1-eh)*0.76, Draw=0.24
    return {"1":round(eh*0.76,3),"X":0.24,"2":round((1-eh)*0.76,3)}

def form_probs(form_h, form_w):
    # Form: W=1, D=0.5, L=0
    def score(f):
        if not f: return 0.5
        m={"W":1,"D":0.5,"L":0}
        return sum(m[x] for x in f)/len(f)
    sh, sa = score(form_h), score(form_w)
    tot=sh+sa if sh+sa>0 else 1
    return {"1":round(sh/tot*0.76,3),"X":0.24,"2":round(sa/tot*0.76,3)}

def ensemble(poisson_probs, elo_p, form_p, weights=(0.50,0.30,0.20)):
    out={}
    for k in ("1","X","2"):
        out[k]=round(poisson_probs[k]*weights[0]+elo_p[k]*weights[1]+form_p[k]*weights[2],3)
    s=sum(out.values())
    for k in out: out[k]=round(out[k]/s,3)
    # باقي الأسواق من Poisson فقط (Elo/Form لا تحسب Over/BTTS)
    for k in ("Over 1.5","Over 2.5","Over 1","BTTS","2H Over 0.5","1X","X2","12"):
        out[k]=poisson_probs[k]
    out["1X"]=round(out["1"]+out["X"],3); out["X2"]=round(out["X"]+out["2"],3); out["12"]=round(out["1"]+out["2"],3)
    return out

def predict_match(home, away, league, team_db, n_verified=14):
    base_h, base_a = LEAGUE_BASE.get(league, LEAGUE_BASE["Default"])
    hs=team_db.get(home); as_=team_db.get(away)
    # Poisson lambda مع shrinkage
    if hs and hs["n"]>=2:
        lam_h = base_h*(hs["attack"]/1.55)*(as_["defense"]/1.25 if as_ else 1.0)*1.08*0.85 + base_h*0.15
    else: lam_h = base_h*1.08
    if as_ and as_["n"]>=2:
        lam_a = base_a*(as_["attack"]/1.25)*(hs["defense"]/1.55 if hs else 1.0)*0.85 + base_a*0.15
    else: lam_a = base_a
    lam_h=max(0.2,min(3.5,round(lam_h,2))); lam_a=max(0.2,min(3.5,round(lam_a,2)))
    # 3 نماذج
    m_poisson = probs_from_matrix(dixon_coles_matrix(lam_h, lam_a))
    elo_h = hs["elo"] if hs else 1500; elo_a = as_["elo"] if as_ else 1500
    m_elo = elo_probs(elo_h, elo_a)
    m_form = form_probs(hs["form"] if hs else [], as_["form"] if as_ else [])
    ens = ensemble(m_poisson, m_elo, m_form)
    # جودة الداتا: full لو الفريقين لعبوا 2+، partial لو الدوري معروف (عندنا متوسط دوري حقيقي)، limited لو الدوري نفسه Default/مجهول
    hs_ok = hs and hs["n"]>=2
    as_ok = as_ and as_["n"]>=2
    if hs_ok and as_ok: dq="full"
    elif league!="Default": dq="partial"  # الدوري معروف = متوسط دوري حقيقي، فمش limited حتى لو مفيش تاريخ للفريق
    else: dq="limited"
    # ثقة معايرة - مش نسبة نجاح مخترعة: = احتمال النتيجة الأرجح بعد Shrink + خصم بسيط لو الداتا محدودة
    maxp=max(ens["1"],ens["X"],ens["2"])
    dq_penalty={"full":0.0,"partial":0.03,"limited":0.07}[dq]
    sample_penalty=0.02 if n_verified<20 else 0.0
    confidence=round(max(0.30,min(0.92, maxp - dq_penalty - sample_penalty)),3)
    # مخاطر وتناقضات
    risks=[]; contradictions=[]
    if maxp<0.45: risks.append("1X2 متوازن - لا أفضلية واضحة")
    if dq=="limited": risks.append("داتا محدودة عن الفريقين")
    if abs(lam_h-lam_a)<0.15: risks.append("قوة متقاربة")
    if ens["Over 2.5"]>0.60 and ens["BTTS"]<0.45: contradictions.append("Over 2.5 مرتفع لكن BTTS منخفض - فريق واحد مسيطر، BTTS خطر")
    if m_poisson["1"]>0.50 and m_elo["1"]<0.35: contradictions.append("Poisson يقول فوز بيت، Elo يقول العكس - النماذج مختلفة")
    if m_poisson["2"]>0.50 and m_elo["2"]<0.35: contradictions.append("Poisson يقول فوز ضيف، Elo يقول العكس - النماذج مختلفة")
    level="HIGH" if len(risks)>=2 or dq=="limited" else ("MEDIUM" if risks or contradictions else "LOW")
    # هل يستحق التوقع؟
    worth = not (dq=="limited" and level=="HIGH" and confidence<0.55)
    # Ranking Score: جودة داتا * ثقة - عقوبة مخاطر
    dq_score={"full":1.0,"partial":0.75,"limited":0.50}[dq]
    ranking=round(max(0,min(100, dq_score*confidence*100 - (20 if level=="HIGH" else (10 if level=="MEDIUM" else 0)))),1)
    # تفسير Sigma AI - بالعربي
    explain = f"هجوم {home} {hs['attack'] if hs else 'غير معروف'} / دفاع {hs['defense'] if hs else '؟'} (Elo {elo_h}) ضد هجوم {away} {as_['attack'] if as_ else 'غير معروف'} / دفاع {as_['defense'] if as_ else '؟'} (Elo {elo_a}). xG المتوقع {lam_h} - {lam_a}. "
    if dq=="limited": explain+="الداتا محدودة، فالثقة مكبوحة والتوقعات الخطر مخفية. "
    if contradictions: explain+="تناقض بين النماذج: " + " | ".join(contradictions) + ". "
    if not worth: explain+="هذه المباراة لا تستحق التوقع الآمن - الأفضل تخطيها."
    else: 
        best = "Over 1" if ens['Over 1']>0.75 else "X2 / 1X"
        best_p = ens['Over 1'] if ens['Over 1']>0.75 else max(ens['X2'],ens['1X'])
        explain+=f"أفضل سوق آمن: {best} باحتمال {int(best_p*100)}% (ثقة 1X2: {int(confidence*100)}% - 1X2 أصعب من Over). "
    return {
        "match":f"{home} vs {away}","league":league,
        "lam_h":lam_h,"lam_a":lam_a,"exp_total":round(lam_h+lam_a,2),
        "attack_defense":{"home_attack":hs["attack"] if hs else None,"home_defense":hs["defense"] if hs else None,"away_attack":as_["attack"] if as_ else None,"away_defense":as_["defense"] if as_ else None,"home_elo":elo_h,"away_elo":elo_a,"home_form":hs["form"] if hs else [],"away_form":as_["form"] if as_ else []},
        "models":{"poisson":m_poisson,"elo":m_elo,"form":m_form,"ensemble":ens},
        "data_quality":dq,"confidence":confidence,"risk_level":level,"risks":risks,"contradictions":contradictions,
        "worth_predicting":worth,"ranking_score":ranking,"explain":explain
    }

def brier(probs_list, outcomes):
    s=0
    for probs,y in zip(probs_list,outcomes):
        one=[0,0,0]; one[y]=1
        s+=sum((p-o)**2 for p,o in zip(probs,one))
    return round(s/len(probs_list) if probs_list else 0,4)
def logloss(probs_list,outcomes):
    import math as _m
    s=0
    for probs,y in zip(probs_list,outcomes):
        s+=-_m.log(max(1e-15,min(1-1e-15,probs[y])))
    return round(s/len(probs_list) if probs_list else 0,4)
def mae(pred,real):
    return round(statistics.mean([abs(p-r) for p,r in zip(pred,real)]) if pred else 0,3)

if __name__=="__main__":
    print("Sigma Engine V5 - Poisson + Dixon-Coles + Elo + Form Ensemble")
    print(predict_match("Test Home","Test Away","England",{},14)["explain"])
