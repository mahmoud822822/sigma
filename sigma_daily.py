import subprocess, sys
def run(cmd):
    print(f">>> {cmd}"); r=subprocess.run([sys.executable]+cmd); print(f"exit {r.returncode}")
print("Sigma Daily: Fetch + Predict + Track")
run(["sigma_auto_fetch.py"])
run(["sigma_predict_next.py"])
run(["sigma_track.py"])
print("Daily done")
