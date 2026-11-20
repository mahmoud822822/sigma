wf_path = ".github/workflows/sigma-auto-update.yml"
with open(wf_path, "r", encoding="utf-8") as f:
    wf = f.read()

wf = wf.replace("0 */6 * * *", "0 */3 * * *")

with open(wf_path, "w", encoding="utf-8") as f:
    f.write(wf)

print("SUCCESS: Workflow restored to every 3 hours (0 */3 * * *)!")
