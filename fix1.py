import pathlib
p = pathlib.Path("index.html")
h = p.read_text(encoding="utf-8", errors="ignore")
parts = h.split("Signature Prediction and Forecast: Sigma")
print(f"Headers: {len(parts)-1}")
if len(parts) > 2:
    h = parts[0] + "Signature Prediction and Forecast: Sigma" + parts[1] + "".join(parts[3:])
    print("Duplicate removed")
p.write_text(h, encoding="utf-8")
print("Part1 done")
