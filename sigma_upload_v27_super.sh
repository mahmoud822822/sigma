cp index.html index_v24_backup.html && echo "Backup done"
cp /sdcard/Download/sigma_v27_super_ai.html index.html && echo "Copied V27" || echo "Check Downloads name"
ls -lh index.html
python sigma_fix_alias_v26_final.py
python sigma_embed_data.py
python sigma_embed_2027.py
ls -lh index.html
grep -c "sigma-embedded-data" index.html && echo "2026 OK"
grep -c "sigma-embedded-2027" index.html && echo "2027 OK"
git add -f index.html index_v24_backup.html
git commit -m "V27 Super AI - All Data Fed - Hidden Tech"
git push
echo "Done - https://mahmoud822822.github.io/sigma/?v=27"
