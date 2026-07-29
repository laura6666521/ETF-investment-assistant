import akshare as ak
import json
import os
import requests
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
# Server酱微信提醒
# =========================

def send_wechat(title, content):

    key = os.getenv(
        "SERVERCHAN_KEY"
    )


    if not key:

        print(
            "没有配置SERVERCHAN_KEY"
        )

        return


    url = (
        "https://sctapi.ftqq.com/"
        + key
        + ".send"
    )


    data = {

        "title": title,

        "desp": content

    }


    try:

        requests.post(
            url,
            data=data,
            timeout=10
        )


        print(
            "微信通知已发送"
        )


    except Exception as e:

        print(
            "微信发送失败:",
            e
        )



# =========================
# 获取ETF实时行情
# =========================

def get_etf_price(code):

    try:

        df = ak.fund_etf_spot_em()


        row = df[
            df["代码"] == code
        ]


        if len(row) > 0:

            price = float(
                row.iloc[0]["最新价"]
            )

            change = float(
                row.iloc[0]["涨跌幅"]
            )


            return price, change


    except Exception as e:

        print(
            "ETF行情获取失败:",
            e
        )


    return None, None



# =========================
# 获取指数实时行情
# =========================

def get_index_price(code):

    try:

        df = ak.stock_zh_index_spot_em()


        row = df[
            df["代码"] == code
        ]


        if len(row) > 0:

            price = float(
                row.iloc[0]["最新价"]
            )


            change = float(
                row.iloc[0]["涨跌幅"]
            )


            return price, change


    except Exception as e:

        print(
            "指数行情获取失败:",
            e
        )


    return None, None



# =========================
# 观察类ETF
# =========================

def watch_etf(name, info):

    price, change = get_etf_price(
        info["代码"]
    )


    print("--------------------")
    print(name)


    if price is None:

        print(
            "获取失败"
        )

        return


    print(
        "当前价格:",
        price
    )


    print(
        "今日涨跌:",
        change,
        "%"
    )


    print(
        "状态: 仅观察"
    )



# =========================
# 检查加仓规则
# =========================

def check_rule(name, info):


    if info["类型"] == "指数":

        price, change = get_index_price(
            info["代码"]
        )


    else:

        price, change = get_etf_price(
            info["代码"]
        )



    print("--------------------")
    print(name)


    if price is None:

        print(
            "获取失败"
        )

        return



    print(
        "当前价格:",
        price
    )


    print(
        "今日涨跌:",
        change,
        "%"
    )



    for rule in info["加仓规则"]:


        target = rule["价格"]

        money = rule["金额"]


        key = (
            name
            +
            "_"
            +
            str(target)
        )


        month = datetime.now().strftime(
            "%Y-%m"
        )



        if record.get(key) == month:

            print(
                "目标:",
                target,
                "本月已提醒"
            )

            continue



        # 达到买点

        if price <= target:


            print(
                "🚨 达到加仓条件"
            )


            print(
                "建议加仓:",
                money,
                "元"
            )



            send_wechat(

                "🚨 ETF加仓提醒",

                f"""
## ETF加仓信号

标的：
{name}

当前价格：
{price}

今日涨跌：
{change}%

触发条件：
≤ {target}

建议操作：
加仓 {money} 元

时间：
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

策略：
下跌分批加仓
"""
            )



            record[key] = month

            save_record(record)



        # 接近买点2%

        elif price <= target * 1.02:


            distance = round(
                (price - target)
                /
                target
                *
                100,
                2
            )


            print(
                "⚠️ 接近买点",
                distance,
                "%"
            )


            print(
                "目标:",
                target
            )



        else:


            print(
                "目标:",
                target,
                "等待"
            )



# =========================
# 主程序
# =========================


now = datetime.now()


print(
    "ETF投资助手",
    now
)


current_time = now.strftime(
    "%H:%M"
)



# 交易时间判断

market_time = (

    "09:30" <= current_time <= "11:30"

    or

    "13:00" <= current_time <= "15:00"

)



if not market_time:


    print(
        "⏸ 当前非交易时间"
    )


else:


    print(
        "📈 市场交易中，开始监控"
    )



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