import os
import re

import requests
from requests.utils import dict_from_cookiejar


def format_time(time):
    if time > 60 * 60:
        fmt = "{}:{}:{}"
        hour = time // (60 * 60)
        minute = (time - (hour * 60 * 60)) // 60
        sec = time - (hour * 60 * 60) - minute * 60
        if minute < 10:
            fmt = "{}:0{}:{}"
        if sec < 10:
            fmt = "{}:{}:0{}"
        if sec < 10 and minute < 10:
            fmt = "{}:0{}:0{}"
        if hour > 10:
            fmt = "1" + fmt
        return fmt.format(hour, minute, sec)
    else:
        fmt = "{}:{}"
        minute = time // 60
        if minute < 10:
            fmt = "0{}:{}"
        sec = time - minute * 60
        if sec < 10:
            fmt = "{}:0{}"
        if sec < 10 and minute < 10:
            fmt = "0{}:0{}"
        return fmt.format(minute, sec)


def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title)  # 替换为下划线
    return new_title


# av bv互转算法
# https://www.zhihu.com/question/381784377/answer/1099438784

def dec(x):
    table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
    tr = {}
    for i in range(58):
        tr[table[i]] = i
    s = [11, 10, 3, 8, 4, 6]
    xor = 177451812
    add = 8728348608
    r = 0
    for i in range(6):
        r += tr[x[s[i]]] * 58 ** i
    return (r - add) ^ xor


def enc(x):
    table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
    tr = {}
    for i in range(58):
        tr[table[i]] = i
    s = [11, 10, 3, 8, 4, 6]
    xor = 177451812
    add = 8728348608
    x = (x ^ xor) + add
    r = list('BV1  4 1 7  ')
    for i in range(6):
        r[s[i]] = table[x // 58 ** i % 58]
    return ''.join(r)


def read_cookie():
    if os.path.exists("cookie.txt"):
        with open("cookie.txt") as f:
            return f.read()
    else:
        b = requests.get("https://www.bilibili.com", headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
            "referer": "https://www.bilibili.com"})
        cookie = ''
        for i, j in dict_from_cookiejar(b.cookies).items():
            cookie += "{}={};".format(i, j)
        return cookie[:-1]
