import pathlib, glob
# 1 - create the guard that runs after every generation
cap = pathlib.Path("cap_after_generate.py")
cap.write_text('''import pathlib, json, re
p = pathlib.Path("data/sigma_site.json")
if not p.exists():
    print("no data file")
    exit(0)
s = p.read_text()
before_934 = s.count("93.4")
# text fix for 93.4 -> 86
s = s.replace("93.4", "86")
# fix Lens 77 -> 75 only near Lens
def fix_chunk(m):
    txt = m.group(0)
    if "Lens" in txt:
        txt = txt.replace("77", "75")
    return txt
s = re.sub(r".{0,300}Lens.{0,300}", fix_chunk, s, flags=re.DOTALL)
# numeric cap: load and cap 1X/X2/DNB to 86, 1X2 to 75
try:
    data = json.loads(s)
    def walk(o):
        if isinstance(o, dict):
            for k in list(o.keys()):
                v = o[k]
                lk = str(k).lower()
                if isinstance(v, (int, float)):
                    if ("1x" in lk or "x2" in lk or "dnb" in lk or "double" in lk) and v > 86:
                        o[k] = 86
                    if ("home_prob" in lk or "home_win" in lk or "1x2" in lk) and v > 75:
                        o[k] = 75
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(data)
    s = json.dumps(data, ensure_ascii=False)
except Exception as e:
    print("json walk skipped", e)
p.write_text(s)
print("cap done before 93.4:", before_934, "after:", s.count("93.4"))
''')
print("cap file created")
# 2 - patch workflow to run cap after generation
for wf in glob.glob(".github/workflows/*.yml") + glob.glob(".github/workflows/*.yaml"):
    t = pathlib.Path(wf).read_text()
    if "cap_after_generate.py" not in t:
        # add after any step that generates site, before upload/commit
        if "sigma_site.json" in t:
            t = t.replace("python3 cap_after_generate.py", "")
            # insert cap step before git add / git commit / upload
            for marker in ["- name: Commit", "- name: Upload", "git add"]:
                if marker in t:
                    t = t.replace(marker, "- name: Cap probabilities\\n        run: python3 cap_after_generate.py\\n      " + marker, 1)
                    break
            else:
                t += "\\n      - name: Cap probabilities\\n        run: python3 cap_after_generate.py\\n"
        else:
            t += "\\n      - name: Cap probabilities\\n        run: python3 cap_after_generate.py\\n"
        pathlib.Path(wf).write_text(t)
        print("patched", wf)
    else:
        print("already patched", wf)
