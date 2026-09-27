
import os
import requests

FRED_API_KEY = os.environ["FRED_API_KEY"]


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
        value = observation["value"]

        # FRED의 "."은 해당 날짜에 데이터가 없다는 의미
        if value != ".":
            return {
                "date": observation["date"],
                "value": float(value),
            }

    raise RuntimeError(f"No valid data found for {series_id}")


vix = get_latest_value("VIXCLS")
dgs10 = get_latest_value("DGS10")

print("VIXCLS")
print(vix)

print("DGS10")
print(dgs10)
