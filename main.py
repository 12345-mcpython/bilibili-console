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
import argparse
import json
import os
import shutil
import sys

# from typing import Union, Tuple
# import os
# import base64
# import json
# import datetime
# import inspect
import threading
import typing
import datetime

try:
    import requests
    from bs4 import BeautifulSoup
    import rsa
    from google.protobuf import json_format
except ImportError as e:
    print("Warning: You don't run \"python -m pip install -r requirements.txt\". LBCC will exit.")
    sys.exit(1)

from biliass import Danmaku2ASS


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
        elif isinstance(json_str, JSON):
            self.json = json_str.json
        else:
            self.json = json.loads(json_str)

    def __getattr__(self, item):
        if isinstance(self.json[item], dict):
            return JSON(json.dumps(self.json[item], ensure_ascii=False))
        if isinstance(self.json[item], list):
            return [JSON(json.dumps(item, ensure_ascii=False)) for item in self.json[item]]
        return self.json[item]

    def __str__(self):
        return json.dumps(self.json, ensure_ascii=False)

    def __repr__(self):
        return json.dumps(self.json, ensure_ascii=False)

    def __getitem__(self, item):
        if isinstance(self.json[item], dict):
            return JSON(json.dumps(self.json[item], ensure_ascii=False))
        return self.json[item]


header = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77", "referer": "https://www.bilibili.com"}

cookie = ""

cookie_mapping = {}

command_mapping = {}

cached = {}

is_login = False

user_mid = None

protobuf_danmaku_enable = False

quality = {
    112: (1920, 1080, True),
    80: (1920, 1080, False),
    64: (1280, 720, False),
    32: (720, 480, False),
    16: (480, 360, False)
}

default_quality = 80


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
        except requests.exceptions.RequestException as error:
            print(f"Request {url} error! Will try {count} counts!")
            count -= 1
            if count <= 0:
                print("Request error!")
                raise error
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
        minute = long // 60
        if minute < 10:
            fmt = "0{}:{}"
        sec = long - minute * 60
        if sec < 10:
            fmt = "{}:0{}"
        if sec < 10 and minute < 10:
            fmt = "0{}:0{}"
        return fmt.format(minute, sec)


def view_comment(avid: typing.Union[int, str], page=1):
    if not isinstance(avid, int):
        avid = avid.strip()
    url = f"http://api.bilibili.com/x/v2/reply/main?mode=0&oid={avid}&next={page}&type=1"
    r = get(url, headers=header, no_cache=True)
    return r.json()['data']['replies'], r.json()['data']['cursor']['all_count']


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


def parse_text_command(command, local="main"):
    if not command_mapping.get(local + "_" + command.split(" ")[0]):
        print("未知命令!")
        return None, None
    command_class: Command = command_mapping.get(local + "_" + command.split(" ")[0])
    if len(command.split(" ")) - 1 > command_class.length:
        print("参数过多!")
        return None, None
    if len(command.split(" ")) - 1 < command_class.length:
        print("参数过少!")
        return None, None
    return command.split(" ")[0], command.split(" ")[1:]


def main_help():
    print("recommend 推荐")
    print("exit 退出")


def like(video_id, bvid=True, unlike=False):
    if not is_login:
        print("请先登录!")
    data = {'csrf': csrf_token}
    if bvid:
        data["bvid"] = video_id
    else:
        data["aid"] = video_id
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


def triple(video_id: str, bvid=True):
    if not is_login:
        print("请先登录!")
    data = {'csrf': csrf_token}
    if bvid:
        data["bvid"] = video_id
    else:
        data["aid"] = video_id

    r = post("http://api.bilibili.com/x/web-interface/archive/like/triple",
             headers=header, data=data)
    code = r.json()['code']
    if code == 0:
        print("三连成功!")
    else:
        print("三连失败!")
        print(code)
        print(r.json()['message'])


def collection(avid: str, media_id: str):
    data = {"rid": avid, "type": 2, "add_media_ids": media_id, "csrf": csrf_token}
    r = post("http://api.bilibili.com/x/v3/fav/resource/deal", headers=header, data=data)
    code = r.json()['code']
    if code == 0:
        print("收藏成功!")
    else:
        print("收藏失败!")
        print(code)
        print(r.json()['message'])


def play(video_id: str, bvid=True):
    print("\n")
    print("视频选集")
    if bvid:
        url = "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + video_id
    else:
        url = "https://api.bilibili.com/x/web-interface/view/detail?aid=" + video_id
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
            print("输入的并不是数字!")
            continue
        if int(page) > len(video) or int(page) <= 0:
            print("选视频超出范围!")
            continue
        cid = video[int(page) - 1]['cid']
        play_with_cid(video_id, cid)
        break
    return


def play_with_cid(video_id: str, cid: int, bangumi=False, bvid=True) -> None:
    if not bangumi:
        if bvid:
            url1 = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn={default_quality}&type=&otype=json" + "&bvid=" + video_id
        else:
            url1 = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn={default_quality}&type=&otype=json" + "&avid=" + video_id
    else:
        url1 = f"https://api.bilibili.com/pgc/player/web/playurl?qn={default_quality}&cid={cid}&ep_id={video_id}"
    req = get(url1, headers=header, no_cache=True)
    if req.json()['code'] != 0:
        print("获取视频错误!")
        print(req.url)
        print(req.json())
        return
    if not bangumi:
        flv_url = str(req.json()["data"]["durl"][0]["url"])
        higher = req.json()['data']['quality']
    else:
        flv_url = str(req.json()["result"]["durl"][0]["url"])
        higher = req.json()['result']['quality']
    width, height, is_higher = quality[higher]
    command = "mpv --sub-file=\"cached/{}.ass\" --user-agent=\"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) " \
              "Gecko/20100101 Firefox/51.0\" " \
              "--referrer=\"https://www.bilibili.com\" \"{}\"".format(cid,

                                                                      flv_url)
    r = requests.get(f"https://comment.bilibili.com/{cid}.xml")
    # Danmaku2ASS([f"cached/{cid}.xml"], "autodetect", f"cached/{cid}.ass", width, height, 0, "SimHei", 25.0, 1.0,
    #             10, 8, None,
    #             None, False, input_format="xml")
    if protobuf_danmaku_enable:
        so = get_danmaku(cid)
        a = Danmaku2ASS(
            so,
            width,
            height,
            input_format="protobuf",
            reserve_blank=0,
            font_face="SimHei",
            font_size=25,
            text_opacity=0.8,
            duration_marquee=15.0,
            duration_still=10.0,
            comment_filter=None,
            is_reduce_comments=False,
            progress_callback=None,
        )
        with open(f"cached/{cid}.ass", "w", encoding="utf-8") as f:
            f.write(a)
    else:
        a = Danmaku2ASS(
            r.content,
            width,
            height,
            input_format="xml",
            reserve_blank=0,
            font_face="SimHei",
            font_size=25,
            text_opacity=0.8,
            duration_marquee=15.0,
            duration_still=10.0,
            comment_filter=None,
            is_reduce_comments=False,
            progress_callback=None,
        )
        with open(f"cached/{cid}.ass", "w", encoding="utf-8") as f:
            f.write(a)
    time = req.json()['data']["timelength"] / 1000
    update_history(video_id, cid, round(time) + 1)
    a = threading.Thread(target=os.system, args=(command,))
    a.start()
    thread_pool.append(a)


def get_danmaku(cid):
    url = "https://api.bilibili.com/x/v2/dm/web/seg.so"
    params = {
        'type': '1',
        'oid': cid,
        'segment_index': '1'
    }
    headers = {
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36"
    }
    resp = requests.get(url, headers=headers, params=params, timeout=8)
    return resp.content


def update_history(video_id, cid, progress, bvid=True):
    data = {"cid": cid, "played_time": progress}
    if bvid:
        data["bvid"] = video_id
    else:
        data["aid"] = video_id
    r = post("https://api.bilibili.com/x/click-interface/web/heartbeat", data=data, headers=header)
    if r.json()['code'] != 0:
        print(data)
        print(r.json()['code'])
        print(r.json()['message'])


def recommend():
    print("推荐界面")
    flag = True
    ls = []
    while flag:
        flag1 = True
        r = get("https://api.bilibili.com/x/web-interface/index/top/feed/rcmd?ps=5",
                headers=header, no_cache=True)
        rcmd = JSON(r)
        rcmd = rcmd.data.item
        ls.append(rcmd)
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
            if command == "exit":
                flag = False
                break
            if not command:
                break
            command, argument = parse_text_command(command, local="recommend")
            if not command:
                continue
            if not argument[0].isdecimal():
                print("输入的不是整数!")
                continue
            if int(argument[0]) > len(rcmd) or int(argument[0]) <= 0:
                print("选视频超出范围!")
                continue
            bvid = rcmd[int(argument[0]) - 1]['bvid']
            if command == "play":
                play(bvid)
            elif command == "like":
                like(bvid)
            elif command == "triple":
                triple(bvid)
            elif command == 'unlike':
                like(bvid, unlike=True)
            elif command == "collection":
                media_id = list_fav(return_info=True)
                collection(media_id=media_id, avid=rcmd[int(argument[0]) - 1]['id'])
                print("收藏成功!")
            # elif a == "view_b_collection":
            #     play_b_collection(bvid)


def register_command(command, length, local="main", run=lambda: None, should_run=True, args=(), kwargs={}):
    command_mapping[local + "_" + command] = Command(local + "_" + command, length, run, should_run, args=args,
                                                     kwargs=kwargs)


thread_pool = []


def exit_all():
    for i in thread_pool:
        i.join()
    sys.exit(0)


def register_all_command():
    register_command("recommend", 0, run=recommend)
    register_command("exit", 0, run=exit_all)
    register_command("help", 0, run=main_help)
    register_command("address", 1, run=address)
    register_command("favorite", 0, run=list_fav)
    register_command("enable_protobuf_danmaku", 0, run=enable_protobuf_danmaku)
    register_command("disable_protobuf_danmaku", 0, run=disable_protobuf_danmaku)
    register_command("clean_memory_cache", 0, run=clean_memory_cache)
    register_command("clean_local_cache", 0, run=clean_local_cache)
    register_command("like", 1, should_run=False, local="recommend")
    register_command("unlike", 1, should_run=False, local="recommend")
    register_command("play", 1, should_run=False, local="recommend")
    register_command("triple", 1, should_run=False, local="recommend")
    register_command("exit", 0, should_run=False, local="recommend")
    register_command("collection", 1, should_run=False, local="recommend")
    register_command("like", 1, should_run=False, local="address")
    register_command("unlike", 1, should_run=False, local="address")
    register_command("play", 0, should_run=False, local="address")
    register_command("triple", 1, should_run=False, local="address")
    register_command("exit", 0, should_run=False, local="address")
    register_command("collection", 1, should_run=False, local="address")
    register_command("like", 1, should_run=False, local="favorite")
    register_command("unlike", 1, should_run=False, local="favorite")
    register_command("play", 1, should_run=False, local="favorite")
    register_command("triple", 1, should_run=False, local="favorite")
    register_command("exit", 0, should_run=False, local="favorite")
    register_command("config", 0, run=config)
    register_command("add_cookie", 0, run=add_cookie)
    register_command("set_users", 0, run=set_users)


def video_status(video_id: str):
    url = "http://api.bilibili.com/x/web-interface/archive/stat?aid={}"
    if video_id.startswith('av'):
        video_id = video_id.strip("av")
        url = "http://api.bilibili.com/x/web-interface/archive/stat?aid={}".format(
            video_id)
    if video_id.startswith("BV"):
        url = "http://api.bilibili.com/x/web-interface/archive/stat?bvid={}".format(
            video_id)

    r = get(url.format(video_id), headers=header)
    json1 = r.json()
    if json1['code'] != 0:
        print("获取状态失败!")
        print(json1['message'])
        return None, None, None, None, None, None, None, None, None
    return json1['data']['bvid'], json1['data']['aid'], json1['data']['view'], json1['data']['danmaku'], json1['data'][
        'like'], json1['data']['coin'], json1['data']['favorite'], json1['data']['share'], json1['data']['reply']


def address(video: str):
    if "b23.tv" in video:
        video = get(video).url
    if video.startswith("http"):
        video = video.split("/")[-1].split("?")[0]
        if not video:
            video = video.split("/")[-2]
    bvid, avid, view, danmaku, like_, coin, favorite, share, comment_count = video_status(
        str(video))
    if not all([bvid, avid, view, danmaku, like_, coin, favorite, share, comment_count]):
        print("链接错误!")
        return
    print('avid: ', avid)
    print("bvid: ", bvid)
    print("观看量: ", view)
    print("弹幕: ", danmaku)
    print("点赞量: ", like_)
    print("硬币量: ", coin)
    print("收藏量: ", favorite)
    print("转发量: ", share)
    print("评论量: ", comment_count)
    while True:
        command = input("链接选项: ")
        if command == "exit":
            break
        if not command:
            continue
        command, argument = parse_text_command(command, local="address")
        if not command:
            continue
        if command != "play":
            if not argument[0].isdecimal():
                print("输入的不是整数!")
                continue
        if command == "play":
            play(bvid)
        elif command == "like":
            like(bvid)
        elif command == "triple":
            triple(bvid)
        elif command == 'unlike':
            like(bvid, unlike=True)
        elif command == "collection":
            media_id = list_fav(return_info=True)
            collection(media_id=media_id, avid=avid)
            print("收藏成功!")


def config():
    print("设置")
    print()
    print("1.清空本地缓存")
    print("2.清空内存缓存")
    print("3.调整分辨率")
    print("4.实验选项")
    print("5.退出")
    while True:
        choose = int(input("设置: "))
        if choose == 1:
            clean_local_cache()
            return
        elif choose == 2:
            clean_memory_cache()
            return
        elif choose == 3:
            set_quality()
            return
        elif choose == 4:
            print("Error!")
        elif choose == 5:
            return
        else:
            print("输入错误.")
            return


def list_fav(return_info=False):
    fav_list = get(
        "https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid={mid}&jsonp=jsonp".format(mid=user_mid),
        headers=header)
    fav_list = JSON(fav_list.json()).data.list
    print("\n")
    print("选择收藏夹")
    print("\n")
    for i, j in enumerate(fav_list):
        print(f"{i + 1}: {j.title}")
    while True:
        choose = input("选择收藏夹: ")
        if choose == "exit":
            break
        if not choose:
            continue
        if not choose.isdecimal():
            print("输入的不是整数!")
            continue
        if int(choose) > len(fav_list) or int(choose) <= 0:
            print("选视频超出范围!")
            continue
        a = fav_list[int(choose) - 1].id
        if not return_info:
            list_collection(a)
            break
        return a


def list_collection(media_id):
    url = f"http://api.bilibili.com/x/v3/fav/resource/list?ps=20&media_id={media_id}"
    ls = get(url, headers=header)
    ls = JSON(ls.json())
    total = ls.data.info.media_count // 20 + 1
    count = 1
    flag = True
    while flag:
        url = f"http://api.bilibili.com/x/v3/fav/resource/list?ps=20&media_id={media_id}&pn={count}"
        ls = get(url, headers=header)
        ls = JSON(ls.json())
        if total < count:
            print("到头了!")
            return
        ls = ls.data.medias
        flag1 = True
        for num, item in enumerate(ls):
            print(num + 1, ":")
            item = JSON(item)
            print("封面: ", item.cover)
            print("标题: ", item.title)
            print("作者: ", item.upper.name, " bvid: ", item.bvid, " 日期: ", datetime.datetime.fromtimestamp(
                item.pubtime).strftime("%Y-%m-%d %H:%M:%S"), " 视频时长:", format_long(item.duration), " 观看量: ",
                  item.cnt_info.play)
        while flag1:
            command = input("收藏选项: ")
            if command == "exit":
                return
            if not command:
                break
            command, argument = parse_text_command(command, local="favorite")
            if not command:
                continue
            if not argument[0].isdecimal():
                print("输入的不是整数!")
                continue
            if int(argument[0]) > len(ls) or int(argument[0]) <= 0:
                print("选视频超出范围!")
                continue
            bvid = ls[int(argument[0]) - 1]['bvid']

            if command == "play":
                play(bvid)
            elif command == "exit":
                return
            elif command == "like":
                like(bvid)
            elif command == "triple":
                triple(bvid)
            elif command == 'unlike':
                like(bvid, unlike=True)

        count += 1


def init():
    if os.path.exists("init"):
        return False
    print("正在初始化LBCC.")
    if not os.path.exists("cached"):
        os.mkdir("cached")
    if not os.path.exists("users"):
        os.mkdir("users")
    with open("init", "w"):
        pass
    print("初始化完成.")
    return True


def main():
    while True:
        command = input("主选项: ")
        parse_command(command)


def get_login_status(cookie=None, set_is_login=True, list_user=False, printout=True):
    global is_login, user_mid
    cached_header = {}
    if list_user:
        cached_header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
            "referer": "https://www.bilibili.com", 'cookie': cookie}
    r = get('https://api.bilibili.com/x/member/web/account',
            headers=cached_header if list_user else header)
    a = JSON(r)
    if a.code == -101:
        if printout:
            print("账号尚未登录! ")
        return False
    elif a.code == 0:
        if not list_user:
            print("账号已登录.")
            print("欢迎" + a.data.uname + "回来.")
        else:
            if printout:
                print("用户" + a.data.uname + "已经登录.")
            return a.data.uname
        if set_is_login:
            is_login = True
            user_mid = a.data.mid
        return True


def check_login(cookie):
    cached_header = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
        "referer": "https://www.bilibili.com", 'cookie': cookie}
    r = get('https://api.bilibili.com/x/member/web/account',
            headers=cached_header)
    a = JSON(r)
    if JSON(r).code == -101:
        return False
    elif a.code == 0:
        return a.data.uname

def cookie_to_dict(string):
    dictionary = {}
    for i in string.split(";"):
        key, value = i.strip().split("=")
        dictionary[key] = value
    return dictionary


def response_to_cookie(request: requests.Response):
    string = ""
    for i in request.cookies:
        string += i.name + "=" + i.value + ";"
    return string[:-1]


def generate_search_cookie():
    print("配置搜索Cookie.")
    r = requests.get("https://www.bilibili.com/", headers=header)
    return response_to_cookie(r)


def ask_cookie(first_use):
    global cookie
    if first_use:
        print("你是第一次使用LBCC, 是否配置cookie? (y/n)")
        print("Laosun Studios 保证用户数据是妥善存放在本地且不会被上传到除了B站以外的服务器.")
        choose = input()
        if choose.lower() == "y":
            cookie_or_file = input("请输入cookies或文件路径: ")
            if os.path.exists(cookie_or_file):
                with open(cookie_or_file) as f:
                    cookie = f.read()
            else:
                cookie = cookie_or_file
            username = check_login(cookie)
            if username:
                print("Cookie指定的用户为: ", username)
            else:
                print("Cookie未指定用户,取消配置.")
                return
            with open(f"users/{username}.txt", "w") as f:
                f.write(cookie)
            with open("cookie", "w") as f:
                pass
            print("Cookie配置成功! LBCC将会退出. ")
            input()
            sys.exit(0)
    return


def add_cookie():
    cookie_or_file = input("请输入cookies或文件路径: ")
    if os.path.exists(cookie_or_file):
        with open(cookie_or_file) as f:
            cookie = f.read()
    else:
        cookie = cookie_or_file
    username = check_login(cookie)
    if username:
        print("Cookie指定的用户为: ", username)
    else:
        print("Cookie未指定用户,取消配置.")
        return
    with open(f"users/{username}.txt", "w") as f:
        f.write(cookie)
    with open("cookie", "w") as f:
        pass
    print("Cookie配置成功! LBCC将会退出.")
    input()
    sys.exit(0)


def enable_protobuf_danmaku():
    global protobuf_danmaku_enable
    protobuf_danmaku_enable = True


def disable_protobuf_danmaku():
    global protobuf_danmaku_enable
    protobuf_danmaku_enable = False


def clean_memory_cache():
    global cached
    cached = {}


def clean_local_cache():
    shutil.rmtree("cached")


def set_users():
    ls = os.listdir("./users")
    print("选择cookie")
    for i, j in enumerate(ls):
        print(f"{i + 1}: {j.split('.')[0]}")
    while True:
        choose = input("选项: ")
        choose = int(choose)
        if choose > len(ls) or choose <= 0:
            print("输入错误.")
        print(f"你选择的是{ls[choose - 1].split('.')[0]}.")
        with open("user", "w") as f:
            f.write(ls[choose - 1].split(".")[0])
        print("配置成功. LBCC将会退出.")
        input()
        sys.exit(0)


def set_quality():
    global default_quality
    for i, j in enumerate(quality.items()):
        print(f"{i}: {j[1][0]}x{j[1][1]} " + ("高码率" if j[1][2] else ""))
    while True:
        try:
            quality_choose = int(input("选择分辨率: "))
        except ValueError:
            print("请输入数字!")
            continue
        if quality_choose < 0 or quality_choose > len(quality.items()):
            print("超出界限!")
            continue
        elif not quality_choose:
            print("请输入数字!")
            continue
        default_quality = list(quality.keys())[quality_choose]
        print("设置成功!")
        break


print("LBCC v1.0.0-dev.")
print("Type \"help\" for more information.")


def get_available_user():
    if not os.path.exists("cookie"):
        return False
    if os.path.exists("user"):
        with open("user") as f:
            return f.read()
    elif len(os.listdir("users")) != 0:
        return os.listdir("users")[0]
    else:
        return None


def test_cookie():
    for i in os.listdir("users"):
        with open(f"users/{i}") as f:
            cookie = f.read()
        username = get_login_status(cookie, set_is_login=False, list_user=True, printout=False)
        if username:
            print(f"Cookie {i} 有效.")
        else:
            print(f"Cookie {i} 无效或已登出.")
            return


def parse_experimental_features(feature_args):
    if feature_args == "protobuf":
        enable_protobuf_danmaku()
        print("已启用特性: protobuf弹幕")
    elif not feature_args:
        return
    else:
        print("未知特性: ", feature_args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LBCC命令行参数')
    parser.add_argument("-ef", '--experimental-features', type=str, help="启用实验特性")
    args = parser.parse_args()
    parse_experimental_features(args.experimental_features)
    first_use = init()
    ask_cookie(first_use)
    username = get_available_user()
    if not username:
        header["cookie"] = generate_search_cookie()
    else:
        with open(f"users/{username}") as f:
            header["cookie"] = f.read()
    get_login_status()
    register_all_command()
    cookie_mapping = cookie_to_dict(header["cookie"])
    csrf_token = cookie_mapping.get("bili_jct")
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
