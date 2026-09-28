import csv
import json
from datetime import datetime, timezone

CSV_FILE = "macro.csv"
JSON_FILE = "summary.json"


def read_all_rows():
    with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise RuntimeError("macro.csv is empty")

    rows.sort(key=lambda x: x["date"])

    return rows


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


rows = read_all_rows()
latest = rows[-1]

# 최근 3거래일의 QLD Target
recent_rows = rows[-3:]

recent_targets = []

for row in recent_rows:
    target = to_float(row.get("QLD_TARGET"))

    if target is not None:
        recent_targets.append({
            "date": row["date"],
            "target": target
        })


# --------------------------------------------------
# 3거래일 확인
# --------------------------------------------------

confirmation_count = 0
confirmed_target = None
confirmation_status = "WAITING"

if len(recent_targets) >= 3:

    targets = [
        item["target"]
        for item in recent_targets
    ]

    # 최근 3거래일의 Target이 모두 같아야 확인 완료
    if targets[0] == targets[1] == targets[2]:

        confirmation_count = 3
        confirmed_target = targets[2]
        confirmation_status = "CONFIRMED"

    else:

        # 현재 Target과 같은 값이 며칠 연속 유지됐는지 계산
        latest_target = targets[-1]

        for target in reversed(targets):

            if target == latest_target:
                confirmation_count += 1
            else:
                break

        confirmation_status = "WAITING"

else:

    latest_target = (
        recent_targets[-1]["target"]
        if recent_targets
        else None
    )

    if latest_target is not None:
        confirmation_count = 1


# --------------------------------------------------
# 기본 지표
# --------------------------------------------------

ndx = to_float(latest.get("NDX"))
ndx_sma200 = to_float(latest.get("NDX_SMA200"))
ndx_peak = to_float(latest.get("NDX_PEAK"))
ndx_dd = to_float(latest.get("NDX_DD"))
vix = to_float(latest.get("VIXCLS"))
dgs10 = to_float(latest.get("DGS10"))
dgs10_3m_change = to_float(
    latest.get("DGS10_3M_CHANGE")
)
qld_target = to_float(latest.get("QLD_TARGET"))


if ndx is not None and ndx_sma200 not in (None, 0):

    sma_distance = (
        ndx / ndx_sma200 - 1
    ) * 100

else:

    sma_distance = None


# --------------------------------------------------
# 전략 규칙 표시
# --------------------------------------------------

if (
    ndx is not None
    and ndx_sma200 is not None
    and ndx >= ndx_sma200
):

    sma_rule = "100%"

else:

    sma_rule = "50%"


if vix is not None and vix >= 35:

    vix_adjustment = -50

elif vix is not None and vix >= 25:

    vix_adjustment = -25

else:

    vix_adjustment = 0


if (
    dgs10_3m_change is not None
    and dgs10_3m_change >= 0.50
):

    dgs10_adjustment = -25

elif (
    dgs10_3m_change is not None
    and dgs10_3m_change <= -0.50
):

    dgs10_adjustment = 10

else:

    dgs10_adjustment = 0


if ndx_dd is not None and ndx_dd <= -25:

    drawdown_rule = "DD <= -25%"

elif ndx_dd is not None and ndx_dd <= -15:

    drawdown_rule = "DD <= -15%"

else:

    drawdown_rule = "Normal"


# --------------------------------------------------
# summary.json
# --------------------------------------------------

summary = {

    "updated_at_utc":
        datetime.now(timezone.utc).isoformat(),

    "date":
        latest.get("date"),

    "ndx":
        ndx,

    "ndx_sma200":
        ndx_sma200,

    "ndx_peak":
        ndx_peak,

    "ndx_drawdown":
        ndx_dd,

    "ndx_distance_from_sma200":
        sma_distance,

    "vix":
        vix,

    "dgs10":
        dgs10,

    "dgs10_3m_change":
        dgs10_3m_change,

    # 현재 계산된 Target
    "qld_target":
        qld_target,

    # 3거래일 확인 결과
    "confirmation": {

        "status":
            confirmation_status,

        "count":
            confirmation_count,

        "required":
            3,

        "confirmed_target":
            confirmed_target,

        "recent_targets":
            recent_targets
    },

    "rules": {

        "ndx_vs_sma200":
            sma_rule,

        "vix_adjustment":
            vix_adjustment,

        "dgs10_adjustment":
            dgs10_adjustment,

        "drawdown":
            drawdown_rule
    }
}


with open(
    JSON_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary,
        f,
        ensure_ascii=False,
        indent=2
    )


print(
    json.dumps(
        summary,
        ensure_ascii=False,
        indent=2
    )
)
