import os
import csv
import requests
from datetime import datetime, timezone

FRED_API_KEY = os.environ["FRED_API_KEY"]

CSV_FILE = "macro.csv"

# 최초 전고점
# 나중에 실제 현재 전고점 값으로 수정
INITIAL_NDX_PEAK = 30608.130859375


def get_latest_fred_value(series_id):
    url = "https://api.stlouisfed.org/fred/series/observations"

    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 10,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    for observation in data["observations"]:
        if observation["value"] != ".":
            return {
                "date": observation["date"],
                "value": float(observation["value"]),
            }

    raise RuntimeError(f"No valid data found for {series_id}")


def get_latest_ndx():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/^NDX"

    params = {
        "range": "5d",
        "interval": "1d",
        "includePrePost": "false",
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()["chart"]["result"][0]

    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]

    latest = None

    for timestamp, close in zip(timestamps, closes):
        if close is None:
            continue

        date = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc
        ).strftime("%Y-%m-%d")

        latest = {
            "date": date,
            "value": float(close),
        }

    if latest is None:
        raise RuntimeError("No valid NDX data found")

    return latest


def load_existing_data():
    if not os.path.exists(CSV_FILE):
        return {}

    data = {}

    with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            data[row["date"]] = row

    return data


def save_data(data):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "date",
            "VIXCLS",
            "DGS10",
            "NDX",
            "NDX_PEAK",
            "NDX_DD",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()

        for date in sorted(data):
            writer.writerow({
                field: data[date].get(field, "")
                for field in fieldnames
            })


# --------------------------------------------------
# 1. FRED 데이터
# --------------------------------------------------

vix = get_latest_fred_value("VIXCLS")
dgs10 = get_latest_fred_value("DGS10")

print("VIXCLS:", vix)
print("DGS10:", dgs10)


# --------------------------------------------------
# 2. NDX 데이터
# --------------------------------------------------

ndx = get_latest_ndx()

print("NDX:", ndx)


# --------------------------------------------------
# 3. 기존 데이터 읽기
# --------------------------------------------------

data = load_existing_data()


# --------------------------------------------------
# 4. 기존 전고점 찾기
# --------------------------------------------------

ndx_peak = INITIAL_NDX_PEAK

for row in data.values():
    value = row.get("NDX_PEAK", "")

    if value:
        try:
            ndx_peak = max(ndx_peak, float(value))
        except ValueError:
            pass


# --------------------------------------------------
# 5. 새로운 NDX가 전고점을 돌파하면 갱신
# --------------------------------------------------

if ndx["value"] > ndx_peak:
    ndx_peak = ndx["value"]


# --------------------------------------------------
# 6. NDX 낙폭 계산
# --------------------------------------------------

ndx_dd = (ndx["value"] / ndx_peak - 1) * 100


# --------------------------------------------------
# 7. 날짜별 데이터 저장
# --------------------------------------------------

date = ndx["date"]

data[date] = {
    "date": date,
    "VIXCLS": vix["value"],
    "DGS10": dgs10["value"],
    "NDX": ndx["value"],
    "NDX_PEAK": ndx_peak,
    "NDX_DD": ndx_dd,
}


# --------------------------------------------------
# 8. 저장
# --------------------------------------------------

save_data(data)

print(f"Saved: {date}")
print(f"NDX: {ndx['value']}")
print(f"NDX_PEAK: {ndx_peak}")
print(f"NDX_DD: {ndx_dd:.2f}%")
