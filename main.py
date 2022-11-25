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

import base64
import datetime
import os
import sys
import threading
import time
import typing

import qrcode
import requests
import rsa

from bilibili.biliass import Danmaku2ASS


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


def safe_input(input_thing):
    try:
        return input(input_thing)
    except KeyboardInterrupt:
        sys.exit(0)


def encrypt_password(public_key, data):
    pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(public_key)
    return base64.urlsafe_b64encode(rsa.encrypt(data, pub_key))


def check_login(cookie):
    cached_header = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
        "referer": "https://www.bilibili.com", 'cookie': cookie}
    r = requests.get('https://api.bilibili.com/x/member/web/account',
                     headers=cached_header)
    if r.json()['code'] == -101:
        return False
    elif r.json()['code'] == 0:
        return r.json()['data']['uname']


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


def parse_text_command(command):
    return command.split(" ")[0], command.split(" ")[1:]


class BiliBili:
    # __init__
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
             "referer": "https://www.bilibili.com"})
        self.is_login: bool = False
        self.username: str = ""
        self.cached_response = {}
        self.user_mid: int = 0
        self.csrf_token: str = ""
        self.quality = {
            112: (1920, 1080, True),
            80: (1920, 1080, False),
            64: (1280, 720, False),
            32: (720, 480, False),
            16: (480, 360, False)
        }

        self.default_quality = 80

    # --------------------------user-------------------------
    def ask_cookie(self, first_use):
        if first_use:
            print("第一次使用LBCC, 是否配置用户? (y/n)")
            choose = input()
            if choose.lower() == "y":
                self.add_user()

    def add_user(self):
        print("添加用户")
        choose = safe_input("添加方式(cookie/login): ")
        if choose == "cookie":
            add_cookie()
        elif choose == "login":
            self.login()
        else:
            print("未知输入, 取消添加用户")

    def login(self):
        while True:
            choose = safe_input("选择登录方式(password/sms/qrcode): ")
            if choose == "password":
                username = safe_input("用户名: ")
                password = safe_input("密码: ")
                validate, seccode, token, challenge = self.verify_captcha_token()
                self.login_by_password(username, password, validate,
                                       seccode, token, challenge)
                break
            elif choose == "sms":
                self.login_by_sms()
                break
            elif choose == "qrcode":
                self.login_by_qrcode()
                break

    def login_by_sms(self):
        print("默认为中国手机号, 如果有异议请提出issues")
        tel = safe_input("请输入手机号: ")
        validate, seccode, token, challenge = self.verify_captcha_token()
        data = {"tel": tel, "cid": 86, "source": "main_web", "token": token,
                "challenge": challenge, "validate": validate, "seccode": seccode}
        r = self.post("https://passport.bilibili.com/x/passport-login/web/sms/send",
                      data=data)
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
        r_login = self.post("https://passport.bilibili.com/x/passport-login/web/login/sms",
                            data=data_login)
        if r_login.json()['code'] == 0:
            cookie = ""
            for i in r_login.cookies:
                cookie += i.name + "=" + i.value + ";"
            cookie = cookie[:-1]
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
        else:
            print("登录失败!")
            print(r_login.json()['code'])

    def login_by_password(self, username, password, validate, seccode, token, challenge):
        key_request = self.get(
            'https://passport.bilibili.com/login?act=getkey', no_cache=True)
        hash, public_key = key_request.json()['hash'], key_request.json()['key']
        password_hashed = hash + password
        password_encrypt = encrypt_password(
            public_key.encode(), password_hashed.encode())
        data = {"username": username, "password": password_encrypt.decode(
        ), "keep": 0, "challenge": challenge, "token": token, "validate": validate, "seccode": seccode}
        r = self.post("http://passport.bilibili.com/x/passport-login/web/login",
                      headers={}, data=data)
        if r.json()['code'] == 0:
            cookie = ""
            for i in r.cookies:
                cookie += i.name + "=" + i.value + ";"
            cookie = cookie[:-1]
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

    def login_by_qrcode(self):
        r = self.get("http://passport.bilibili.com/x/passport-login/web/qrcode/generate")
        url = r.json()['data']['url']
        qrcode_key = r.json()['data']['qrcode_key']
        image = qrcode.make(url)
        with open("cached/qrcode.jpg", "wb") as f:
            image.save(f)
        a = threading.Thread(target=os.system, args=("mpv cached/qrcode.jpg --loop",))
        a.start()
        while True:
            r = self.get("http://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key=" + qrcode_key,
                         no_cache=True)
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
        cookie = ""
        for i in r.cookies:
            cookie += i.name + "=" + i.value + ";"
        cookie = cookie[:-1]
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

    def verify_captcha_token(self):
        r = self.get("https://passport.bilibili.com/x/passport-login/captcha?source=main_web", no_cache=True)
        a = r.json()
        token = a['data']['token']
        print("gt: ", a['data']['geetest']['gt'],
              "challenge: ", a['data']['geetest']['challenge'])
        print("请到 https://kuresaru.github.io/geetest-validator/ 认证")
        validate = safe_input("validate: ")
        seccode = safe_input("seccode: ")
        return validate, seccode, token, a['data']['geetest']['challenge']

    def load_user(self):
        if os.path.exists("user"):
            with open("user") as f:
                self.username = f.read()
        elif len(os.listdir("users")) != 0:
            self.username = os.listdir("users")[0]
        else:
            pass
        with open(f"users/{self.username}") as f:
            cookie = f.read()
        cookie_is_valid = check_login(cookie)
        if not cookie_is_valid:
            print(f"用户{self.username}cookie已失效或已登出!")
            self.set_user()
        else:
            self.session.headers.update({'cookie': cookie})
        for i in cookie.split(";", maxsplit=1):
            key, value = i.strip().split("=", maxsplit=1)
            if key == "bili_jct":
                self.csrf_token = value
                break

    def set_user(self):
        ls = os.listdir("./users")
        print("选择用户")
        for i, j in enumerate(ls):
            print(f"{i + 1}: {j.split('.')[0]}")
        while True:
            choose = input("选项: ")
            choose = int(choose)
            if choose > len(ls) or choose <= 0:
                print("输入错误.")
            with open("user", "w") as f:
                f.write(ls[choose - 1].split(".")[0] + ".txt")
            print("切换用户成功. 检查可用性...")
            with open(f"users/{ls[choose - 1].split('.')[0]}.txt") as f:
                cookie = f.read()
            cookie_is_valid = check_login(cookie)
            if cookie_is_valid:
                return
            else:
                print(f"你选择的用户{self.username}cookie已失效或已登出! ")
                self.set_user()

    def get_login_status(self):
        r = self.get('https://api.bilibili.com/x/member/web/account', no_cache=True)
        if r.json()['code'] == -101:
            print("账号尚未登录!")
        elif r.json()['code'] == 0:
            print("账号已登录.")
            print("欢迎" + r.json()['data']['uname'] + "回来.")
            self.user_mid = r.json()['data']['mid']
            self.is_login = True

    # --------------------------user-------------------------

    # --------------------------utils-------------------------
    def get(self, url: str, params=None, no_cache=False, **kwargs) -> requests.Response:
        if self.cached_response.get(url):
            return self.cached_response.get(url)
        else:
            count = 3
            while True:
                try:
                    r = self.session.get(url, params=params, timeout=5, **kwargs)
                    break
                except requests.exceptions.RequestException as request_error:
                    print(f"{url}请求错误! 将会重试{count}次! ")
                    count -= 1
                    if count <= 0:
                        raise request_error
            if not no_cache:
                self.cached_response[url] = r
            return r

    def post(self, url: str, params=None, **kwargs) -> requests.Response:
        count = 3
        while True:
            try:
                r = self.session.post(url, params=params, timeout=5, **kwargs)
                break
            except requests.exceptions.RequestException as error:
                print(f"{url}请求错误! 将会重试{count}次!")
                count -= 1
                if count <= 0:
                    print("Request error!")
                    raise error
        return r

    # --------------------------utils-------------------------

    # --------------------------interface-------------------------

    def recommend(self):
        print("推荐界面")
        flag = True
        while flag:
            flag1 = True
            r = self.get("https://api.bilibili.com/x/web-interface/index/top/feed/rcmd?ps=5", no_cache=True)
            rcmd = r.json()['data']['item']
            for num, item in enumerate(rcmd):
                print(num + 1, ":")
                print("封面: ", item['pic'])
                print("标题: ", item['title'])
                print("作者: ", item['owner']['name'], " bvid: ", item['bvid'], " 日期: ", datetime.datetime.fromtimestamp(
                    item['pubdate']).strftime("%Y-%m-%d %H:%M:%S"), " 视频时长:", format_long(item['duration']), " 观看量: ",
                      item['stat']['view'])
            while flag1:
                command = safe_input("选择视频: ")
                if command == "exit":
                    return
                if not command:
                    break
                if not command.isdecimal():
                    print("输入的不是整数!")
                    continue
                if int(command) > len(rcmd) or int(command) <= 0:
                    print("选视频超出范围!")
                    continue
                bvid = rcmd[int(command) - 1]['bvid']
                avid = rcmd[int(command) - 1]['id']
                title = rcmd[int(command) - 1]['title']
                print(f"你选择了视频{command}.")
                self.view_video(avid, bvid, title)

    def view_video(self, avid, bvid, title, disable_favorite=False):
        while True:
            command = safe_input("视频选项: ")
            if not command:
                return
            command, argument = parse_text_command(command)
            if command == "play":
                self.play(bvid, title=title)
                break
            elif command == "like":
                self.like(bvid)
                break
            elif command == "triple":
                self.triple(bvid)
                break
            elif command == 'unlike':
                self.like(bvid, unlike=True)
                break
            if not disable_favorite:
                if command == "favorite":
                    media_id = self.list_fav(return_info=True)
                    self.collection(media_id=media_id, avid=avid)
                    print("收藏成功!")
                    break
            elif command == "video_info":
                self.get_video_info(bvid, True)
                break
            elif command == "view_collection":
                self.view_collection(bvid, True)
                break
            elif command == 'coin':
                coin_count = int(safe_input("请输入投币量(1-2): "))
                if coin_count != 1 and coin_count != 2:
                    print("输入错误!")
                self.coin(bvid, coin_count, bvid=True)
                break
            elif command == "view_comment":
                self.comment_viewer(avid)
                break
            else:
                print("未知命令!")

    def comment_like(self, avid, rpid, unlike=False, comment_type=1):
        data = {
            "type": comment_type,
            "oid": avid,
            "rpid": rpid,
            'csrf': self.csrf_token
        }
        if unlike:
            data['action'] = 1
        else:
            data['action'] = 1
        r = self.post("https://api.bilibili.com/x/v2/reply/action", data=data)
        if r.json()['code'] == 0:
            print("点赞评论成功!")
        else:
            print("点赞评论失败!")
            print(r.json()['code'])
            print(r.json()['message'])

    def get_comment(self, avid: typing.Union[int, str], page=0, comment_type=1):
        if not isinstance(avid, int):
            avid = avid.strip()
        url = f"https://api.bilibili.com/x/v2/reply/main?mode=0&oid={avid}&next={page}&type={comment_type}&ps=5"
        r = self.get(url, no_cache=True)
        return r.json()['data']['replies'], r.json()['data']['cursor']['all_count']

    def comment_viewer(self, avid):
        _, total = self.get_comment(avid)
        page = 0
        while 1:
            comment, _ = self.get_comment(avid, page)
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
            command, argument = parse_text_command(choose)
            if int(argument[0]) > len(comment) or int(argument[0]) <= 0:
                print("选视频超出范围!")
                continue
            rpid = comment[int(argument[0]) - 1]['rpid']
            if command == "like":
                self.comment_like(avid, rpid)
            elif command == "unlike":
                self.comment_like(avid, rpid, unlike=True)

    def list_fav(self, return_info=False):
        fav_list = self.get(
            "https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid={mid}&jsonp=jsonp".format(
                mid=self.user_mid))
        fav_list = fav_list.json()['data']['list']
        print("\n")
        print("选择收藏夹")
        print("\n")
        for i, j in enumerate(fav_list):
            print(f"{i + 1}: {j['title']}")
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
            a = fav_list[int(choose) - 1]['id']
            if not return_info:
                self.list_collection(a)
                break
            return a

    def list_collection(self, media_id):
        url = f"http://api.bilibili.com/x/v3/fav/resource/list?ps=20&media_id={media_id}"
        ls = self.get(url)
        total = ls.json()['data']['info']['media_count'] // 5 + 1
        count = 1
        flag = True
        while flag:
            url = f"http://api.bilibili.com/x/v3/fav/resource/list?ps=5&media_id={media_id}&pn={count}"
            ls = self.get(url)
            if total < count:
                print("到头了!")
                return
            ls = ls.json()['data']['medias']
            flag1 = True
            for num, item in enumerate(ls):
                print(num + 1, ":")
                print("封面: ", item['cover'])
                print("标题: ", item['title'])
                print("作者: ", item["upper"]["name"], " bvid: ", item['bvid'], " 日期: ",
                      datetime.datetime.fromtimestamp(
                          item['pubtime']).strftime("%Y-%m-%d %H:%M:%S"), " 视频时长:", format_long(item['duration']),
                      " 观看量: ",
                      item['cnt_info']['play'])
            while flag1:
                command = safe_input("选择视频: ")
                if command == "exit":
                    return
                if not command:
                    break
                if not command.isdecimal():
                    print("输入的不是整数!")
                    continue
                if int(command) > len(ls) or int(command) <= 0:
                    print("选视频超出范围!")
                    continue
                bvid = ls[int(command) - 1]['bvid']
                avid = ls[int(command) - 1]['id']
                title = ls[int(command) - 1]['title']
                print(f"你选择了视频{command}.")
                self.view_video(avid, bvid, title, disable_favorite=True)
            count += 1

    def view_collection(self, video_id, bvid=True):
        video_id = str(video_id)
        url = "http://api.bilibili.com/x/web-interface/view/detail"
        if not bvid:
            url += "?aid=" + video_id
        else:
            url += "?bvid=" + video_id
        r = self.get(url)
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
                self.get_video_info(b_collection_video[int(page_) - 1]['bvid'])
            if not page:
                continue
            if not page.isdigit():
                continue
            if int(page) > len(b_collection_video) or int(page) <= 0:
                print("选视频错误!")
                continue
            cid = b_collection_video[int(page) - 1]['cid']
            self.play_with_cid(b_collection_video[int(page) - 1]['bvid'], cid)
        return

    def get_video_info(self, video_id: str, bvid=True, easy=False):
        url = "http://api.bilibili.com/x/web-interface/view/detail"
        if bvid:
            url += "?bvid=" + video_id
        else:
            url += "?aid=" + video_id
        r = self.get(url)
        video = r.json()['data']["View"]
        avid = video['aid']
        bvid = video['bvid']
        title = video['title']
        # author = r.json()['data']["Card"]
        status = video['stat']
        if easy:
            print("封面: ", video['pic'])
            print("标题: ", video['title'])
            print("作者: ", video["owner"]["name"], " bvid: ", video['bvid'], " 日期: ", datetime.datetime.fromtimestamp(
                video['pubdate']).strftime("%Y-%m-%d %H:%M:%S"), " 视频时长:", format_long(video['duration']), " 观看量: ",
                  video['stat']['view'])
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

    # --------------------------interface-------------------------

    # --------------------------互动功能----------------------------
    def like(self, video_id, bvid=True, unlike=False):
        if not self.is_login:
            print("请先登录!")
        data = {'csrf': self.csrf_token}
        if bvid:
            data["bvid"] = video_id
        else:
            data["aid"] = video_id
        if not unlike:
            data['like'] = 1
        else:
            data['like'] = 2
        r = self.post("http://api.bilibili.com/x/web-interface/archive/like",
                      data=data)
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

    def coin(self, video_id, coin_count, bvid=True, like=False):
        if not self.is_login:
            print("请先登录!")
        data = {'csrf': self.csrf_token, 'multiply': coin_count}
        if bvid:
            data["bvid"] = video_id
        else:
            data["aid"] = video_id
        if like:
            data['select_like'] = 1
        r = self.post("http://api.bilibili.com/x/web-interface/coin/add",
                      data=data)
        code = r.json()['code']
        if code == 0:
            print("投币成功!")
        else:
            print("投币失败!")
            print(code)
            print(r.json()['message'])

    def triple(self, video_id: str, bvid=True):
        if not self.is_login:
            print("请先登录!")
        data = {'csrf': self.csrf_token}
        if bvid:
            data["bvid"] = video_id
        else:
            data["aid"] = video_id

        r = self.post("http://api.bilibili.com/x/web-interface/archive/like/triple", data=data)
        code = r.json()['code']
        if code == 0:
            print("三连成功!")
        else:
            print("三连失败!")
            print(code)
            print(r.json()['message'])

    def collection(self, avid: str, media_id: str):
        data = {"rid": avid, "type": 2, "add_media_ids": media_id, "csrf": self.csrf_token}
        r = self.post("http://api.bilibili.com/x/v3/fav/resource/deal", ata=data)
        code = r.json()['code']
        if code == 0:
            print("收藏成功!")
        else:
            print("收藏失败!")
            print(code)
            print(r.json()['message'])

    def play(self, video_id: str, bvid=True, title=""):
        print("\n")
        print("视频选集")
        if bvid:
            url = "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + video_id
        else:
            url = "https://api.bilibili.com/x/web-interface/view/detail?aid=" + video_id
        r = self.get(url)
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
            self.play_with_dash(video_id, cid, bvid, title)
            break
        return

    def play_with_cid(self, video_id: str, cid: int, bangumi=False, bvid=True, title="") -> None:
        if not bangumi:
            if bvid:
                url1 = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn={self.default_quality}&ty" \
                       f"pe=&otype=json&bvid={video_id}"
            else:
                url1 = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn={self.default_quality}&type=&oty" \
                       f"pe=json&avid={video_id}"
        else:
            url1 = f"https://api.bilibili.com/pgc/player/web/playurl" \
                   f"?qn={self.default_quality}&cid={cid}&ep_id={video_id}"
        req = self.get(url1, no_cache=True)
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
        width, height, is_higher = self.quality[higher]
        command = "mpv " \
                  "--sub-file=\"cached/{}.ass\" " \
                  "--user-agent=\"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) " \
                  "Gecko/20100101 Firefox/51.0\" " \
                  "--referrer=\"https://www.bilibili.com\" \"{}\" " \
                  "--title=\"{}\"".format(cid, flv_url, title)
        a = Danmaku2ASS(
            self.get_danmaku(cid),
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
            self.update_history(video_id, cid, round(time) + 1)
        a = threading.Thread(target=os.system, args=(command,))
        a.start()

    # --merge-files
    def play_with_dash(self, video_id: str, cid: int, bvid=True, title=""):
        if bvid:
            url1 = f"https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={video_id}&fnval=16&fourk=0"
        else:
            url1 = f"https://api.bilibili.com/x/player/playurl?cid={cid}&avid={video_id}&fnval=16&fourk=0"
        r = self.get(url1)
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
            video_url = video_mapping[self.default_quality][0]
        except KeyError:
            video_url = video_mapping[default_video][0]
        width, height, is_higher = self.quality[self.default_quality]
        a = Danmaku2ASS(
            self.get_danmaku(cid),
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
        command = f"mpv " \
                  f"--sub-file=\"cached/{cid}.ass\" " \
                  f"--user-agent=\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                  f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53\" " \
                  f"--referrer=\"https://www.bilibili.com\" \"{video_url}\" " \
                  f"--audio-file=\"{audio_url}\" " \
                  f"--title=\"{title}\""
        time = r.json()['data']["timelength"] / 1000
        self.update_history(video_id, cid, round(time) + 1)
        a = threading.Thread(target=os.system, args=(command,))
        a.start()

    def get_danmaku(self, cid):
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
        resp = self.get(url, headers=headers, params=params, no_cache=True)
        return resp.content

    def update_history(self, video_id, cid, progress, bvid=True):
        data = {"cid": cid, "played_time": progress}
        if bvid:
            data["bvid"] = video_id
        else:
            data["aid"] = video_id
        r = self.post("https://api.bilibili.com/x/click-interface/web/heartbeat", data=data)
        if r.json()['code'] != 0:
            print(data)
            print(r.json()['code'])
            print(r.json()['message'])

    # --------------------------互动功能----------------------------

    # main
    def main(self):
        first_use = init()
        self.ask_cookie(first_use)
        self.load_user()
        self.get_login_status()
        while True:
            command = safe_input("主选项: ")
            if command == "exit":
                sys.exit(0)
            elif command == "favorite":
                self.list_fav()
            elif command == "recommend":
                self.recommend()
            else:
                print("未知命令!")


print("LBCC v1.0.0-dev.")
print()

print("""Copyright (C) 2022 Laosun Studios.

This program comes with ABSOLUTELY NO WARRANTY; 
This is free software, and you are welcome to redistribute it
under certain conditions.""")

print("")

if __name__ == '__main__':
    bilibili = BiliBili()
    bilibili.main()
