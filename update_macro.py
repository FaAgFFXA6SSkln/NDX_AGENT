import os
import csv
import requests
from datetime import datetime, timezone, timedelta

FRED_API_KEY = os.environ["FRED_API_KEY"]

CSV_FILE = "macro.csv"

# 최초 전고점
INITIAL_NDX_PEAK = 26000.0


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


def get_ndx_data():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/^NDX"

    params = {
        "range": "1y",
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

    data = []

    for timestamp, close in zip(timestamps, closes):
        if close is None:
            continue

        date = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc
        ).strftime("%Y-%m-%d")

        data.append({
            "date": date,
            "close": float(close),
        })

    if len(data) < 200:
        raise RuntimeError(
            f"Not enough NDX data for 200-day SMA: {len(data)} days"
        )

    return data


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
                "DGS10_3M_CHANGE",
                "NDX",
                "NDX_SMA200",
                "NDX_PEAK",
                "NDX_DD",
                "QLD_TARGET",
            ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

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

ndx_data = get_ndx_data()

latest_ndx = ndx_data[-1]

print("NDX:", latest_ndx)


# --------------------------------------------------
# 3. 200일 SMA 계산
# --------------------------------------------------

last_200_closes = [
    row["close"]
    for row in ndx_data[-200:]
]

ndx_sma200 = sum(last_200_closes) / 200

print("NDX 200-day SMA:", ndx_sma200)


# --------------------------------------------------
# 4. 기존 데이터 읽기
# --------------------------------------------------

data = load_existing_data()


# --------------------------------------------------
# 5. 기존 전고점 찾기
# --------------------------------------------------

ndx_peak = INITIAL_NDX_PEAK

for row in data.values():

    value = row.get("NDX_PEAK", "")

    if value:
        try:
            ndx_peak = max(
                ndx_peak,
                float(value)
            )
        except ValueError:
            pass


# --------------------------------------------------
# 6. 새로운 NDX가 전고점을 돌파하면 갱신
# --------------------------------------------------

if latest_ndx["close"] > ndx_peak:
    ndx_peak = latest_ndx["close"]


# --------------------------------------------------
# 7. NDX 낙폭 계산
# --------------------------------------------------

ndx_dd = (
    latest_ndx["close"] / ndx_peak - 1
) * 100

# --------------------------------------------------
# QLD 기본 목표 비중
# --------------------------------------------------

if latest_ndx["close"] >= ndx_sma200:
    qld_target = 100
else:
    qld_target = 50


# --------------------------------------------------
# VIX 조정
# --------------------------------------------------

if vix["value"] >= 35:
    qld_target -= 50
elif vix["value"] >= 25:
    qld_target -= 25


# --------------------------------------------------
# DGS10 3개월 변화
# --------------------------------------------------

# 현재까지의 데이터를 날짜순으로 정렬
sorted_dates = sorted(data.keys())

current_date = latest_ndx["date"]

# 현재 날짜에서 약 3개월 전 날짜 찾기
current_dt = datetime.strptime(current_date, "%Y-%m-%d")

target_dt = current_dt - timedelta(days=90)

# 가장 가까운 과거 데이터 찾기
past_date = None

for date in sorted_dates:
    date_dt = datetime.strptime(date, "%Y-%m-%d")

    if date_dt <= target_dt:
        past_date = date
    else:
        break

if past_date is None:
    raise RuntimeError("Not enough DGS10 history for 3-month change")

current_dgs10 = float(dgs10["value"])
past_dgs10 = float(data[past_date]["DGS10"])

dgs10_3m_change = current_dgs10 - past_dgs10

print("DGS10 3M change:", dgs10_3m_change)

# --------------------------------------------------
# 8. 오늘 데이터 저장
# --------------------------------------------------

date = latest_ndx["date"]

data[date] = {

    "date": date,

    "VIXCLS": vix["value"],

    "DGS10": dgs10["value"],

    "NDX": latest_ndx["close"],

    "NDX_SMA200": ndx_sma200,

    "NDX_PEAK": ndx_peak,

    "NDX_DD": ndx_dd,

    "QLD_TARGET": qld_target,
}

# --------------------------------------------------
# 9. 저장
# --------------------------------------------------

save_data(data)

print(f"Saved: {date}")
print(f"NDX: {latest_ndx['close']}")
print(f"NDX_SMA200: {ndx_sma200}")
print(f"NDX_PEAK: {ndx_peak}")
print(f"NDX_DD: {ndx_dd:.2f}%")
