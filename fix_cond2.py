import pathlib
p=pathlib.Path("sigma_conditions.py")
t=p.read_text()
t=t.replace("cor_h=round(max(2,min(14, ch*(ha/1.45))),1); cor_a=round(max(2,min(14, ca*(aa/1.25))),1)","cor_h=round(max(2,min(11, ch*(0.75+0.25*(ha/1.55)))),1); cor_a=round(max(2,min(11, ca*(0.75+0.25*(aa/1.25)))),1)")
t=t.replace("thr_h=round(23*(ha/1.45),1); thr_a=round(19*(aa/1.25),1)","thr_h=round(max(12,min(35, 23*(0.8+0.2*(ha/1.55)))),1); thr_a=round(max(10,min(32, 19*(0.8+0.2*(aa/1.25)))),1)")
p.write_text(t)
print("fixed2")
