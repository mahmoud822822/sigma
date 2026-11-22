#!/bin/bash
echo "=== $(date) - بدء Pipeline ===" | tee -a logs.txt
python3 join_bulk_results.py >> logs.txt 2>&1
echo "--- join خلص ---" | tee -a logs.txt
python3 sigma_ai_system.py >> logs.txt 2>&1
echo "--- ai system خلص ---" | tee -a logs.txt
python3 sigma_or_v2.py >> logs.txt 2>&1
echo "--- or v2 خلص ---" | tee -a logs.txt
python3 fix_womens_leak.py >> logs.txt 2>&1
echo "--- womens leak خلص ---" | tee -a logs.txt
python3 fix_or_layer.py >> logs.txt 2>&1
echo "--- or layer خلص ---" | tee -a logs.txt
if [ -d ".git" ]; then
  git pull --rebase >> logs.txt 2>&1
  git add data/sigma_site.json data/sigma_site_women.json data/sigma_results_joined.json data/sigma_unmatched.json data/sigma_unified.json data/sigma_ensemble_weights.json logs.txt >> logs.txt 2>&1
  git commit -m "auto: pipeline $(date +%F-%H:%M) cap 86% + فصل السيدات" >> logs.txt 2>&1
  git push >> logs.txt 2>&1
  echo "--- push خلص ---" | tee -a logs.txt
fi
echo "=== $(date) - خلص Pipeline ===" | tee -a logs.txt
