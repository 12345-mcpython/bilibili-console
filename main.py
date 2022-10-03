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

# from typing import Union, Tuple
# import os
# import base64
# import json
# import datetime
# import inspect
# import shutil
# import argparse
# import rsa

import json
import os
import sys
import threading
import typing
import datetime
import shutil

import requests

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

local_cookie = ""

cookie_mapping = {}

command_mapping = {}

cached_response = {}

is_login = False

local_user_mid = None

quality = {
    127: (7680, 4320, False),
    120: (3840, 2160, False),
    112: (1920, 1080, True),
    80: (1920, 1080, False),
    64: (1280, 720, False),
    32: (720, 480, False),
    16: (480, 360, False)
}

default_quality = 80


# 辅助方法

def get(url: str, params=None, no_cache=False, **kwargs) -> requests.Response:
    if cached_response.get(url):
        return cached_response.get(url)
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
            cached_response[url] = r
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


def coin(video_id, coin_count, bvid=True, like=False):
    if not is_login:
        print("请先登录!")
    data = {'csrf': csrf_token, 'multiply': coin_count}
    if bvid:
        data["bvid"] = video_id
    else:
        data["aid"] = video_id
    if like:
        data['select_like'] = 1
    r = post("http://api.bilibili.com/x/web-interface/coin/add",
             data=data, headers=header)
    code = r.json()['code']
    if code == 0:
        print("投币成功!")
    else:
        print("投币失败!")
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
        play_with_dash(video_id, cid, bvid)
        # play_with_cid(video_id, cid)
        break
    return


def play_with_cid(video_id: str, cid: int, bangumi=False, bvid=True) -> None:
    if not bangumi:
        if bvid:
            url1 = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn={default_quality}&ty" \
                   f"pe=&otype=json&bvid={video_id}"
        else:
            url1 = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn={default_quality}&type=&oty" \
                   f"pe=json&avid={video_id}"
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
              "--referrer=\"https://www.bilibili.com\" \"{}\"".format(cid, flv_url)
    # r = requests.get(f"https://comment.bilibili.com/{cid}.xml")
    # Danmaku2ASS([f"cached/{cid}.xml"], "autodetect", f"cached/{cid}.ass", width, height, 0, "SimHei", 25.0, 1.0,
    #             10, 8, None,
    #             None, False, input_format="xml")
    # if protobuf_danmaku_enable:
    a = Danmaku2ASS(
        get_danmaku(cid),
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
    # else:
    #     a = Danmaku2ASS(
    #         r.content,
    #         width,
    #         height,
    #         input_format="xml",
    #         reserve_blank=0,
    #         font_face="SimHei",
    #         font_size=25,
    #         text_opacity=0.8,
    #         duration_marquee=15.0,
    #         duration_still=10.0,
    #         comment_filter=None,
    #         is_reduce_comments=False,
    #         progress_callback=None,
    #     )
    #     with open(f"cached/{cid}.ass", "w", encoding="utf-8") as f:
    #         f.write(a)
    if not bangumi:
        time = req.json()['data']["timelength"] / 1000
        update_history(video_id, cid, round(time) + 1)
    a = threading.Thread(target=os.system, args=(command,))
    a.start()


# --merge-files
def play_with_dash(video_id: str, cid: int, bvid=True):
    if bvid:
        url1 = f"https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={video_id}&fnval=16&fourk=0"
    else:
        url1 = f"https://api.bilibili.com/x/player/playurl?cid={cid}&avid={video_id}&fnval=16&fourk=0"
    r = get(url1, headers=header)
    videos = r.json()['data']['dash']["video"]
    audios = r.json()['data']['dash']["audio"]

    video_mapping = {}
    audio_mapping = {}

    for i in videos:
        if not video_mapping.get(i['id']):
            video_mapping[i['id']] = [i['base_url']]
        else:
            video_mapping[i['id']].append(i['base_url'])

    for i in audios:
        audio_mapping[i['id']] = i['base_url']

    default_audio = sorted(list(audio_mapping.keys()), reverse=True)[0]
    default_video = sorted(list(video_mapping.keys()), reverse=True)[0]

    audio_url = audio_mapping[default_audio]
    try:
        video_url = video_mapping[default_quality][0]
    except KeyError:
        video_url = video_mapping[default_video][0]
    width, height, is_higher = quality[default_quality]
    a = Danmaku2ASS(
        get_danmaku(cid),
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
    command = f"mpv --sub-file=\"cached/{cid}.ass\" --user-agent=\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
              f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53\" " \
              f"--referrer=\"https://www.bilibili.com\" \"{video_url}\" --audio-file=\"{audio_url}\" "
    time = r.json()['data']["timelength"] / 1000
    update_history(video_id, cid, round(time) + 1)
    a = threading.Thread(target=os.system, args=(command,))
    a.start()


def get_danmaku(cid):
    url = "https://api.bilibili.com/x/v2/dm/web/seg.so"
    params = {
        'type': '1',
        'oid': cid,
        'segment_index': '1'
    }
    headers = {
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/72.0.3626.81 Safari/537.36 "
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
            avid = rcmd[int(argument[0]) - 1]['id']
            if command == "play":
                play(bvid)
            elif command == "like":
                like(bvid)
            elif command == "triple":
                triple(bvid)
            elif command == 'unlike':
                like(bvid, unlike=True)
            elif command == "favorite":
                media_id = list_fav(return_info=True)
                collection(media_id=media_id, avid=rcmd[int(argument[0]) - 1]['id'])
                print("收藏成功!")
            elif command == "video_info":
                get_video_info(bvid, True)
            elif command == "view_collection":
                view_collection(bvid, True)
            elif command == 'coin':
                coin_count = int(input("请输入投币量(1-2): "))
                if coin_count != 1 and coin_count != 2:
                    print("输入错误!")
                coin(bvid, coin_count, bvid=True)
            elif command == "view_comment":
                comment_viewer(avid)


def register_command(command, length, local="main", run=lambda: None, should_run=True, args=(), kwargs={}):
    command_mapping[local + "_" + command] = Command(local + "_" + command, length, run, should_run, args=args,
                                                     kwargs=kwargs)


def exit_all():
    sys.exit(0)


def register_all_command():
    register_command("recommend", 0, run=recommend)
    register_command("exit", 0, run=exit_all)
    register_command("address", 1, run=address)
    register_command("favorite", 0, run=list_fav)
    register_command("search", 0, run=search)
    register_command("bangumi", 0, run=bangumi)
    register_command("config", 0, run=config)
    register_command("add_cookie", 0, run=add_cookie)
    register_command("set_users", 0, run=set_users)
    # recommend
    register_command("like", 1, should_run=False, local="recommend")
    register_command("unlike", 1, should_run=False, local="recommend")
    register_command("play", 1, should_run=False, local="recommend")
    register_command("triple", 1, should_run=False, local="recommend")
    register_command("exit", 0, should_run=False, local="recommend")
    register_command("collection", 1, should_run=False, local="recommend")
    register_command("view_collection", 1, should_run=False, local='recommend')
    register_command("video_info", 1, should_run=False, local='recommend')
    register_command("view_comment", 1, should_run=False, local="recommend")
    register_command("coin", 1, should_run=False, local="recommend")
    # address
    register_command("like", 0, should_run=False, local="address")
    register_command("unlike", 0, should_run=False, local="address")
    register_command("play", 0, should_run=False, local="address")
    register_command("triple", 0, should_run=False, local="address")
    register_command("exit", 0, should_run=False, local="address")
    register_command("video_info", 0, should_run=False, local='address')
    register_command("view_collection", 0, should_run=False, local='address')
    register_command("collection", 0, should_run=False, local="address")
    register_command("view_comment", 0, should_run=False, local="address")
    register_command("coin", 0, should_run=False, local="address")
    # favorite
    register_command("like", 1, should_run=False, local="favorite")
    register_command("unlike", 1, should_run=False, local="favorite")
    register_command("play", 1, should_run=False, local="favorite")
    register_command("triple", 1, should_run=False, local="favorite")
    register_command("exit", 0, should_run=False, local="favorite")
    register_command("video_info", 1, should_run=False, local='favorite')
    register_command("view_collection", 1, should_run=False, local='favorite')
    register_command("view_comment", 1, should_run=False, local='favorite')
    register_command("coin", 1, should_run=False, local="favorite")
    # comment
    register_command("like", 1, should_run=False, local='comment')
    register_command("unlike", 1, should_run=False, local='comment')
    register_command('view_reply', 1, should_run=False, local="comment")
    # comment_reply
    register_command("like", 1, should_run=False, local='comment_reply')
    register_command("unlike", 1, should_run=False, local='comment_reply')


def get_comment(avid: typing.Union[int, str], page=0, comment_type=1):
    if not isinstance(avid, int):
        avid = avid.strip()
    url = f"https://api.bilibili.com/x/v2/reply/main?mode=0&oid={avid}&next={page}&type={comment_type}&ps=5"
    r = get(url, headers=header, no_cache=True)
    return r.json()['data']['replies'], r.json()['data']['cursor']['all_count']


def comment_viewer(avid):
    _, total = get_comment(avid)
    page = 0
    while 1:
        comment, _ = get_comment(avid, page)
        for i, j in enumerate(comment):
            print(f"{i + 1}: ")
            print(f"作者: {j['member']['uname']} 点赞: {j['like']} 回复量: {j['rcount']}")
            print(f"内容: {j['content']['message']}")
        choose = input("评论选项: ")
        choose = choose.lstrip()
        choose = choose.rstrip()
        if choose == 'exit':
            return
        if not choose:
            page += 1
            continue
        command, argument = parse_text_command(choose, local="comment")
        if int(argument[0]) > len(comment) or int(argument[0]) <= 0:
            print("选视频超出范围!")
            continue
        rpid = comment[int(argument[0]) - 1]['rpid']
        if command == "like":
            comment_like(avid, rpid)
        elif command == "unlike":
            comment_like(avid, rpid, unlike=True)


def comment_like(avid, rpid, unlike=False, comment_type=1):
    data = {
        "type": comment_type,
        "oid": avid,
        "rpid": rpid,
        'csrf': csrf_token
    }
    if unlike:
        data['action'] = 1
    else:
        data['action'] = 1
    r = post("https://api.bilibili.com/x/v2/reply/action", headers=header, data=data)
    if r.json()['code'] == 0:
        print("点赞评论成功!")
    else:
        print("点赞评论失败!")
        print(r.json()['code'])
        print(r.json()['message'])


# def comment_reply_viewer(avid, rpid, type=1):
#     pass


def search():
    search_url = "http://api.bilibili.com/x/web-interface/search/type?keyword={}&search_type=video&page={}"
    try:
        search_thing = input("请输入搜索的东西: ")
    except KeyboardInterrupt:
        print("\n取消搜索.")
        return
    page = 1
    while 1:
        r = get(search_url.format(search_thing, page), headers=header)
        if not r.json()['data'].get("result"):
            print("到头了!")
            return
        flag1 = True
        result = r.json()['data']['result']
        for num, item in enumerate(result):
            print(num + 1, ":")
            print("封面: ", item['pic'])
            print("标题: ", item['title'].replace("<em class=\"keyword\">", "").replace("</em>", ""))
            print("作者: ", item['author'], " bvid: ", item['bvid'], " 日期: ", datetime.datetime.fromtimestamp(
                item['pubdate']).strftime("%Y-%m-%d %H:%M:%S"), " 观看量: ", item['play'])
        while flag1:
            command = input("搜索选项: ")
            if command == "exit":
                return
            if not command:
                break
            command, argument = parse_text_command(command, local="recommend")
            if not command:
                continue
            if not argument[0].isdecimal():
                print("输入的不是整数!")
                continue
            if int(argument[0]) > len(result) or int(argument[0]) <= 0:
                print("选视频超出范围!")
                continue
            bvid = result[int(argument[0]) - 1]['bvid']
            avid = result[int(argument[0]) - 1]['aid']
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
            elif command == "video_info":
                get_video_info(bvid, True)
            elif command == "favorite":
                media_id = list_fav(return_info=True)
                collection(media_id=media_id, avid=avid)
                print("收藏成功!")
            elif command == "view_collection":
                view_collection(bvid, True)
            elif command == "view_comment":
                comment_viewer(avid)
            elif command == 'coin':
                coin_count = int(input("请输入投币量(1-2): "))
                if coin_count != 1 and coin_count != 2:
                    print("输入错误!")
                coin(bvid, coin_count, bvid=True)
        page += 1


def get_video_info(video_id: str, bvid=True, easy=False):
    url = "http://api.bilibili.com/x/web-interface/view/detail"
    if bvid:
        url += "?bvid=" + video_id
    else:
        url += "?aid=" + video_id
    r = get(url, headers=header)
    video = r.json()['data']["View"]
    avid = video['aid']
    bvid = video['bvid']
    title = video['title']
    # author = r.json()['data']["Card"]
    status = video['stat']
    video = JSON(video)
    if easy:
        print("封面: ", video.pic)
        print("标题: ", video.title)
        print("作者: ", video.owner.name, " bvid: ", video.bvid, " 日期: ", datetime.datetime.fromtimestamp(
            video.pubdate).strftime("%Y-%m-%d %H:%M:%S"), " 视频时长:", format_long(video.duration), " 观看量: ",
              video.stat.view)
        return
    print('avid: ', avid)
    print("bvid: ", bvid)
    print("标题: ", title)
    print("视频时长: ", format_long(video['duration']))
    print("播放: ", status["view"])
    print("点赞: ", status['like'])
    print("投币: ", status["coin"])
    print("收藏: ", status["favorite"])
    print("转发: ", status["share"])
    print("弹幕: ", status["danmaku"])
    print("评论: ", status["reply"])
    print("avid: ", video["aid"])
    print("日期: ", datetime.datetime.fromtimestamp(
        video["pubdate"]).strftime("%Y-%m-%d %H:%M:%S"))
    print("简介: ")
    print("\n")
    print(video['desc'])
    print("\n")
    print("封面: ", video['pic'])
    print("作者: ", video['owner']['name'])
    print("mid: ", video['owner']['mid'])


def get_bvid(avid):
    url = "http://api.bilibili.com/x/web-interface/view/detail"
    url += "?aid=" + avid
    r = get(url, headers=header)
    return r.json()['data']['View']['bvid']


def get_aid(bvid):
    url = "http://api.bilibili.com/x/web-interface/view/detail"
    url += "?bvid=" + bvid
    r = get(url, headers=header)
    return r.json()['data']['View']['aid']


def address(video: str):
    video_processed = ""
    if "b23.tv" in video:
        video = get(video).url
    if video.startswith("http"):
        video_processed = video.split("/")[-1].split("?")[0]
        if not video_processed:
            video_processed = video.split("/")
            video_processed = video_processed[-2]
    video_processed = video_processed.strip()
    avid = ""
    bvid = video_processed
    is_bvid = True
    if video.isdecimal():
        is_bvid = False
        avid = video
        bvid = get_bvid(avid)
    print()
    get_video_info(video_processed, is_bvid, easy=True)

    while True:
        command = input("链接选项: ")
        if command == "exit":
            break
        if not command:
            continue
        command, argument = parse_text_command(command, local="address")
        if not command:
            continue
        if command == "play":
            play(bvid)
        elif command == "like":
            like(bvid)
        elif command == "triple":
            triple(bvid)
        elif command == 'unlike':
            like(bvid, unlike=True)
        elif command == "video_info":
            get_video_info(bvid, is_bvid)
        elif command == "view_collection":
            view_collection(bvid, is_bvid)
        elif command == "favorite":
            media_id = list_fav(return_info=True)
            collection(media_id=media_id, avid=avid)
            print("收藏成功!")
        elif command == "view_comment":
            comment_viewer(avid)
        elif command == 'coin':
            coin_count = int(input("请输入投币量(1-2): "))
            if coin_count != 1 and coin_count != 2:
                print("输入错误!")
            coin(bvid, coin_count, bvid=True)


def list_fav(return_info=False):
    fav_list = get(
        "https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid={mid}&jsonp=jsonp".format(mid=local_user_mid),
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
    total = ls.data.info.media_count // 5 + 1
    count = 1
    flag = True
    while flag:
        url = f"http://api.bilibili.com/x/v3/fav/resource/list?ps=5&media_id={media_id}&pn={count}"
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
            avid = ls[int(argument[0]) - 1]['id']
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
            elif command == "video_info":
                get_video_info(bvid, True)
            elif command == "view_collection":
                view_collection(bvid, True)
            elif command == "view_comment":
                comment_viewer(avid)
            elif command == 'coin':
                coin_count = int(input("请输入投币量(1-2): "))
                if coin_count != 1 and coin_count != 2:
                    print("输入错误!")
                coin(bvid, coin_count, bvid=True)
        count += 1


def bangumi():
    while True:
        choose_bangumi = input("番剧选项: ")
        if choose_bangumi == "address":
            url = input("输入地址: ")
            ssid_or_epid = url.split("/")[-1]
            ssid_or_epid = ssid_or_epid.split("?")[0]
            if ssid_or_epid.startswith("ss"):
                url = "http://api.bilibili.com/pgc/view/web/season?season_id=" + \
                      ssid_or_epid.strip("ss")
            else:
                url = "http://api.bilibili.com/pgc/view/web/season?ep_id=" + \
                      ssid_or_epid.strip('ep')
            bangumi_url = get(url, headers=header)
            bangumi_page = bangumi_url.json()['result']['episodes']
            for i, j in enumerate(bangumi_page):
                print(f"{i + 1}: {j['share_copy']} ({j['badge']})")
            print("请以冒号前面的数字为准选择视频.")
            while True:
                page = input("选择视频: ")
                if page == "exit":
                    break
                if not page:
                    continue
                if not page.isdigit():
                    continue
                if int(page) > len(bangumi_page) or int(page) <= 0:
                    print("选视频错误!")
                    continue
                cid = bangumi_page[int(page) - 1]['cid']
                epid = bangumi_page[int(page) - 1]['id']
                play_with_cid(epid, cid, bangumi=True)
        elif choose_bangumi == "exit":
            return


def view_collection(video_id, bvid=True):
    video_id = str(video_id)
    url = "http://api.bilibili.com/x/web-interface/view/detail"
    if not bvid:
        url += "?aid=" + video_id
    else:
        url += "?bvid=" + video_id
    r = get(url, headers=header)
    if not r.json()['data']['View'].get("ugc_season"):
        print("视频并没有合集!")
        return
    b_collection = r.json()['data']['View']['ugc_season']
    status = b_collection['stat']
    print("\n")
    print("标题", b_collection['title'])
    print("图片: ", b_collection['cover'])
    print("合集简介: ", b_collection['intro'])
    print("总播放: ", status["view"])
    print("总点赞: ", status['like'])
    print("总投币: ", status["coin"])
    print("总收藏: ", status["fav"])
    print("总转发: ", status["share"])
    print("总弹幕: ", status["danmaku"])
    print("总评论: ", status["reply"])
    print("\n")
    print("视频合集选集")
    b_collection_video = b_collection['sections'][0]['episodes']
    for i, j in enumerate(b_collection_video):
        print(f"{i + 1}: {j['title']}")
    print("请以冒号前面的数字为准选择视频.")
    while True:
        page = input("选择视频: ")
        if page == "exit":
            break
        if page.startswith("view_info"):
            page_ = page.strip("view_info").strip()
            if not page_.isdecimal():
                print("参数错误! ")
                continue
            get_video_info(b_collection_video[int(page_) - 1]['bvid'])
        if not page:
            continue
        if not page.isdigit():
            continue
        if int(page) > len(b_collection_video) or int(page) <= 0:
            print("选视频错误!")
            continue
        cid = b_collection_video[int(page) - 1]['cid']
        play_with_cid(b_collection_video[int(page) - 1]['bvid'], cid)
    return


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


def config():
    print("设置")
    print()
    print("1.清空本地缓存")
    print("2.清空内存缓存")
    print("3.调整分辨率")
    print("4.退出")
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
            return
        else:
            print("输入错误.")


def get_login_status():
    global is_login, local_user_mid
    r = get('https://api.bilibili.com/x/member/web/account',
            headers=header)
    a = JSON(r)
    if a.code == -101:
        print("账号尚未登录! ")
    elif a.code == 0:
        print("账号已登录.")
        print("欢迎" + a.data.uname + "回来.")
        local_user_mid = a.data.mid
        is_login = True
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
    global local_cookie
    if first_use:
        print("你是第一次使用LBCC, 是否配置cookie? (y/n)")
        print("Laosun Studios 保证用户数据是妥善存放在本地且不会被上传到除了B站以外的服务器.")
        choose = input()
        if choose.lower() == "y":
            cookie_or_file = input("请输入cookies或文件路径: ")
            if os.path.exists(cookie_or_file):
                with open(cookie_or_file) as f:
                    local_cookie = f.read()
            else:
                local_cookie = cookie_or_file
            username = check_login(local_cookie)
            if username:
                print("Cookie指定的用户为: ", username)
            else:
                print("Cookie未指定用户,取消配置.")
                return
            with open(f"users/{username}.txt", "w") as f:
                f.write(local_cookie)
            with open("cookie", "w"):
                pass
            print("Cookie配置成功! LBCC将会退出. ")
            input()
            sys.exit(0)


def add_cookie():
    cookie_or_file = input("请输入cookies或文件路径: ")
    if os.path.exists(cookie_or_file):
        with open(cookie_or_file) as f:
            cookie = f.read()
    else:
        cookie = cookie_or_file
    username = check_login(cookie)
    if username in os.listdir("users"):
        print("用户已经添加过!取消配置.")
        return
    if username:
        print("Cookie指定的用户为: ", username)
    else:
        print("Cookie未指定用户,取消配置.")
        return
    with open(f"users/{username}.txt", "w") as f:
        f.write(cookie)
    with open("cookie", "w"):
        pass
    print("Cookie配置成功! LBCC将会退出.")
    input()
    sys.exit(0)


def clean_memory_cache():
    global cached_response
    cached_response = {}


def clean_local_cache():
    shutil.rmtree("cached")
    os.mkdir('cached')


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
        username = check_login(cookie)
        if username:
            print(f"Cookie {username} 有效.")
        else:
            print(f"Cookie {i} 无效或已登出.")
            return


def main():
    while True:
        command = input("主选项: ")
        parse_command(command)


# def parse_experimental_features(feature_args):
#     if feature_args == "protobuf":
#         enable_protobuf_danmaku()
#         print("已启用特性: protobuf弹幕")
#     elif not feature_args:
#         return
#     else:
#         print("未知特性: ", feature_args)

print("LBCC v1.0.0-dev.")
print("Type \"help\" for more information.")

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description='LBCC命令行参数')
    # parser.add_argument("-ef", '--experimental-features', type=str, help="启用实验特性")
    # args = parser.parse_args()
    # parse_experimental_features(args.experimental_features)
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
