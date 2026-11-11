#!/bin/bash
# Sigma V50 RESCUE v4 - Clean + Analyze v2 + Check v2 + Push, no password prompt
# Run: bash sigma_v50_rescue_fixed_v4.sh
set -e
cd ~/sigma-repo || exit 1
cp -f "/sdcard/Download/Meta AI"/sigma_x5f_v50*clean* sigma_v50_clean_fix.py
cp -f "/sdcard/Download/Meta AI"/sigma_x5f_v50*analyze*fix*2* sigma_v50_analyze_fix_v2.py 2>/dev/null || cp -f "/sdcard/Download/Meta AI"/sigma_x5f_v50*analyze* sigma_v50_analyze_fix_v2.py
cp -f "/sdcard/Download/Meta AI"/sigma_x5f_v50*check* sigma_v50_pre_upload_check_v2.py
printf "token.txt\n*.log\n" > .gitignore
echo "=== CLEAN encoded ==="; python3 sigma_v50_clean_fix.py
echo "=== ANALYZE v2 ==="; python3 sigma_v50_analyze_fix_v2.py
echo "=== CHECK v2 ==="; python3 sigma_v50_pre_upload_check_v2.py || { echo "BLOCKED - DO NOT PUSH"; exit 1; }
echo "PASS - pushing..."
if [ ! -f ~/token.txt ]; then echo "MISSING ~/token.txt"; exit 1; fi
TOK=$(cat ~/token.txt | tr -d ' \n\r')
export GIT_TERMINAL_PROMPT=0
git remote set-url origin "https://x-access-token:${TOK}@github.com/mahmoud822822/sigma.git"
git add -A
git commit -m "Sigma V50 - clean 5 encoded files, fix Golden/DEFAULT detection, internal+external data pack" || echo "nothing to commit"
if git push origin main; then echo "DONE - PUSH OK. Open ?v=50"; else echo "PUSH FAILED - Token wrong. Do NOT type password."; exit 1; fi
