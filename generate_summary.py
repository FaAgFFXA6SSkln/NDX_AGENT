import csv
import json
from datetime import datetime, timezone

CSV_FILE = "macro.csv"
JSON_FILE = "summary.json"


def read_latest_row():
    with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise RuntimeError("macro.csv is empty")

    return rows[-1]


def to_float(value):
    if value is None or value == "":
        return None

    try:
        return float(value)
    except ValueError:
        return None


def format_number(value, decimals=2):
    if value is None:
        return "-"
    return round(value, decimals)


row = read_latest_row()

ndx = to_float(row.get("NDX"))
ndx_sma200 = to_float(row.get("NDX_SMA200"))
ndx_peak = to_float(row.get("NDX_PEAK"))
ndx_dd = to_float(row.get("NDX_DD"))
vix = to_float(row.get("VIXCLS"))
dgs10 = to_float(row.get("DGS10"))
dgs10_3m_change = to_float(row.get("DGS10_3M_CHANGE"))
qld_target = to_float(row.get("QLD_TARGET"))

if ndx is not None and ndx_sma200 not in (None, 0):
    sma_distance = (ndx / ndx_sma200 - 1) * 100
else:
    sma_distance = None


summary = {
    "updated_at_utc": datetime.now(timezone.utc).isoformat(),

    "date": row.get("date"),

    "ndx": ndx,
    "ndx_sma200": ndx_sma200,
    "ndx_peak": ndx_peak,
    "ndx_drawdown": ndx_dd,
    "ndx_distance_from_sma200": sma_distance,

    "vix": vix,

    "dgs10": dgs10,
    "dgs10_3m_change": dgs10_3m_change,

    "qld_target": qld_target,

    "rules": {
        "ndx_vs_sma200": (
            "100%"
            if ndx is not None
            and ndx_sma200 is not None
            and ndx >= ndx_sma200
            else "50%"
        ),

        "vix_adjustment": (
            -50
            if vix is not None and vix >= 35
            else -25
            if vix is not None and vix >= 25
            else 0
        ),

        "dgs10_adjustment": (
            -25
            if dgs10_3m_change is not None and dgs10_3m_change >= 0.50
            else 10
            if dgs10_3m_change is not None and dgs10_3m_change <= -0.50
            else 0
        ),

        "drawdown": (
            "DD <= -25%"
            if ndx_dd is not None and ndx_dd <= -25
            else "DD <= -15%"
            if ndx_dd is not None and ndx_dd <= -15
            else "Normal"
        )
    }
}


with open(JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(json.dumps(summary, ensure_ascii=False, indent=2))
