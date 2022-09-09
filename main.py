#!/usr/bin/env python3
"""
Copyright (c) 2022 Laosun Studios. All Rights Reserved.

Distributed under GPL-3.0 License.

The product is developing. Effect currently
displayed is for reference only. Not indicative
of final product.

Copyright (C) 2022 Laosun Studios.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

The old version also use the GPL-3.0 license, not MIT License.
"""
# import shutil
import json
import os
import sys

# from typing import Union, Tuple
# import os
# import base64
# import json
# import datetime
# import inspect
import typing
import datetime

try:
    import requests
    from bs4 import BeautifulSoup
    import rsa
except ImportError as e:
    print("Warning: You don't run \"python -m pip install -r requirements.txt\". LBCC will exit.")
    sys.exit(1)

from danmaku2ass import Danmaku2ASS


class Command:
    def __init__(self, command, length=0, run=lambda: None, should_run=True, args=(), kwargs={}):
        self.command = command
        self.length = length
        self.run = run
        self.should_run = should_run
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return "<{} command={} length={}>".format(type(self).__name__, self.command, self.length)


class JSON:
    def __init__(self, json_str: typing.Union[str, requests.Response, dict]):
        if isinstance(json_str, requests.Response):
            self.json = json_str.json()
        elif isinstance(json_str, dict):
            self.json = json_str
        else:
            self.json = json.loads(json_str)

    def __getattr__(self, item):
        if isinstance(self.json[item], dict):
            return JSON(json.dumps(self.json[item]))
        return self.json[item]

    def __str__(self):
        return json.dumps(self.json)

    def __getitem__(self, item):
        if isinstance(self.json[item], dict):
            return JSON(json.dumps(self.json[item]))
        return self.json[item]


header = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77"}

cookie = ""

cookie_mapping = {}

command_mapping = {}

cached = {}

is_login = False

quality = {
    112: (1920, 1080),
    80: (1920, 1080),
    64: (1280, 720),
    32: (720, 480),
    16: (480, 360)
}


# 辅助方法

def get(url: str, params=None, no_cache=False, **kwargs) -> requests.Response:
    if cached.get(url):
        return cached.get(url)
    else:
        count = 3
        while True:
            try:
                r = requests.get(url, params=params, timeout=5, **kwargs)
                break
            except requests.exceptions.RequestException as request_error:
                print(f"Request {url} error! Will try {count} counts!")
                count -= 1
                if count <= 0:
                    raise request_error
        if not no_cache:
            cached[url] = r
        return r


def post(url: str, params=None, **kwargs) -> requests.Response:
    count = 3
    while True:
        try:
            r = requests.post(url, params=params, timeout=5, **kwargs)
            break
        except requests.exceptions.RequestException as e:
            print(f"Request {url} error! Will try {count} counts!")
            count -= 1
            if count <= 0:
                print("Request error!")
                raise e
    return r


def format_long(long):
    if long > 60 * 60:
        fmt = "{}:{}:{}"
        hour = long // (60 * 60)
        minute = (long - (hour * 60 * 60)) // 60
        sec = long - (hour * 60 * 60) - minute * 60
        if minute < 10:
            fmt = "{}:0{}:{}"
        if sec < 10:
            fmt = "{}:{}:0{}"
        if sec < 10 and minute < 10:
            fmt = "{}:0{}:0{}"
        return fmt.format(hour, minute, sec)
    else:
        fmt = "{}:{}"
        minute = (long) // 60
        if minute < 10:
            fmt = "0{}:{}"
        sec = long - minute * 60
        if sec < 10:
            fmt = "{}:0{}"
        if sec < 10 and minute < 10:
            fmt = "0{}:0{}"
        return fmt.format(minute, sec)


def read_cookie():
    global cookie, cookie_mapping, header
    with open("cookie.txt") as f:
        cookie = f.read()
    for i in cookie.split(";"):
        try:
            key, value = i.strip().split("=")
        except ValueError:
            return
        cookie_mapping[key] = value
    header["cookie"] = cookie


def write_cookie(cookie_or_response: typing.Union[requests.Response, str], append=False):
    if isinstance(cookie_or_response, requests.Response):
        with open("cookie.txt", "w" if not append else "a") as f:
            string = ""
            for i in cookie_or_response.cookies:
                string += i.name + "=" + i.value + ";"
            f.write(string[:-1])
    elif isinstance(cookie_or_response, str):
        with open("cookie.txt", "w" if not append else "a") as f:
            f.write(cookie_or_response)


def response_to_cookie(request: requests.Response):
    string = ""
    for i in request.cookies:
        string += i.name + "=" + i.value + ";"
    return string[:-1]


def cookie_to_dict(string):
    dictionary = {}
    for i in string.split(";"):
        key, value = i.strip().split("=")
        dictionary[key] = value
    return dictionary


def generate_search_cookie():
    r = requests.get("https://www.bilibili.com/", headers=header)
    return response_to_cookie(r)


# 界面

def parse_command(command, local="main"):
    if not command_mapping.get(local + "_" + command.split(" ")[0]):
        print("未知命令!")
        return
    command_class: Command = command_mapping.get(local + "_" + command.split(" ")[0])
    if len(command.split(" ")) - 1 > command_class.length:
        print("参数过多!")
        return
    if len(command.split(" ")) - 1 < command_class.length:
        print("参数过少!")
        return
    if command_class.should_run:
        command_class.run(*command.split(" ")[1:], *command_class.args, **command_class.kwargs)
    else:
        return command.split(" ")[0], command.split(" ")[1:]


def main_help():
    print("recommend 推荐")
    print("exit 退出")


def get_login_status():
    global is_login
    r = get('https://api.bilibili.com/x/member/web/account',
            headers=header)
    a = JSON(r)
    if a.code == -101:
        print("账号尚未登录! ")
    elif a.code == 0:
        print("账号已登录.")
        print("欢迎" + a.data.uname + "回来.")
        is_login = True


def like(index: str, rcmd, unlike=False):
    if index.isdecimal():
        print("参数错误!")
    if not is_login:
        print("请先登录!")
    data = {'bvid': rcmd[int(index) - 1]['bvid']}
    if not unlike:
        data['like'] = 1
    else:
        data['like'] = 2
    data['csrf'] = csrf_token
    r = post("http://api.bilibili.com/x/web-interface/archive/like",
             data=data, headers=header)
    code = r.json()['code']
    if code == 0:
        if not unlike:
            print("点赞成功!")
        else:
            print("取消点赞成功!")
    else:
        print("点赞失败!")
        print(code)
        print(r.json()['message'])


def triple(index: str, rcmd: dict):
    bvid = rcmd[int(index) - 1]['bvid']
    data = {'bvid': bvid, 'csrf': csrf_token}
    r = post("http://api.bilibili.com/x/web-interface/archive/like/triple",
             headers=header, data=data)
    code = r.json()['code']
    if code == 0:
        print("三连成功!")
    else:
        print("三连失败!")
        print(code)
        print(r.json()['message'])


def play(index: str, rcmd: dict):
    print("\n")
    print("视频选集")
    bvid = rcmd[int(index) - 1]['bvid']
    url = "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + bvid
    r = get(url, headers=header)
    video = r.json()['data']["View"]["pages"]
    for i in video:
        print(f"{i['page']}: {i['part']}")
    print("请以冒号前面的数字为准选择视频.")
    while True:
        page = input("选择视频: ")
        if page == "exit":
            break
        if not page:
            continue
        if not page.isdigit():
            continue
        if int(page) > len(video) or int(page) <= 0:
            print("选视频错误!")
            continue
        cid = video[int(page) - 1]['cid']
        play_with_cid(bvid, cid)
        break
    return


def play_with_cid(bvid: str, cid: int, bangumi=False) -> None:
    if not bangumi:
        url1 = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn=80&type=&otype=json" + "&bvid=" + bvid

    else:
        url1 = f"https://api.bilibili.com/pgc/player/web/playurl?qn=80&cid={cid}&ep_id={bvid}"
    req = get(url1, headers=header, no_cache=True)
    if req.json()['code'] != 0:
        print("获取视频错误!")
        print(req.url)
        print(req.json())
        return
    if not bangumi:
        url111 = str(req.json()["data"]["durl"][0]["url"])
        higher = req.json()['data']['quality']
    else:
        url111 = str(req.json()["result"]["durl"][0]["url"])
        higher = req.json()['result']['quality']
    width, height = quality[higher]
    command = "mpv --sub-file=\"cached/{}.ass\" --user-agent=\"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) " \
              "Gecko/20100101 Firefox/51.0\" " \
              "--referrer=\"https://www.bilibili.com\" \"{}\"".format(cid,
                                                                      url111)
    if not os.path.exists("cached"):
        os.mkdir("cached")
    if not os.path.exists(f"cached/{cid}.xml"):
        r = requests.get(f"https://comment.bilibili.com/{cid}.xml")
        with open(f"cached/{cid}.xml", "wb") as f:
            f.write(r.content)
    Danmaku2ASS([f"cached/{cid}.xml"], "autodetect", f"cached/{cid}.ass", width, height, 0, "SimHei", 25.0, 1.0,
                10, 8, None,
                None, False)
    time = req.json()['data']["timelength"] / 1000
    update_history(bvid, cid, round(time) + 1)
    os.system(command)


def update_history(bvid, cid, progress):
    data = {"cid": cid, "played_time": progress, 'bvid': bvid}
    r = post("http://api.bilibili.com/x/click-interface/web/heartbeat", data=data, headers=header)
    if r.json()['code'] != 0:
        print(data)
        print(r.json()['code'])
        print(r.json()['message'])


def recommend():
    def register_all_command_recommend():
        register_command("like", 1, run=like, local="recommend", kwargs={'rcmd': rcmd})
        register_command("unlike", 1, run=like, local="recommend", kwargs={"unlike": True, "rcmd": rcmd})
        register_command("play", 1, run=play, local="recommend", kwargs={"rcmd": rcmd})
        register_command("exit", 0, run=exit_all, local="recommend")
        register_command("triple", 1, run=triple, local="recommend", kwargs={"rcmd": rcmd})
        register_command("next", 0, run=next_1, local="recommend")
        register_command("prev", 0, run=prev, local="recommend")

    def exit_all():
        nonlocal flag, flag1
        flag = False
        flag1 = False

    def next_1():
        nonlocal flag1
        flag1 = False

    def prev():
        nonlocal is_prev, flag1
        is_prev = True
        flag1 = False

    print("推荐界面")
    flag = True
    is_prev = False
    ls = []
    index = 0
    while flag:
        flag1 = True
        r = get("https://api.bilibili.com/x/web-interface/index/top/feed/rcmd?ps=5",
                headers=header, no_cache=True)
        rcmd = JSON(r)
        rcmd = rcmd.data.item
        ls.append(rcmd)
        if not is_prev:
            pass
        else:
            try:
                rcmd = ls[index - 1]
            except IndexError:
                print("无上一页!")
        is_prev = False
        for num, item in enumerate(rcmd):
            print(num + 1, ":")
            item = JSON(item)
            print("封面: ", item.pic)
            print("标题: ", item.title)
            print("作者: ", item.owner.name, " bvid: ", item.bvid, " 日期: ", datetime.datetime.fromtimestamp(
                item.pubdate).strftime("%Y-%m-%d %H:%M:%S"), " 视频时长:", format_long(item.duration), " 观看量: ",
                  item.stat.view)

        while flag1:
            command = input("推荐选项: ")
            register_all_command_recommend()
            parse_command(command, local="recommend")
        index += 1


def register_command(command, length, local="main", run=lambda: None, should_run=True, args=(), kwargs={}):
    command_mapping[local + "_" + command] = Command(local + "_" + command, length, run, should_run, args=args,
                                                     kwargs=kwargs)


def register_all_command():
    register_command("recommend", 0, run=recommend)
    register_command("exit", 0, run=sys.exit, args=(0,))
    register_command("help", 0, run=main_help)


def test(*args, **kwargs):
    print(args, kwargs)


print("LBCC v1.0.0-dev.")
print("Type \"help\" for more information.")


def init():
    if os.path.exists("init"):
        return
    print("正在初始化LBCC.")
    if not os.path.exists("collection.txt"):
        with open("collection.txt", "w"):
            pass
    if not os.path.exists("cookie.txt"):
        with open("cookie.txt", "w"):
            pass
    if not os.path.exists("cached"):
        os.mkdir("cached")
    if not os.path.exists("users"):
        os.mkdir("users")
    with open("init", "w"):
        pass
    print("初始化完成.")


def main():
    while True:
        command = input("主选项: ")
        parse_command(command)


if __name__ == "__main__":
    init()
    register_all_command()
    read_cookie()
    get_login_status()
    csrf_token = cookie_mapping.get("bili_jct")
    if not is_login:
        if not cookie_mapping.get("buvid3"):
            print("初始化cookie中.")
            a = generate_search_cookie()
            write_cookie(a)
            print("初始化完成.")
    else:
        if not cookie_mapping.get("buvid3"):
            print("初始化cookie.")
            a = "; " + generate_search_cookie()
            write_cookie(a)
            print("初始化完成.")
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
