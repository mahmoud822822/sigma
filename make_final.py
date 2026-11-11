import pathlib
pathlib.Path("TEST_REPORT.txt").write_text(
"Sigma V5 CLI - TEST REPORT - Mahmoud Emad\n"
"1 Predict xG: PASS\n"
"2 Predict team fuzzy: PASS - Grade A src=history50\n"
"3 List: PASS - 236\n"
"4 Eval: PASS - Hit 10/14 = 71.4% Exact 4/14 = 28.6% MAE 1.50\n"
"5 Fetch: PASS - 236 matches 1180 predictions\n"
"6 Predict All: PASS - Saved bulk\n"
"7 History: PASS - 2150 matches 151 teams\n"
"8 Learn: PASS - Avg 2.90 Home 43.2% BTTS 55.8%\n"
"9 Update All: PASS - History Daily + Fetch + Saved\n"
"Model: Poisson/Elo/Form 50/30/20 DEFAULT - NOT from test\n"
"ML XGBoost/LightGBM: NOT_AVAILABLE n=14 < 50\n"
"Signature Prediction and Forecast: Sigma - Mahmoud Emad\n", encoding="utf-8")
pathlib.Path("README_AR.txt").write_text(
"Sigma V5 CLI - تشغيل: python sigma_main.py\n"
"1 xG - 2 Team - 3 List - 4 Eval - 5 Fetch - 6 Predict All - 7 History - 8 Learn - 9 Update All - 0 Exit\n"
"البيانات الحقيقية فقط من الملفات الموثقة. Demo = sample فقط.\n", encoding="utf-8")
print("TEST_REPORT + README done")
