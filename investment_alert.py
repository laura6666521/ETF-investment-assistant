import akshare as ak
import time
import json
import os
from datetime import datetime
from config import RULES


RECORD_FILE = "record.json"


# =========================
# 读取提醒记录
# =========================

def load_record():

    if os.path.exists(RECORD_FILE):

        with open(
            RECORD_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    return {}



def save_record(record):

    with open(
        RECORD_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            record,
            f,
            ensure_ascii=False,
            indent=4
        )



record = load_record()



# =========================
# 获取指数价格
# =========================

def get_index_price(code):

    try:

        df = ak.index_zh_a_hist(
            symbol=code,
            period="daily",
            start_date="20260729",
            end_date="20260729"
        )


        if len(df) > 0:

            return float(
                df.iloc[-1]["收盘"]
            )


    except Exception as e:

        print("指数获取失败:", e)


    return None



# =========================
# 获取ETF实时价格
# =========================

def get_etf_price(code):

    try:

        df = ak.fund_etf_spot_em()

        row = df[df["代码"] == code]


        if len(row) > 0:

            return float(
                row.iloc[0]["最新价"]
            )


    except Exception as e:

        print("ETF获取失败:", e)


    return None



# =========================
def watch_etf(name, info):

    price = get_etf_price(
        info["代码"]
    )


    if price is None:

        print(
            name,
            "获取失败"
        )

        return


    print("--------------------")
    print(name)

    print(
        "当前价格:",
        price
    )

    print(
        "状态: 仅观察"
    )
def check_rule(name, info):

    code = info["代码"]


    if info["类型"] == "指数":

        price = get_index_price(code)

    else:

        price = get_etf_price(code)



    if price is None:

        print(
            name,
            "获取失败"
        )

        return



    print("--------------------")
    print(name)

    print(
        "当前价格:",
        price
    )


    for rule in info["加仓规则"]:

        target = rule["价格"]

        money = rule["金额"]


        key = name + "_" + str(target)


        today_month = datetime.now().strftime("%Y-%m")



        if record.get(key) == today_month:

            print(
                "目标:",
                target,
                "本月已提醒"
            )

            continue



        if price <= target:

            print(
                "🚨 达到加仓条件"
            )

            print(
                "建议加仓:",
                money,
                "元"
            )


            record[key] = today_month

            save_record(record)



        elif price <= target * 1.02:


            distance = round(
                (price-target)/target*100,
                2
            )


            print(
                "⚠️ 接近买点"
            )

            print(
                "目标:",
                target
            )

            print(
                "距离:",
                distance,
                "%"
            )


        else:

            print(
                "目标:",
                target,
                "等待"
            )

# =========================
# 主循环
# =========================

# =========================
# 主循环
# =========================

# =========================
# 单次运行
# =========================

now = datetime.now()

current_time = now.strftime("%H:%M")


print("\n====================")

print(
    "ETF投资助手",
    now
)


morning = (
    "09:30" <= current_time <= "11:30"
)


afternoon = (
    "13:00" <= current_time <= "15:00"
)


if morning or afternoon:


    print("📈 市场交易中，开始监控")


    for name, info in RULES.items():


        if info["类型"] == "观察":

            watch_etf(
                name,
                info
            )


        else:

            check_rule(
                name,
                info
            )


else:

    print(
        "⏸ 当前非交易时间"
    )