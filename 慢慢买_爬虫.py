# !coding=utf-8
import requests
import re
import json
import datetime
import time
import pandas as pd
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import string
import webbrowser
import os


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def clean_filename(title, max_length=30):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned = ''.join(c for c in title if c in valid_chars)
    return cleaned[:max_length]


def raw(text):
    escape_dict = {'/': '%252F', '?': '%253F', '=': '%253D', ':': '%253A', '&': '%26'}
    new_string = ''
    for char in text:
        new_string += escape_dict.get(char, char)
    return new_string


def mmm(item):
    item = raw(item)
    url = 'https://apapia.manmanbuy.com/ChromeWidgetServices/WidgetServices.ashx'
    s = requests.session()
    headers = {
        'Host': 'apapia.manmanbuy.com',
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
        'Proxy-Connection': 'close',
        'Cookie': 'ASP.NET_SessionId=uwhkmhd023ce0yx22jag2e0o;',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_3 like Mac OS X) AppleWebKit/603.3.8 (KHTML, like Gecko) Mobile/14G60 mmbWebBrowse',
        'Content-Length': '457',
        'Accept-Encoding': 'gzip',
        'Connection': 'close',
    }
    postdata = 'c_devid=2C5039AF-99D0-4800-BC36-DEB3654D202C&username=&qs=true&c_engver=1.5.0&c_devtoken=&c_devmodel=iPhone%20SE&c_contype=wifi&' \
               't=1537348981671&c_win=w_320_h_568&p_url={}&' \
               'c_ostype=ios&jsoncallback=%3F&c_ctrl=w_search_trend0_f_content&methodName=getBiJiaInfo_wxsmall&c_devtype=phone&' \
               'jgzspic=no&c_operator=%E4%B8%AD%E5%9B%BD%E7%A7%BB%E5%8A%A8&c_appver=3.6.0&bj=false&c_dp=2&c_osver=10.3.3'.format(
        item)
    s.headers.update(headers)

    try:
        req = s.get(url=url, data=postdata, verify=False).text
        js = json.loads(req)
        title = js['single']['title']
        jiagequshi = js['single']['jiagequshi']
        lowerPrice = js['single']['lowerPrice']
        lowerDate = js['single']['lowerDate']
        lowerDate = re.search(r'[1-9]\d{0,9}', lowerDate).group(0)
        lowerDate = time.strftime("%Y-%m-%d", time.localtime(int(lowerDate)))
        itemurl = js['single']['url']

        date_list = []
        price_list = []
        datalist = jiagequshi.replace('[Date.UTC(', '').replace(')', '').replace(']', '').split(',')
        for i in range(0, len(datalist), 5):
            if i != 0:
                day = int(datalist[i + 2])
                if int(datalist[i + 1]) == 12:
                    mon = 1
                    year = int(datalist[i]) + 1
                else:
                    mon = int(datalist[i + 1]) + 1
                    year = int(datalist[i])
                date = datetime.date(year=year, month=mon, day=day) - datetime.timedelta(days=1)
                price = float(datalist[i - 2])
                date_list.append(date)
                price_list.append(price)

            day = int(datalist[i + 2])
            if int(datalist[i + 1]) == 12:
                mon = 1
                year = int(datalist[i]) + 1
            else:
                mon = int(datalist[i + 1]) + 1
                year = int(datalist[i])
            date = datetime.date(year=year, month=mon, day=day)
            price = float(datalist[i + 3])
            date_list.append(date)
            price_list.append(price)

        data = {'date_日期': date_list, 'price_价格': price_list}
        df = pd.DataFrame(data)
        df.loc[:, "title_名称"] = title
        df.loc[:, "lowerPrice_最低价格"] = lowerPrice
        df.loc[:, "lowerDate_最低价格日期"] = lowerDate
        df.loc[:, "itemurl_商品链接"] = itemurl
        safe_title = clean_filename(title)
        os.makedirs("data", exist_ok=True)
        df.to_csv(f'data/{safe_title}.csv', index=False, mode='a', encoding="GB18030")
        print(f"数据抓取成功，已保存为：{safe_title}.csv")
    except Exception as e:
        print("获取失败，请确认网址是否正确或该商品是否有历史价格信息。")
        print("错误详情：", e)


def main():
    webbrowser.open("https://tool.manmanbuy.com/HistoryLowest.aspx", new=2)
    while True:
        item = input("\n请粘贴商品网址（输入 q 退出）：\n> ").strip()
        if item.lower() == 'q':
            break
        if not item.startswith('http'):
            print("输入的不是有效网址，请重新输入。")
            continue
        mmm(item)


if __name__ == '__main__':
    main()