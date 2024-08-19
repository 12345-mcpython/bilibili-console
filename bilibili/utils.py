import hashlib
import json
import os
import re
import time
import urllib.parse

import requests
from google.protobuf.json_format import MessageToJson

from bilibili.biliass import Proto2ASS
from bilibili.protobuf.dm_pb2 import DmSegMobileReply

XOR_CODE = 23442827791579
MASK_CODE = 2251799813685247
MAX_AID = 1 << 51

data = [b"F", b"c", b"w", b"A", b"P", b"N", b"K", b"T", b"M", b"u", b"g", b"3", b"G", b"V", b"5", b"L", b"j", b"7",
        b"E", b"J", b"n", b"H", b"p", b"W", b"s", b"x", b"4", b"t", b"b", b"8", b"h", b"a", b"Y", b"e", b"v", b"i",
        b"q", b"B", b"z", b"6", b"r", b"k", b"C", b"y", b"1", b"2", b"m", b"U", b"S", b"D", b"Q", b"X", b"9", b"R",
        b"d", b"o", b"Z", b"f"]

BASE = 58
BV_LEN = 12
PREFIX = "BV1"

cached_response: dict[str, str] = {}


class UserManager:
    def __init__(self, cookie=""):
        self.cached_response: dict[str, requests.Response] = {}
        self.session = requests.session()
        self.session.headers.update(
            {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) "
                              "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
                "referer": "https://www.bilibili.com",
            }
        )
        self.session.headers.update({"cookie": cookie})
        self.mid = 0
        self.csrf = clean_cookie(
            convert_cookies_to_dict(self.session.headers.get("cookie"))
        ).get("bili_jct", "")
        self.is_login = False

    # 这个函数不可能返回 None, 因为 if 已经对 cached_response 进行了验空
    def get(self, url: str, params=None, cache=False, **kwargs) -> requests.Response:
        if self.cached_response.get(url):
            return self.cached_response.get(url)  # type: ignore
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
        self.session.headers["cookie"] = cookie
        print()
        print("刷新登录状态成功.")
        print()
        return self.login()

    def login(self):
        request = self.get("https://api.bilibili.com/x/member/web/account")
        if request.json()["code"] == -101:
            print("账号尚未登录.")
            print()
        elif request.json()["code"] == 0:
            print("账号已登录.")
            print(f"欢迎{request.json()['data']['uname']}登录.")
            print()
            self.mid = request.json()["data"]["mid"]
            self.is_login = True
        else:
            raise Exception("Invalid login code: " + str(request.json()["code"]))


def convert_cookies_to_dict(cookies) -> dict[str, str]:
    if not cookies:
        return {}
    return dict([li.split("=", 1) for li in cookies.split(";")])


def clean_cookie(dict_cookie: dict[str, str]) -> dict[str, str]:
    cleaned = {}
    for i, j in dict_cookie.items():
        cleaned[i.strip()] = j.strip()
    return cleaned


def remove(remove_str: str, want_remove: str):
    return remove_str.replace(want_remove, "")


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


def av2bv(aid):
    bytes = [b"B", b"V", b"1", b"0", b"0", b"0", b"0", b"0", b"0", b"0", b"0", b"0"]
    bv_idx = BV_LEN - 1
    tmp = (MAX_AID | aid) ^ XOR_CODE
    while int(tmp) != 0:
        bytes[bv_idx] = data[int(tmp % BASE)]
        tmp /= BASE
        bv_idx -= 1
    bytes[3], bytes[9] = bytes[9], bytes[3]
    bytes[4], bytes[7] = bytes[7], bytes[4]
    return "".join([i.decode() for i in bytes])


def bv2av(bvid: str):
    bvid_list = list(bvid)
    bvid_list[3], bvid_list[9] = bvid_list[9], bvid_list[3]
    bvid_list[4], bvid_list[7] = bvid_list[7], bvid_list[4]
    bvid_list = bvid_list[3:]
    tmp = 0
    for i in bvid_list:
        idx = data.index(i.encode())
        tmp = tmp * BASE + idx
    return (tmp & MASK_CODE) ^ XOR_CODE


def read_cookie():
    if os.path.exists("cookie.txt"):
        with open("cookie.txt") as f:
            cookie = f.read().strip()
            return cookie
    else:
        with open("cookie.txt", "w") as f:
            f.write("")


def encrypt_wbi(request_params: str):
    params = {i.split("=")[0]: i.split("=")[1] for i in request_params.split("&")}
    r = user_manager.get("https://api.bilibili.com/x/web-interface/nav", cache=True)
    wbi_img_url = r.json()["data"]["wbi_img"]["img_url"]
    wbi_sub_url = r.json()["data"]["wbi_img"]["sub_url"]
    oe = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12,
          38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62,
          11, 36, 20, 34, 44, 52]

    le = []
    key = (
            wbi_img_url.split("/")[-1].split(".")[0]
            + wbi_sub_url.split("/")[-1].split(".")[0]
    )
    for i in oe:
        le.append(key[i])
    key = "".join(le)[:32]
    params["wts"] = str(round(time.time()))
    wbi_sign = hashlib.md5(
        (urllib.parse.urlencode(dict(sorted(params.items()))) + key).encode()
    ).hexdigest()  # 计算 w_rid
    params["w_rid"] = wbi_sign
    return urllib.parse.urlencode(params)


# https://www.cnblogs.com/0506winds/p/13953600.html
# python字节自适应转化单位KB、MB、GB
def hum_convert(value):
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = 1024.0
    for i in range(len(units)):
        if (value / size) < 1:
            return "%.2f%s" % (value, units[i])
        value = value / size


def get_danmaku(cid: int, index: int = 1):
    resp = user_manager.get(
        f"https://api.bilibili.com/x/v2/dm/web/seg.so?type=1&oid={cid}&segment_index={index}",
        cache=True,
    )
    return resp.content


def get_more_danmaku(cid: int):
    view = parse_view(cid)
    total = int(view['dmSge']['total'])
    danmaku_byte = [get_danmaku(cid, i) for i in range(1, total + 1)]
    return b"".join(danmaku_byte)


def parse_view(cid: int):
    resp = user_manager.get(f"https://api.bilibili.com/x/v2/dm/web/view?oid={cid}&type=1", cache=True)
    dm_view = DmSegMobileReply()
    dm_view.ParseFromString(resp.content)
    dm_view = json.loads(MessageToJson(dm_view))
    return dm_view


def danmaku_provider():
    try:
        from danmakuC.bilibili import proto2ass
        return proto2ass
    except Exception:
        return Proto2ASS


user_manager = UserManager(read_cookie())
