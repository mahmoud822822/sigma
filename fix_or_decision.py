import pathlib
p = pathlib.Path('sigma_or_engine.py')
t = p.read_text()
old = """def or_decision(prob_capped, ev, pick_type):
    risk = 100 - prob_capped
    if risk > 13: return f"ABSTAIN - مخاطرة {risk:.1f}% فوق 13%"
    if ev < 0: return f"ABSTAIN - EV سالب {ev:.3f}"
    if prob_capped >= 86 and pick_type in ["1X","X2"]: return "HOLD - على الكاب، راجع EV"
    return "SAFE - تحت القيود\""""
new = """def or_decision(prob_capped, ev, pick_type, anomaly_reasons=None):
    if anomaly_reasons:
        return f"ABSTAIN - شذوذ: {anomaly_reasons}"
    if ev < 0:
        return f"ABSTAIN - EV سالب {ev:.3f}"
    if pick_type in ["1X","X2","DNB"]:
        if prob_capped >= 86:
            return "SAFE-ON-CAP - على الكاب 86% + EV موجب"
        risk = 100 - prob_capped
        return f"ABSTAIN - مخاطرة {risk:.1f}% تحت الكاب 86%"
    else:
        if prob_capped >= 75:
            return "SAFE-ON-CAP - على الكاب 75% + EV موجب"
        risk = 100 - prob_capped
        return f"ABSTAIN - مخاطرة {risk:.1f}% تحت الكاب 75%\""""
if old in t:
    p.write_text(t.replace(old, new))
    print("تم اصلاح or_decision")
else:
    print("مش لاقي الدالة القديمة - افتح الملف وتأكد من اسمها")
