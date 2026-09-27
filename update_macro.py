name: Update Macro Data

on:
  workflow_dispatch:
  schedule:
    - cron: "30 22 * * 1-5"

jobs:
  update:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Install dependencies
        run: |
          pip install requests

      - name: Update macro data
        env:
          FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
        run: |
          python update_macro.py
