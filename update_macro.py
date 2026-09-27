import os
import csv
import requests

FRED_API_KEY = os.environ["FRED_API_KEY"]
CSV_FILE = "macro.csv"


def get_latest_value(series_id):
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


def load_existing_data():
    if not os.path.exists(CSV_FILE):
        return {}

    data = {}

    with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            data[row["date"]] = {
                "VIXCLS": row["VIXCLS"],
                "DGS10": row["DGS10"],
            }

    return data


def save_data(data):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["date", "VIXCLS", "DGS10"])

        for date in sorted(data):
            writer.writerow([
                date,
                data[date]["VIXCLS"],
                data[date]["DGS10"],
            ])


# 최신 데이터 가져오기
vix = get_latest_value("VIXCLS")
dgs10 = get_latest_value("DGS10")

print("VIXCLS:", vix)
print("DGS10:", dgs10)


# 기존 데이터 읽기
data = load_existing_data()


# 두 지표의 최신 관측일을 사용
date = max(vix["date"], dgs10["date"])

data[date] = {
    "VIXCLS": vix["value"],
    "DGS10": dgs10["value"],
}


# CSV 저장
save_data(data)

print(f"Saved: {date}")
