import akshare as ak
import requests
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
# 微信推送 Server酱
# =========================

def send_wechat(title, content):

    key = os.getenv(
        "SERVERCHAN_KEY"
    )


    if not key:

        print(
            "没有配置 SERVERCHAN_KEY"
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

        r = requests.post(
            url,
            data=data,
            timeout=10
        )


        if r.status_code == 200:

            print(
                "微信通知发送成功"
            )

        else:

            print(
                "微信发送失败",
                r.text
            )


    except Exception as e:

        print(
            "微信发送异常:",
            e
        )



# =========================
# 获取指数行情
# =========================

def get_index_data(code):

    try:

        df = ak.index_zh_a_hist(
            symbol=code,
            period="daily",
            start_date="20260701",
            end_date=datetime.now().strftime("%Y%m%d")
        )


        if len(df) > 0:

            today = df.iloc[-1]


            price = float(
                today["收盘"]
            )


            if len(df) >= 2:

                yesterday = float(
                    df.iloc[-2]["收盘"]
                )

                change = round(
                    (price - yesterday)
                    /
                    yesterday
                    *
                    100,
                    2
                )

            else:

                change = 0


            return price, change


    except Exception as e:

        print(
            "指数获取失败:",
            e
        )


    return None, None



# =========================
# 获取ETF行情
# =========================

def get_etf_data(code):

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
            "ETF获取失败:",
            e
        )


    return None, None



# =========================
# 获取价格
# =========================

def get_price_data(info):

    if info["类型"] == "指数":

        return get_index_data(
            info["代码"]
        )

    else:

        return get_etf_data(
            info["代码"]
        )
# =========================
# 生成ETF报告
# =========================

def create_report():

    now = datetime.now()

    report = f"""
📊 ETF投资助手

时间：
{now.strftime("%Y-%m-%d %H:%M")}

====================
"""


    for name, info in RULES.items():


        price, change = get_price_data(info)


        if price is None:

            report += f"""
{name}

行情获取失败

--------------------
"""

            continue



        if change >= 0:

            change_text = "+" + str(change) + "%"

        else:

            change_text = str(change) + "%"



        report += f"""
{name}

当前价格：
{price}

今日涨跌：
{change_text}
"""



        # 观察类ETF

        if info["类型"] == "观察":

            report += """

状态：
观察

--------------------
"""

            continue



        report += "\n"



        # 判断买点状态

        status = "等待"



        for rule in info["加仓规则"]:

            target = rule["价格"]


            if price <= target:

                status = (
                    "🚨 已达到加仓点 "
                    + str(target)
                )

                break



            elif price <= target * 1.02:

                status = (
                    "⚠️ 接近买点 "
                    + str(target)
                )



        report += f"""
买点：

"""

        for rule in info["加仓规则"]:

            report += (
                str(rule["价格"])
                +
                "（"
                +
                str(rule["金额"])
                +
                "元） "
            )


        report += f"""

状态：
{status}


--------------------
"""


    return report




# =========================
# 检查买点提醒
# =========================

def check_buy_signal(name, info):


    if info["类型"] == "观察":

        return



    price, change = get_price_data(info)


    if price is None:

        return



    today_month = datetime.now().strftime("%Y-%m")



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



        # 防止重复提醒

        if record.get(key) == today_month:

            continue



        # 达到买点

        if price <= target:


            send_wechat(

                "🚨 ETF加仓提醒",

                f"""
{name}

当前价格：
{price}

触发买点：
{target}

建议加仓：
{money}元
"""

            )


            record[key] = today_month

            save_record(record)



# =========================
# 主程序
# =========================


if __name__ == "__main__":


    now = datetime.now()


    print(
        "ETF投资助手",
        now
    )



    # 每次运行发送行情报告

    report = create_report()



    send_wechat(

        "ETF投资助手",

        report

    )



    # 检查买点

    for name, info in RULES.items():


        check_buy_signal(
            name,
            info
        )



    print(
        report
    )