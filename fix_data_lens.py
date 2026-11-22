import pathlib, json
p = pathlib.Path("data/sigma_site.json")
s = p.read_text()
print("before 93.4:", s.count("93.4"))
print("before 77 Lens check:", s.count("77"))
# fix text values
s = s.replace("93.4", "86")
# fix JSON numbers: cap any 1X/X2 over 86, fix Lens 77 to 75 in text around Lens
# simple safe pass: replace 77 only when near Lens in same chunk
import re
def fix_chunk(m):
    txt = m.group(0)
    if "Lens" in txt:
        txt = txt.replace("77", "75")
    return txt
s = re.sub(r".{0,200}Lens.{0,200}", fix_chunk, s, flags=re.DOTALL)
p.write_text(s)
s2 = p.read_text()
print("after 93.4:", s2.count("93.4"))
print("done data fix")
