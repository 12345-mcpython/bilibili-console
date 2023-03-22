import hashlib
import os
import re
import time

import requests

cached_response: dict[str, str] = {}


def convert_cookies_to_dict(cookies) -> dict[str, str]:
    return dict([l.split("=", 1) for l in cookies.split(";")])


def clean_cookie(dict_cookie: dict[str, str]) -> dict[str, str]:
    cleaned = {}
    for i, j in dict_cookie.items():
        cleaned[i.strip()] = j.strip()
    return cleaned


def format_time(time: int) -> str:
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


def validateTitle(title) -> str:
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title)  # 替换为下划线
    return new_title


# av bv互转算法
# https://www.zhihu.com/question/381784377/answer/1099438784

def dec(x: str) -> int:
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


def enc(x: int) -> str:
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
        for i, j in b.cookies.get_dict().items():
            cookie += "{}={};".format(i, j)
        return cookie[:-1]


def encrypt_wbi(request_argument: str):
    wbi_img_url = "https://i0.hdslb.com/bfs/wbi/e056202f38ff49fe8d110c0ec0d36877.png"
    wbi_sub_url = "https://i0.hdslb.com/bfs/wbi/ba5f93b9bf4b4c75b5c9f66257bcb593.png"
    oe = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12,
          38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62,
          11, 36, 20, 34, 44, 52]

    le = []
    key = wbi_img_url.split("/")[-1].split(".")[0] + wbi_sub_url.split("/")[-1].split(".")[0]
    for i in oe:
        le.append(key[i])
    key = "".join(le)[:32]
    hashed = request_argument + "&wts=" + str(round(time.time()))
    return hashed + "&w_rid=" + hashlib.md5(hashed.encode() + key.encode()).hexdigest()