import akshare as ak
import requests
import json
import os

from datetime import datetime, timezone, timedelta

from config import RULES


RECORD_FILE = "record.json"


# =========================
# 中国北京时间
# =========================

def china_time():

    return (
        datetime.now(timezone.utc)
        +
        timedelta(hours=8)
    )



# =========================
# 读取提醒记录
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

        except Exception:

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
# Server酱微信推送
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


        response = requests.post(

            url,

            data=data,

            timeout=10

        )


        if response.status_code == 200:

            print(
                "微信发送成功"
            )

        else:

            print(
                "微信发送失败:",
                response.text
            )


    except Exception as e:


        print(
            "微信发送异常:",
            e
        )



# =========================
# ETF实时行情
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

            "ETF行情获取失败:",

            e

        )



    return None, None
# =========================
# 指数实时行情（新浪）
# =========================

def get_index_data(code):

    try:

        print(
            "获取指数实时行情..."
        )


        if code == "000510.CSI":

            symbol = "sh000510"


        elif code == "000300.CSI":

            symbol = "sh000300"


        else:

            return None, None



        import time

        url = (
              "https://hq.sinajs.cn/list="
              +
    		symbol
    		+
    		"&_="
    		+
    		str(int(time.time()))
	)

        headers = {

    		"Referer":
    		"https://finance.sina.com.cn",

   	 	"User-Agent":
    		"Mozilla/5.0 (Windows NT 10.0; Win64; x64)",

    		"Accept":
    		"*/*"

	}



        response = requests.get(

            url,

            headers=headers,

            timeout=10

        )


        text = response.text

	print("新浪返回:", text)



        if '"' not in text:

            print(
                "新浪返回为空"
            )

            return None, None



        data = text.split('"')[1].split(",")


        if len(data) < 4:
            print("新浪数据格式异常")
            return None, None


        price = float(data[3])


        yesterday = float(data[2])



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


        print(
            "指数行情失败:",
            e
        )


        return None, None


# =========================
# 统一行情入口
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
# 生成日报
# =========================

def create_report():


    now = china_time()


    report = f"""
📊 ETF投资助手 {now.strftime("%H:%M")}

时间：
{now.strftime("%Y-%m-%d %H:%M")}

====================
"""



    for name, info in RULES.items():


        price, change = get_price(info)



        if price is None:


            report += f"""

{name}

行情获取失败

--------------------
"""

            continue



        if change >= 0:

            change_text = (

                "+"

                +

                str(round(change,2))

                +

                "%"

            )

        else:

            change_text = (

                str(round(change,2))

                +

                "%"

            )



        report += f"""

{name}

当前价格：
{price}

今日涨跌：
{change_text}

"""



        # =====================
        # 观察类
        # =====================

        if info["类型"] == "观察":


            report += """

状态：
观察

--------------------
"""

            continue



        # =====================
        # 买点状态
        # =====================

        status = "等待买点"



        for rule in info["加仓规则"]:


            target = rule["价格"]



            if price <= target:


                status = (

                    "🚨 已达到买点 "

                    +

                    str(target)

                )

                break



            elif price <= target * 1.02:


                status = (

                    "⚠️ 接近买点 "

                    +

                    str(target)

                )



        report += """

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
# 买点提醒
# =========================

def check_buy_signal(name, info):


    # 观察类不提醒

    if info["类型"] == "观察":

        return



    price, change = get_price(info)



    if price is None:


        print(
            name,
            "行情失败，跳过提醒"
        )

        return



    # 每天提醒一次

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



        # 今天已经提醒

        if record.get(key) == today:

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


            record[key] = today

            save_record(record)



        # 接近买点

        elif price <= target * 1.02:


            send_wechat(

                "⚠️ ETF接近买点提醒",

                f"""

{name}


当前价格：

{price}



目标买点：

{target}



请关注

"""

            )


            record[key] = today

            save_record(record)





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



    # =====================
    # 检查买点
    # =====================

    print(
        "检查买点..."
    )



    for name, info in RULES.items():


        check_buy_signal(

            name,

            info

        )



    # =====================
    # 生成日报
    # =====================

    print(
        "生成日报..."
    )



    report = create_report()



    print(
        report
    )



    # =====================
    # 发送日报
    # =====================


    send_wechat(

        "ETF投资助手 "
        +
        now.strftime("%H:%M"),

        report

    )


    print(
        "ETF投资助手运行完成"
    )