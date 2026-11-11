#!/bin/bash
# Sigma V50 RESCUE FIXED v3 - Clean + Analyze + Check + Push, no password prompt
# Run: bash sigma_v50_rescue_fixed_v3.sh
set -e
cd ~/sigma-repo || exit 1
echo "=== Copy V50 from Download (exact names) ==="
cp -f "/sdcard/Download/Meta AI/sigma_x5f_v50_x5f_analyze_x5f_fix_py.txt" sigma_v50_analyze_fix.py 2>/dev/null || cp -f "/sdcard/Download/Meta AI"/sigma_x5f_v50*analyze* sigma_v50_analyze_fix.py
cp -f "/sdcard/Download/Meta AI/sigma_x5f_v50_x5f_pre_x5f_upload_x5f_check_x5f_v2_py.txt" sigma_v50_pre_upload_check_v2.py 2>/dev/null || cp -f "/sdcard/Download/Meta AI"/sigma_x5f_v50*check* sigma_v50_pre_upload_check_v2.py
# .gitignore for token
printf "token.txt\n*.log\n" > .gitignore
echo "=== Run V50 Analyze (collect internal+external) ==="
python3 sigma_v50_analyze_fix.py
echo "=== Pre-Upload Check v2 (must PASS) ==="
python3 sigma_v50_pre_upload_check_v2.py || { echo "BLOCKED - DO NOT PUSH"; exit 1; }
echo "PASS - pushing..."
if [ ! -f ~/token.txt ]; then echo "MISSING ~/token.txt - run sigma_setup_token.sh"; exit 1; fi
TOK=$(cat ~/token.txt | tr -d ' \n\r')
export GIT_TERMINAL_PROMPT=0
git remote set-url origin "https://x-access-token:${TOK}@github.com/mahmoud822822/sigma.git"
git add -A
git commit -m "Sigma V50 - analyze+fix Golden/DEFAULT, internal+external data pack, all-sports view data, clean names" || echo "nothing to commit"
if git push origin main; then echo "DONE - PUSH OK. Open ?v=50"; else echo "PUSH FAILED - Token wrong. Do NOT type password."; exit 1; fi
