import akshare as ak
import requests
import json
import os
import time

from datetime import datetime, timezone, timedelta

from config import RULES


RECORD_FILE = "record.json"


# =========================
# 北京时间
# =========================

def china_time():
    return (
        datetime.now(timezone.utc)
        +
        timedelta(hours=8)
    )


# =========================
# 记录文件
# =========================

def load_record():

    if os.path.exists(RECORD_FILE):

        try:

            with open(
                RECORD_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except:

            return {}

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
# 微信推送
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
        +
        key
        +
        ".send"
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
                "微信发送成功"
            )

        else:

            print(
                "微信发送失败",
                r.text
            )


    except Exception as e:

        print(
            "微信异常:",
            e
        )



# =========================
# ETF行情
# =========================

ETF_CACHE = None



def get_etf_data(code):

    global ETF_CACHE


    try:

        if ETF_CACHE is None:

            print(
                "获取ETF实时行情..."
            )

            ETF_CACHE = ak.fund_etf_spot_em()



        row = ETF_CACHE[
            ETF_CACHE["代码"] == code
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
            "ETF行情失败:",
            e
        )


    return None, None




# =========================
# 腾讯指数行情
# =========================

def get_index_data(code):

    try:

        print("获取指数行情...")


        if code == "000510.CSI":

            symbol = "sh000510"


        elif code == "000300.CSI":

            symbol = "s_sh000300"


        else:

            return None, None


        url = (
            "https://qt.gtimg.cn/q="
            +
            symbol
        )


        response = requests.get(
            url,
            timeout=10
        )


        text = response.text


        print("腾讯返回:", text)


        data = text.split("~")


        if len(data) < 6:

            return None, None


        price = float(data[3])

        yesterday = float(data[4])


        change = round(
            (price-yesterday)
            /
            yesterday
            *
            100,
            2
        )


        return price, change


    except Exception as e:

        print("指数行情失败:", e)

        return None, None



# =========================
# 统一行情
# =========================

def get_price(info):


    if info["类型"] == "指数":

        return get_index_data(
            info["代码"]
        )


    else:

        return get_etf_data(
            info["代码"]
        )




# =========================
# 买点检查
# =========================

def check_buy_signal(name, info):


    if info["类型"] == "观察":

        return



    price, change = get_price(info)


    if price is None:

        print(
            name,
            "行情失败，跳过提醒"
        )

        return



    today = china_time().strftime(
        "%Y-%m-%d"
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



        if record.get(key) == today:

            continue



        if price <= target:


            send_wechat(

                "🚨 ETF加仓提醒",

                f"""
{name}

当前价格:
{price}

触发价格:
{target}

建议金额:
{money}元
"""
            )


            record[key] = today

            save_record(record)



        elif price <= target * 1.02:


            send_wechat(

                "⚠️ ETF接近买点",

                f"""
{name}

当前价格:
{price}

目标价格:
{target}
"""
            )


            record[key] = today

            save_record(record)




# =========================
# 日报
# =========================

def create_report():

    now = china_time()


    report = f"""
📊 ETF投资助手

时间:
{now.strftime("%Y-%m-%d %H:%M")}

================
"""



    for name, info in RULES.items():


        price, change = get_price(info)



        if price is None:

            report += f"""

{name}

行情获取失败

----------------
"""

            continue



        report += f"""

{name}

价格:
{price}

涨跌:
{change}%

"""



        if info["类型"] == "观察":

            report += """

状态:
观察

----------------
"""

            continue



        status = "等待买点"



        for rule in info["加仓规则"]:

            if price <= rule["价格"]:

                status = (
                    "🚨 达到买点 "
                    +
                    str(rule["价格"])
                )

                break



        report += f"""

状态:
{status}

----------------
"""



    return report




# =========================
# 主程序
# =========================

if __name__ == "__main__":


    now = china_time()


    print(
        "ETF投资助手启动"
    )


    print(
        "北京时间:",
        now.strftime("%Y-%m-%d %H:%M")
    )



    print(
        "检查买点..."
    )


    for name, info in RULES.items():

        check_buy_signal(
            name,
            info
        )



    print(
        "生成日报..."
    )


    report = create_report()



    print(report)



    send_wechat(

        "ETF投资助手 "
        +
        now.strftime("%H:%M"),

        report

    )



    print(
        "ETF投资助手运行完成"
    )