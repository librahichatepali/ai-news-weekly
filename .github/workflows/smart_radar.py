name: Daily News Bot

on:
  schedule:
    # 每天早上 8:00 自动运行一次 (UTC 0:00)
    - cron: '0 0 * * *'
  workflow_dispatch: # 允许你手动点击运行

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Execute script
        env:
          # 调用你刚刚在 Secrets 里存好的变量
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
        run: python main.py
