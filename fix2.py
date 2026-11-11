import pathlib, re
p = pathlib.Path("index.html")
h = p.read_text(encoding="utf-8", errors="ignore")
# Remove extra top headers - keep first only
tops = list(re.finditer(r'<div class="top">.*?</div>\s*</div>', h, flags=re.DOTALL))
print(f"Top blocks: {len(tops)}")
if len(tops) > 1:
    for m in reversed(tops[1:]):
        h = h[:m.start()] + h[m.end():]
    print("Extra top removed")
# Fix image - replace any img with M avatar
h2 = re.sub(r'<img[^>]*>', '<div style="width:60px;height:60px;background:#fbbf24;color:#111;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:22px">M</div>', h, count=1)
if h2 != h:
    h = h2
    print("Image fixed to M")
# Hide audit
if "Real Audit" in h and "Advanced - Click" not in h:
    h = h.replace("Real Audit - Name Fix", "<details><summary>Real Audit - Advanced - Click to show</summary><div>Real Audit - Name Fix")
    h = h.replace("No more fake 0.00", "No more fake 0.00</div></details>")
    print("Audit hidden")
p.write_text(h, encoding="utf-8")
print("Part2 done")
