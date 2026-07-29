import akshare as ak
import json
import os
import requests
from datetime import datetime


# =========================
# 配置
# =========================

RECORD_FILE = "record.json"


# =========================
# 监控标的
# =========================

RULES = {

    "中证A500": {

        "类型": "指数",

        "代码": "000510",

        "加仓规则": [
            {
                "价格": 5500,
                "金额": 500
            },
            {
                "价格": 5211,
                "金额": 1000
            }
        ]

    },


    "沪深300": {

        "类型": "指数",

        "代码": "000300",

        "加仓规则": [
            {
                "价格": 4466,
                "金额": 500
            },
            {
                "价格": 4231,
                "金额": 1000
            }
        ]

    },


    "电力ETF广发": {

        "类型": "ETF",

        "代码": "159611",

        "加仓规则": [
            {
                "价格": 1.0041,
                "金额": 500
            }
        ]

    },


    "煤炭ETF国泰": {

        "类型": "观察",

        "代码": "515220"

    },


    "红利低波50ETF南方": {

        "类型": "观察",

        "代码": "515450"

    }

}



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
# 微信提醒
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
# 获取ETF价格
# =========================

def get_etf_price(code):

    try:

        df = ak.fund_etf_spot_em()


        row = df[
            df["代码"] == code
        ]


        if len(row) > 0:

            return float(
                row.iloc[0]["最新价"]
            )


    except Exception as e:

        print(
            "ETF获取失败:",
            e
        )


    return None



# =========================
# 获取指数价格
# =========================

def get_index_price(code):

    try:

        df = ak.stock_zh_index_daily(
            symbol="sh" + code
        )


        if len(df) > 0:

            return float(
                df.iloc[-1]["close"]
            )


    except Exception as e:

        print(
            "指数获取失败:",
            e
        )


    return None



# =========================
# 观察ETF
# =========================

def watch_etf(name, info):

    price = get_etf_price(
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
        "状态: 仅观察"
    )



# =========================
# 检查加仓规则
# =========================

def check_rule(name, info):

    if info["类型"] == "指数":

        price = get_index_price(
            info["代码"]
        )

    else:

        price = get_etf_price(
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



    for rule in info["加仓规则"]:


        target = rule["价格"]

        money = rule["金额"]


        key = (
            name
            + "_"
            + str(target)
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
{name}

当前价格:
{price}

触发目标:
{target}

建议加仓:
{money}元
"""

            )


            record[key] = month

            save_record(record)



        elif price <= target * 1.02:


            distance = round(
                (price-target)
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


current = now.strftime(
    "%H:%M"
)


# 非交易时间

if not (
    "09:30" <= current <= "11:30"
    or
    "13:00" <= current <= "15:00"
):

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