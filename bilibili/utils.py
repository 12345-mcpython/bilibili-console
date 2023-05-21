import hashlib
import os
import re
import sys
import time

import requests

cached_response: dict[str, str] = {}


class RequestManager:

    def __init__(self, cookie=""):
        self.cached_response: dict[str, requests.Response] = {}
        self.session = requests.session()
        self.session.headers.update(
            {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) "
                           "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
             "referer": "https://www.bilibili.com"})
        self.session.headers.update({"cookie": cookie})

    def get(self, url: str, params=None, cache=False, **kwargs) -> requests.Response:
        if self.cached_response.get(url):
            return self.cached_response.get(url)
        else:
            count = 5
            while True:
                try:
                    request = self.session.get(url, params=params, timeout=5, **kwargs)
                    break
                except requests.exceptions.RequestException as request_error:
                    print("\n")
                    print(f"{url}请求错误! 将会重试{count}次! ")
                    count -= 1
                    if count <= 0:
                        raise request_error
            if cache:
                self.cached_response[url] = request
            return request

    def post(self, url: str, params=None, **kwargs) -> requests.Response:
        count = 5
        while True:
            try:
                request = self.session.post(url, params=params, timeout=5, **kwargs)
                break
            except requests.exceptions.RequestException as request_error:
                print("\n")
                print(f"{url}请求错误! 将会重试{count}次! ")
                count -= 1
                if count <= 0:
                    raise request_error
        return request

    def refresh_login_state(self):
        if os.path.exists("cookie.txt"):
            with open("cookie.txt") as file:
                cookie = file.read()
        self.session.headers['cookie'] = cookie
        print()
        print("刷新登录状态成功.")
        print()
        return self.is_login()

    def is_login(self) -> bool:
        request = self.get('https://api.bilibili.com/x/member/web/account')
        if request.json()['code'] == -101:
            print("账号尚未登录.")
            print()
            print("可能 cookie 已失效, 重新替换 cookie.txt 并执行 refresh_login_state.")
            print()
            return False
        elif request.json()['code'] == 0:
            print("账号已登录.")
            print(f"欢迎{request.json()['data']['uname']}登录.")
            print()
            return request.json()['data']['mid']
        else:
            raise Exception("Invalid login code: " + str(request.json()['code']))

    def get_local_user_mid(self) -> int:
        request = self.get('https://api.bilibili.com/x/member/web/account')
        return request.json()['data']['mid']


def convert_cookies_to_dict(cookies) -> dict[str, str]:
    return dict([li.split("=", 1) for li in cookies.split(";")])


def clean_cookie(dict_cookie: dict[str, str]) -> dict[str, str]:
    cleaned = {}
    for i, j in dict_cookie.items():
        cleaned[i.strip()] = j.strip()
    return cleaned


def format_time(timestamp: int) -> str:
    if timestamp > 60 * 60:
        fmt = "{}:{}:{}"
        hour = timestamp // (60 * 60)
        minute = (timestamp - (hour * 60 * 60)) // 60
        sec = timestamp - (hour * 60 * 60) - minute * 60
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
        minute = timestamp // 60
        if minute < 10:
            fmt = "0{}:{}"
        sec = timestamp - minute * 60
        if sec < 10:
            fmt = "{}:0{}"
        if sec < 10 and minute < 10:
            fmt = "0{}:0{}"
        return fmt.format(minute, sec)


def validate_title(title) -> str:
    rstr = r"[\/\\\:\*\?\"\<\>\|]"
    new_title = re.sub(rstr, "_", title)
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
            cookie = f.read().strip()
            if not cookie:
                print("cookie.txt 内没有内容!")
                sys.exit(1)
            return cookie
    else:
        print("cookie.txt 不存在! 请创建 cookie.txt 并写入 cookie!")
        sys.exit(1)


def encrypt_wbi(request_argument: str):
    r = request_manager.get("https://api.bilibili.com/x/web-interface/nav", cache=True)
    wbi_img_url = r.json()['data']['wbi_img']['img_url']
    wbi_sub_url = r.json()['data']['wbi_img']['sub_url']
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


# https://www.cnblogs.com/0506winds/p/13953600.html
# python字节自适应转化单位KB、MB、GB
def hum_convert(value):
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = 1024.0
    for i in range(len(units)):
        if (value / size) < 1:
            return "%.2f%s" % (value, units[i])
        value = value / size


request_manager = RequestManager(read_cookie())
