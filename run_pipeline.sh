#!/bin/bash
if [ -d ".git" ]; then
  git pull --rebase
fi
echo "=== $(date) - بدء Pipeline ===" | tee -a logs.txt
python3 join_bulk_results.py >> logs.txt 2>&1
echo "--- join خلص - كود الخروج: $? ---" | tee -a logs.txt
python3 sigma_ai_system.py >> logs.txt 2>&1
python3 sigma_or_v2.py >> logs.txt 2>&1
python3 fix_womens_leak.py >> logs.txt 2>&1
python3 fix_or_layer.py >> logs.txt 2>&1
if [ -d ".git" ]; then
  git add -A -- ':!logs.txt'
  git commit -m "auto: pipeline $(date +%F-%H:%M) cap 86%" || echo "مفيش جديد للـ commit" >> logs.txt 2>&1
  git push >> logs.txt 2>&1
  echo "--- push خلص ---" | tee -a logs.txt
fi
echo "=== $(date) - خلص Pipeline ===" | tee -a logs.txt
