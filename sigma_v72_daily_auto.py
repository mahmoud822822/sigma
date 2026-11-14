name: Sigma Auto - 3h + Daily 4pm Cairo
on:
  schedule:
    - cron: "0 */3 * * *"
    - cron: "0 14 * * *"
  workflow_dispatch:
jobs:
  run-3h:
    if: github.event_name == 'schedule' && github.event.schedule != '0 14 * * *'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Run Sigma V69 - 3h Fixes + Collect
        run: python3 sigma_v69_fix_and_automation.py
      - name: Commit only reports - NEVER Bulk
        run: |
          git config user.name "Sigma Bot"
          git config user.email "sigma@mahmoud.local"
          git add sigma_v69_fix_and_automation.py data/sigma_v69_report.json data/sigma_v69_fixed_predictions.json data/sigma_v69_snapshots.jsonl || true
          git commit -m "Sigma V69 - 3h auto" || echo "no change"
          git push || echo "push failed"
  run-daily:
    if: github.event.schedule == '0 14 * * *' || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Run Sigma V72 - Daily Auto Update 4pm Cairo
        run: python3 sigma_v72_daily_auto.py
      - name: Commit daily report - NEVER Bulk
        run: |
          git config user.name "Sigma Bot"
          git config user.email "sigma@mahmoud.local"
          git add sigma_v72_daily_auto.py data/sigma_daily_report.json data/sigma_daily_log.jsonl || true
          git commit -m "Sigma V72 - Daily auto 4pm" || echo "no change"
          git push || echo "push failed"
