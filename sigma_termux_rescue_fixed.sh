#!/bin/bash
# Sigma RESCUE FIXED v2 - يصلح مشكلة Password prompt
# الفرق عن القديم: يستخدم x-access-token:TOKEN@ بدل TOKEN@ لوحده، و GIT_TERMINAL_PROMPT=0 عشان مايطلبش باسورد ابدا
# Run: bash sigma_termux_rescue_fixed.sh
set -e
cd ~/sigma-repo || exit 1
echo "=== Copy V46-V49 from Download ==="
for D in "/sdcard/Download/Meta AI" "/sdcard/Download"; do
  [ -d "$D" ] || continue
  for f in "$D"/sigma_x5f_v46_x5f_final.py*.txt "$D"/sigma_x5f_v47_x5f_verify_x5f_fix.py*.txt "$D"/sigma_x5f_v48_x5f_add_x5f_posters_x5f_basketball.py*.txt "$D"/sigma_x5f_v49_x5f_future_x5f_ai.py*.txt "$D"/sigma_x5f_v49_x5f_pre_x5f_upload_x5f_check.py*.txt; do
    [ -f "$f" ] || continue
    base=$(basename "$f")
    # decode sigma_x5f_ -> sigma_ , remove (1) (2) and .txt
    clean=$(echo "$base" | sed 's/sigma_x5f_/sigma_/g; s/ ([0-9]*)//g; s/\.txt$//')
    # keep newest only: if file exists and new is older, skip
    cp -f "$f" "$clean"
    echo "Copied $base -> $clean"
  done
done
for f in sigma_v46_final.py sigma_v47_verify_fix.py sigma_v48_add_posters_basketball.py sigma_v49_future_ai.py sigma_v49_pre_upload_check.py; do
  if [ ! -f "$f" ]; then echo "MISSING: $f - download it first, then run again"; exit 1; fi
done
echo "All 5 present. Good."
echo "=== Run V46-V49 ==="
python3 sigma_v46_final.py
python3 sigma_v47_verify_fix.py
python3 sigma_v48_add_posters_basketball.py
python3 sigma_v49_future_ai.py
echo "=== Pre-Upload Check (must PASS) ==="
python3 sigma_v49_pre_upload_check.py || { echo "BLOCKED - DO NOT PUSH. Fix FAIL above."; exit 1; }
echo "PASS - pushing..."
if [ ! -f ~/token.txt ]; then echo "MISSING ~/token.txt - run: bash sigma_setup_token.sh"; exit 1; fi
TOK=$(cat ~/token.txt | tr -d ' \n\r')
if [ -z "$TOK" ]; then echo "token.txt empty - re-run setup"; exit 1; fi
# FIX: use x-access-token, no password prompt
export GIT_TERMINAL_PROMPT=0
git remote set-url origin "https://x-access-token:${TOK}@github.com/mahmoud822822/sigma.git"
git add -A
git commit -m "Sigma V49 Future AI - all sports continuous brain" || echo "nothing to commit"
if git push origin main; then
  echo "DONE - PUSH OK. Open ?v=49"
else
  echo "PUSH FAILED - Token wrong/expired. Do NOT type password."
  echo "Generate new token (repo scope, ghp_...) and run sigma_setup_token.sh again, then run this script again."
  exit 1
fi
