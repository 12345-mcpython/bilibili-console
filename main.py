#!/usr/bin/env python3
"""
Copyright (c) 2022 Laosun Studios.

Distributed under GPL-3.0 License.

The product is developing. Effect currently
displayed is for reference only. Not indicative
of final product.

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
import datetime
import json
import os
import platform
import shutil
import sys
import threading
import time
import typing

import qrcode

from bilibili import init
from bilibili.biliass import Danmaku2ASS
from bilibili.command import parse_text_command, parse_command, register_command
from bilibili.users import check_login, get_available_user, fake_search_cookie, add_cookie, set_user
from bilibili.util_classes import JSON
from bilibili.utils import get, post, format_long, response_to_cookie, encrypt_password, cookie_to_dict

header = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77", "referer": "https://www.bilibili.com"}

cookie_mapping = {}

cached_response = {}

is_login = False

local_user_mid = None

quality = {
    112: (1920, 1080, True),
    80: (1920, 1080, False),
    64: (1280, 720, False),
    32: (720, 480, False),
    16: (480, 360, False)
}

default_quality = 80


def safe_input(input_thing):
    try:
        return input(input_thing)
    except KeyboardInterrupt:
        sys.exit(0)


def logout():
    if not is_login:
        print("请先登录!")
        return

    choose = safe_input("确认退出登录(y/n): ")
    if choose.lower() == "y":
        r = post("https://passport.bilibili.com/login/exit/v2",
                 headers=header, data={"biliCSRF": csrf_token})
        try:
            if r.json()['code'] == 0:
                os.remove(f"users/{username}.txt")
                print("登出成功! LBCC将退出.")
                safe_input()
                sys.exit(0)
        except json.decoder.JSONDecodeError:
            print("登出失败!")


def login():
    while True:
        choose = safe_input("选择登录方式(password/sms/qrcode): ")
        if choose == "password":
            username = safe_input("用户名: ")
            password = safe_input("密码: ")
            validate, seccode, token, challenge = verify_captcha_token()
            login_by_password(username, password, validate,
                              seccode, token, challenge)
            break
        elif choose == "sms":
            login_by_sms()
            break
        elif choose == "qrcode":
            login_by_qrcode()
            break


def login_by_sms():
    print("默认为中国手机号, 如果有异议请提出issues")
    tel = safe_input("请输入手机号: ")
    validate, seccode, token, challenge = verify_captcha_token()
    data = {"tel": tel, "cid": 86, "source": "main_web", "token": token,
            "challenge": challenge, "validate": validate, "seccode": seccode}
    r = post("https://passport.bilibili.com/x/passport-login/web/sms/send",
             data=data, headers=header)
    if r.json()['code'] == 0:
        captcha_key = r.json()['data']['captcha_key']
        print("发送成功!")
    else:
        print("发送失败!")
        print(r.json()['code'])
        print(r.json()['message'])
        return
    code = safe_input("请输入短信认证码: ")
    data_login = {"code": code, "tel": tel, "cid": 86,
                  "source": "main_web", "captcha_key": captcha_key}
    r_login = post("https://passport.bilibili.com/x/passport-login/web/login/sms",
                   headers=header, data=data_login)
    if r_login.json()['code'] == 0:
        cookie = response_to_cookie(r_login)
        username_local = check_login(cookie)
        print(f"用户{username_local}登录成功!")
        choose = safe_input("确认添加用户(y/n): ")
        if choose.lower() == "y":
            if username_local in os.listdir("users"):
                print("用户已经添加过!取消添加.")
                return
            with open(f"users/{username_local}.txt", "w") as f:
                f.write(cookie)
            print("添加成功! LBCC将退出.")
            safe_input()
            sys.exit(0)
        else:
            print("取消添加.")
            print("Cookie: ")
            print(cookie)
            return

    else:
        print("登录失败!")
        print(r_login.json()['code'])


def login_by_password(username, password, validate, seccode, token, challenge):
    key_request = get(
        'https://passport.bilibili.com/login?act=getkey', headers=header, no_cache=True)
    hash, public_key = key_request.json()['hash'], key_request.json()['key']
    password_hashed = hash + password
    password_encrypt = encrypt_password(
        public_key.encode(), password_hashed.encode())
    data = {"username": username, "password": password_encrypt.decode(
    ), "keep": 0, "challenge": challenge, "token": token, "validate": validate, "seccode": seccode}
    r = post("http://passport.bilibili.com/x/passport-login/web/login",
             headers={}, data=data)
    if r.json()['code'] == 0:
        cookie = response_to_cookie(r)
        print(cookie)
        username_local = check_login(cookie)
        print(f"用户{username_local}登录成功!")
        choose = safe_input("确认添加用户(y/n): ")
        if choose.lower() == "y":
            if username_local in os.listdir("users"):
                print("用户已经添加过!取消添加.")
                return
            with open(f"users/{username_local}.txt", "w") as f:
                f.write(cookie)
            print("添加成功! LBCC将退出.")
            safe_input()
            sys.exit(0)
    else:
        print("登录失败!")
        print(r.json()['code'])
        print(r.json()['message'])


def login_by_qrcode():
    r = get("http://passport.bilibili.com/x/passport-login/web/qrcode/generate", headers=header)
    url = r.json()['data']['url']
    qrcode_key = r.json()['data']['qrcode_key']
    image = qrcode.make(url)
    with open("cached/qrcode.jpg", "wb") as f:
        image.save(f)
    a = threading.Thread(target=os.system, args=("mpv cached/qrcode.jpg --loop",))
    a.start()
    while True:
        r = get("http://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key=" + qrcode_key)
        code = r.json()['data']['code']
        if code == 86101:
            print("未扫码. 等待5秒...")
            time.sleep(5)
            continue
        elif code == 86090:
            print("扫码成功! 手机端请确认! 等待2秒...")
            time.sleep(2)
        elif code == 0:
            print("手机端已确认! 登录完毕!")
            break
    cookie = response_to_cookie(r)
    username_local = check_login(cookie)
    print(f"用户{username_local}登录成功!")
    choose = safe_input("确认添加用户(y/n): ")
    if choose.lower() == "y":
        if username_local in os.listdir("users"):
            print("用户已经添加过!取消添加.")
            return
        with open(f"users/{username_local}.txt", "w") as f:
            f.write(cookie)
        print("添加成功! LBCC将退出.")
        safe_input()
        sys.exit(0)


def verify_captcha_token():
    r = get("https://passport.bilibili.com/x/passport-login/captcha?source=main_web",
            headers=header, no_cache=True)
    a = r.json()
    token = a['data']['token']
    print("gt: ", a['data']['geetest']['gt'],
          "challenge: ", a['data']['geetest']['challenge'])
    print("请到 https://kuresaru.github.io/geetest-validator/ 认证")
    validate = safe_input("validate: ")
    seccode = safe_input("seccode: ")
    return validate, seccode, token, a['data']['geetest']['challenge']


# 界面


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


def play(video_id: str, bvid=True, title=""):
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
        page = safe_input("选择视频: ")
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
        play_with_dash(video_id, cid, bvid, title)
        break
    return


def play_with_cid(video_id: str, cid: int, bangumi=False, bvid=True, title="") -> None:
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
              "--referrer=\"https://www.bilibili.com\" \"{}\" --title=\"{}\"".format(cid, flv_url, title)
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
    if not bangumi:
        time = req.json()['data']["timelength"] / 1000
        update_history(video_id, cid, round(time) + 1)
    a = threading.Thread(target=os.system, args=(command,))
    a.start()


# --merge-files
def play_with_dash(video_id: str, cid: int, bvid=True, title=""):
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
              f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53\" -" \
              f"-referrer=\"https://www.bilibili.com\" \"{video_url}\" --audio-file=\"{audio_url}\" --title=\"{title}\""
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
    resp = get(url, headers=headers, params=params, no_cache=True)
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
            command = safe_input("推荐选项: ")
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
                play(bvid, title=rcmd[int(argument[0]) - 1]['title'])
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
                coin_count = int(safe_input("请输入投币量(1-2): "))
                if coin_count != 1 and coin_count != 2:
                    print("输入错误!")
                coin(bvid, coin_count, bvid=True)
            elif command == "view_comment":
                comment_viewer(avid)


def add_user():
    print("添加用户")
    choose = safe_input("添加方式(cookie/login): ")
    if choose == "cookie":
        add_cookie()
    elif choose == "login":
        login()
    else:
        print("未知输入, 取消添加用户")


def user_manager():
    print("用户管理")
    print()
    print(f"当前用户为{username}, mid: {local_user_mid}")
    print("1.添加用户")
    print("2.登出当前用户")
    print("3.切换用户")
    choose = safe_input("选项: ")
    if choose == "1":
        add_user()
    elif choose == '2':
        logout()
    elif choose == "3":
        set_user()
    else:
        print("未知输入, 用户管理已退出")


def register_all_command():
    register_command("recommend", 0, run=recommend)
    register_command("exit", 0, run=sys.exit)
    register_command("address", 1, run=address)
    register_command("favorite", 0, run=list_fav)
    register_command("search", 0, run=search)
    register_command("bangumi", 0, run=bangumi)
    register_command("config", 0, run=config)
    register_command("manage_user", 0, run=user_manager)
    register_command("precious", 0, run=precious)
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
        choose = safe_input("评论选项: ")
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


def search():
    search_url = "http://api.bilibili.com/x/web-interface/search/type?keyword={}&search_type=video&page={}"
    try:
        search_thing = safe_input("请输入搜索的东西: ")
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
            command = safe_input("搜索选项: ")
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
                play(bvid, title=result[int(argument[0]) - 1]['title'])
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
                coin_count = int(safe_input("请输入投币量(1-2): "))
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
        return video.title
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
    video_processed = video
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
    title = get_video_info(video_processed, is_bvid, easy=True)

    while True:
        command = safe_input("链接选项: ")
        if command == "exit":
            break
        if not command:
            continue
        command, argument = parse_text_command(command, local="address")
        if not command:
            continue
        if command == "play":
            play(bvid, title=title)
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
        elif command == "collection":
            media_id = list_fav(return_info=True)
            collection(media_id=media_id, avid=avid)
            print("收藏成功!")
        elif command == "view_comment":
            comment_viewer(avid)
        elif command == 'coin':
            coin_count = int(safe_input("请输入投币量(1-2): "))
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
        choose = safe_input("选择收藏夹: ")
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
            command = safe_input("收藏选项: ")
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
                play(bvid, title=ls[int(argument[0]) - 1]['title'])
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
                coin_count = int(safe_input("请输入投币量(1-2): "))
                if coin_count != 1 and coin_count != 2:
                    print("输入错误!")
                coin(bvid, coin_count, bvid=True)
        count += 1


def bangumi():
    while True:
        choose_bangumi = safe_input("番剧选项: ")
        if choose_bangumi == "address":
            url = safe_input("输入地址: ")
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
                page = safe_input("选择视频: ")
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


def precious():
    url = "https://api.bilibili.com/x/web-interface/popular/precious?page_size=100&page=1"
    r = get(url, headers=header)
    precious_list = r.json()['data']['list']
    for i, j in enumerate(precious_list):
        print(f"{i + 1}: ")
        print(f"标题: {j['title']} 作者: {j['owner']['name']}")
        print(f"成就: {j['achievement']}")
        print(f"bvid: {j['bvid']} aid: {j['aid']}")
    while True:
        command = safe_input("入站必刷选项: ")
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
        if int(argument[0]) > len(precious_list) or int(argument[0]) <= 0:
            print("选视频超出范围!")
            continue
        bvid = precious_list[int(argument[0]) - 1]['bvid']
        avid = precious_list[int(argument[0]) - 1]['aid']
        if command == "play":
            play(bvid, title=precious_list[int(argument[0]) - 1]['title'])
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
            coin_count = int(safe_input("请输入投币量(1-2): "))
            if coin_count != 1 and coin_count != 2:
                print("输入错误!")
            coin(bvid, coin_count, bvid=True)
        elif command == "favorite":
            media_id = list_fav(return_info=True)
            collection(media_id=media_id, avid=precious_list[int(argument[0]) - 1]['id'])
            print("收藏成功!")


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
        page = safe_input("选择视频: ")
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


def config():
    print("设置")
    print()
    print("1.清空本地缓存")
    print("2.清空内存缓存")
    print("3.调整分辨率")
    print("4.退出")
    while True:
        choose = int(safe_input("设置: "))
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
            headers=header, no_cache=True)
    a = JSON(r)
    if a.code == -101:
        print("账号尚未登录! ")
    elif a.code == 0:
        print("账号已登录.")
        print("欢迎" + a.data.uname + "回来.")
        local_user_mid = a.data.mid
        is_login = True
        return True


def clean_memory_cache():
    global cached_response
    cached_response = {}


def clean_local_cache():
    shutil.rmtree("cached")
    os.mkdir('cached')


def set_quality():
    global default_quality
    for i, j in enumerate(quality.items()):
        print(f"{i}: {j[1][0]}x{j[1][1]} " + ("高码率" if j[1][2] else ""))
    while True:
        try:
            quality_choose = int(safe_input("选择分辨率: "))
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


def main():
    while True:
        command = safe_input("主选项: ")
        parse_command(command)


def check_environment():
    if platform.system() == "Windows" and not os.path.exists("mpv.exe"):
        print("mpv正在配置...")
        with open("mpv.exe", "wb") as f:
            f.write(get("https://programming-file.obs.cn-north-4.myhuaweicloud.com/mpv.exe").content)
        print("mpv配置完成.")
        return
    elif platform.system() == "Linux" and os.path.exists("/etc/debian_version"):
        print("mpv正在配置...")
        prefix = "sudo " if shutil.which("sudo") else ""
        os.system(f"{prefix}apt install mpv")
        print("mpv配置完成.")
        return
    if os.path.exists("mpv.exe"):
        return
    print("所在平台可能并不支持mpv, 请到https://mpv.io/installation/下载.")


def ask_cookie(first_use):
    if first_use:
        print("第一次使用LBCC, 是否配置用户? (y/n)")
        choose = input()
        if choose.lower() == "y":
            add_user()
    check_environment()


print("LBCC v1.0.0-dev.")
print()

print("""Copyright (C) 2022 Laosun Studios.

This program comes with ABSOLUTELY NO WARRANTY; 
This is free software, and you are welcome to redistribute it
under certain conditions.""")

print("")

if __name__ == "__main__":
    first_use = init()
    ask_cookie(first_use)
    username_file = get_available_user()
    username = ""
    if not username_file:
        header["cookie"] = fake_search_cookie()
    else:
        username = username_file.split(".")[0]
        with open(f"users/{username}.txt") as f:
            header["cookie"] = f.read()
    get_login_status()
    register_all_command()
    cookie_mapping = cookie_to_dict(header["cookie"])
    csrf_token = cookie_mapping.get("bili_jct")
    main()
