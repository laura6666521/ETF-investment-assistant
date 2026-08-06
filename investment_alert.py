import akshare as ak
import requests
import json
import os

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
# 记录
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
# 指数行情
# =========================

def get_index_data(code):

    try:

        print(
            "获取指数行情..."
        )


        if code == "000510.CSI":

            symbol = "sh000510"


        elif code == "000300.CSI":

            symbol = "sh000300"


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


        data = response.text.split("~")



        if len(data) < 6:

            return None, None



        price = float(
            data[3]
        )


        yesterday = float(
            data[4]
        )


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
# 沪深300 PE
# =========================

def get_hs300_pe():

    try:

        print(
            "获取沪深300 PE..."
        )


        data = ak.stock_index_pe_lg(
            symbol="沪深300"
        )


        pe = float(
            data.iloc[-1]["滚动市盈率"]
        )


        return pe



    except Exception as e:

        print(
            "沪深300PE获取失败:",
            e
        )


        return None


# =========================
# 伦敦金价格
# =========================

def get_gold_price():

    try:

        print(
            "获取伦敦金价格..."
        )


        # 腾讯国际黄金现货
        url = (
            "https://qt.gtimg.cn/q=hf_GC"
        )


        response = requests.get(
            url,
            timeout=10
        )


        text = response.text


        print(
            "黄金返回:",
            text
        )


        data_str = text.split('"')[1]

        data = data_str.split(",")


        # 美元/盎司
        usd_price = float(
            data[0]
        )


        change = float(
            data[1]
        )


        return usd_price, change



    except Exception as e:

        print(
            "黄金行情失败:",
            e
        )

        return None, None


# =========================
# 美元人民币汇率
# =========================

def get_usdcny():

    try:

        print(
            "获取美元人民币汇率..."
        )


        url = (
            "https://hq.sinajs.cn/list=fx_susdcny"
        )


        headers = {
            "Referer": "https://finance.sina.com.cn"
        }


        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )


        text = response.text


        print(
            "汇率返回:",
            text
        )


        data_str = text.split('"')[1]


        data = data_str.split(",")


        # 美元人民币现价
        rate = float(
            data[1]
        )


        return rate



    except Exception as e:


        print(
            "汇率获取失败:",
            e
        )


        return None



# =========================
# 沪深300估值提醒
# =========================

def check_hs300_pe():


    pe = get_hs300_pe()


    if pe is None:

        return



    today = china_time().strftime(
        "%Y-%m-%d"
    )



    key = "沪深300_PE提醒"



    if pe > 15:


        if record.get(key) == today:

            return



        send_wechat(

            "⚠️ 沪深300估值提醒",

            f"""
沪深300滚动PE:

{pe}

超过15

请关注估值风险。
"""
        )


        record[key] = today

        save_record(record)






# =========================
# 获取统一行情
# =========================

def get_price(info):


    if info["类型"] == "指数":

        return get_index_data(
            info["代码"]
        )


    elif info["类型"] == "ETF":

        return get_etf_data(
            info["代码"]
        )


    elif info["类型"] == "观察":

        return get_etf_data(
            info["代码"]
        )


    else:

        return None, None



# =========================
# 买点检查
# =========================

def check_buy_signal(name, info):


    if info["类型"] != "ETF" and info["类型"] != "指数":

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



        # 正式买点

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



        # 2%提前提醒

        elif price <= target * 1.02:


            send_wechat(

                "⚠️ ETF接近买点",

                f"""
{name}

当前价格:
{price}

目标价格:
{target}

距离买点:
{round((price-target)/target*100,2)}%
"""
            )


            record[key] = today

            save_record(record)






# =========================
# 日报
# =========================

def create_report():


    now = china_time()


    today = now.strftime(
        "%Y-%m-%d"
    )


    report = f"""
📊 ETF投资助手

时间:
{now.strftime("%Y-%m-%d %H:%M")}

================
"""



    for name, info in RULES.items():



        # =========================
        # 获取行情
        # =========================


        # 黄金单独处理

        if info["类型"] == "黄金":


            usd_price, change = get_gold_price()


            rate = get_usdcny()


            if usd_price is not None and rate is not None:


                # 美元/盎司 转 人民币/克

                price = round(
                    usd_price * rate / 31.1035,
                    2
                )


            else:

                price = None



        else:


            price, change = get_price(info)




        # =========================
        # 行情失败
        # =========================

        if price is None:


            report += f"""

{name}

行情获取失败

----------------
"""

            continue




        # =========================
        # 输出价格
        # =========================

        report += f"""

{name}

价格:
{price}

"""



        if change is not None:


            report += f"""

涨跌:
{change}%

"""




        # =========================
        # 观察类
        # =========================

        if info["类型"] == "观察":


            report += """

状态:
观察

----------------
"""


            continue




        # =========================
        # 黄金类
        # =========================

        if info["类型"] == "黄金":


            report += """

状态:
仅查看价格

----------------
"""


            continue



        # =========================
        # ETF / 指数 买点判断
        # =========================

        status = "⏳ 等待买点"



        for rule in info["加仓规则"]:


            target = rule["价格"]


            key = (
                name
                +
                "_"
                +
                str(target)
            )



            # 今天已经提醒过

            if record.get(key) == today:


                if price <= target:


                    status = (
                        "🚨 今日已达到买点 "
                        +
                        str(target)
                    )


                else:


                    status = (
                        "⚠️ 今日已接近买点 "
                        +
                        str(target)
                    )


                break




            # 当前达到买点

            if price <= target:


                status = (
                    "🚨 当前达到买点 "
                    +
                    str(target)
                )


                break




            # 距离买点2%

            elif price <= target * 1.02:


                status = (
                    "⚠️ 接近买点 "
                    +
                    str(target)
                )


                break




        report += f"""

状态:
{status}

----------------
"""



    # =========================
    # 沪深300 PE显示
    # =========================

    pe = get_hs300_pe()



    if pe is not None:


        report += f"""

沪深300估值:

滚动PE:
{pe}

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
        "检查沪深300估值..."
    )



    check_hs300_pe()




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