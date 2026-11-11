#!/bin/bash
# Sigma Termux Rescue - fixes screenshot errors: wrong folder + files not moved
# Run: bash sigma_termux_rescue.sh   (ONE command, do NOT paste all commands at once)
# It does: cd to repo -> find V46-V49 in Download/Meta AI -> rename encoded names -> run V46-V49 in order -> check -> push ONLY if PASS
# Token is NEVER printed. It is read from ~/token.txt only for push.
set -u
echo "=== 1) Where am I? ==="
pwd
echo "=== 2) Go to repo ==="
if [ -d "$HOME/sigma-repo" ]; then
  cd "$HOME/sigma-repo" || exit 1
else
  echo "No ~/sigma-repo found - cloning..."
  cd "$HOME" || exit 1
  git clone https://github.com/mahmoud822822/sigma.git sigma-repo || exit 1
  cd sigma-repo || exit 1
fi
pwd
ls -la | head -n 30
echo ""
echo "=== 3) Find downloaded Sigma files ==="
DL1="/sdcard/Download/Meta AI"
DL2="/sdcard/Download"
DL3="$HOME/storage/downloads"
for D in "$DL1" "$DL2" "$DL3"; do
  if [ -d "$D" ]; then echo "Checking: $D"; ls -1 "$D" 2>/dev/null | grep -i sigma | head -n 30; fi
done
echo ""
echo "=== 4) Copy + decode names (sigma_x5f_ -> sigma_) ==="
python3 - << 'PY'
import pathlib, shutil, re, os
cands = []
for d in ["/sdcard/Download/Meta AI", "/sdcard/Download", os.path.expanduser("~/storage/downloads")]:
    p = pathlib.Path(d)
    if p.exists():
        cands += list(p.glob("*sigma*")) + list(p.glob("*Sigma*"))
# decode: _x5f_ = _, _x2d_ = -, etc. _xHH_ hex
def decode(n):
    def repl(m):
        try: return chr(int(m.group(1), 16))
        except: return "_"
    return re.sub(r"_x([0-9a-fA-F]{2})_", repl, n)
want = {
  "sigma_v46": "sigma_v46_final.py",
  "sigma_v47": "sigma_v47_verify_fix.py",
  "sigma_v48": "sigma_v48_add_posters_basketball.py",
  "sigma_v49_future": "sigma_v49_future_ai.py",
  "sigma_v49_pre": "sigma_v49_pre_upload_check.py",
  "sigma_termux": "sigma_termux_rescue.sh",
}
for c in sorted(cands, key=lambda x: x.stat().st_mtime, reverse=True):
    dn = decode(c.name).lower()
    for k, target in want.items():
        if k in dn and c.is_file():
            dest = pathlib.Path.cwd() / target
            # only copy if dest missing or source newer
            if not dest.exists() or c.stat().st_mtime > dest.stat().st_mtime:
                shutil.copy2(c, dest)
                print(f"Copied {c.name} -> {target}")
            break
PY
echo ""
echo "=== 5) Do we have V46-V49 now? ==="
ls -lh sigma_v46_final.py sigma_v47_verify_fix.py sigma_v48_add_posters_basketball.py sigma_v49_future_ai.py sigma_v49_pre_upload_check.py 2>&1
for f in sigma_v46_final.py sigma_v47_verify_fix.py sigma_v48_add_posters_basketball.py sigma_v49_future_ai.py sigma_v49_pre_upload_check.py; do
  if [ ! -f "$f" ]; then echo "MISSING: $f - download it from Meta AI first, then run this script again"; exit 1; fi
done
echo "All 5 files present. Good."
echo ""
echo "=== 6) Disk check (you had 100% full before) ==="
df -h "$HOME" | tail -n 2
echo ""
echo "=== 7) Run in order - stops if any fails ==="
python3 sigma_v46_final.py || { echo "V46 FAILED - stop, do not push"; exit 1; }
python3 sigma_v47_verify_fix.py || { echo "V47 FAILED - stop"; exit 1; }
python3 sigma_v48_add_posters_basketball.py || { echo "V48 FAILED - stop"; exit 1; }
python3 sigma_v49_future_ai.py || { echo "V49 FAILED - stop"; exit 1; }
echo ""
echo "=== 8) Pre-upload gate - MUST say PASS ==="
python3 sigma_v49_pre_upload_check.py || { echo "CHECK BLOCKED - DO NOT PUSH. Fix the FAIL lines above."; exit 1; }
echo ""
echo "=== 9) Push (only because check PASSED) ==="
git status --short | head -n 40
git add data/sigma_bulk_predictions.json data/sigma_bulk_predictions_v44.json data/sigma_universal_fixtures.json data/sigma_basketball_fixtures.json data/sigma_poster_audit.json data/sigma_all_sports_master.json data/sigma_knowledge.json data/sigma_brain_state.json data/sigma_finished_archive.csv data/sigma_suspect.json data/sigma_team_stats.json data/sigma_league_stats.json index.html sigma_v44_view.html sigma_v46_final.py sigma_v47_verify_fix.py sigma_v48_add_posters_basketball.py sigma_v49_future_ai.py sigma_v49_pre_upload_check.py sigma_auto_fetch.py sigma_forecaster.py sigma_main.py sigma_real_verified.csv sigma_v44_final_one_shot.py 2>/dev/null || true
git add -A 2>/dev/null || true
git commit -m "Sigma V49 Future AI - all sports continuous brain, reverse-verify truth, pre-upload gate" || echo "Nothing new to commit"
# Push using token file silently (never printed)
if [ -f "$HOME/token.txt" ]; then
  echo "Using token from ~/token.txt (not shown)"
  git push https://$(cat "$HOME/token.txt")@github.com/mahmoud822822/sigma.git main || git push origin main
else
  git push origin main
fi
echo ""
echo "DONE. Open: https://mahmoud822822.github.io/sigma/?v=49"
