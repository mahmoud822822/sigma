import pathlib
p=pathlib.Path("sigma_make_index_full.py")
t=p.read_text()
t=t.replace("sigma_mega_predictions.csv","sigma_mega_conditions.csv")
if "Corners" not in t:
    t=t.replace("<th>BTTS</th>","<th>BTTS</th><th>Corners</th><th>Throw</th>")
    t=t.replace("<td>${r.BTTS||''}%</td>","<td>${r.BTTS||''}%</td><td>${r.Corners||''}</td><td>${r.Throw||''}</td>")
p.write_text(t)
print("site patched")
