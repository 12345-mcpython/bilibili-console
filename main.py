#!/usr/bin/env python3
"""
Copyright (c) 2025 Laosun Studios.

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
import getpass
import json
import os
import reprlib
import shutil
import subprocess
import sys
import time
import traceback
from typing import Generator, List

import requests
import rsa
from google.protobuf.json_format import MessageToJson
from tqdm import tqdm

from bilibili.protobuf.dm_pb2 import DmSegMobileReply
# from bilibili.biliass.protobuf.danmaku_pb2 import DmSegMobileReply
from bilibili.utils import (
    av2bv,
    bv2av,
    format_time,
    validate_title,
    encrypt_wbi,
    user_manager,
    hum_convert,
    get_danmaku,
    remove, parse_view, danmaku_provider,
)

__version__ = "1.0.0-dev"

__year__ = 2025

__author__ = "Laosun Studios"

saw = False

quality_mapping = {6: "240P 极速", 16: "360P 流畅", 32: "480P 清晰", 64: "720P 高清", 74: "720P60 高帧率",
                   80: "1080P 高清", 112: "1080P+ 高码率", 116: "1080P60 高帧率", 120: "4K 超清"}


def view_short_video_info(bvid):
    video = user_manager.get(
        "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + bvid
    )
    item = video.json()["data"]["View"]
    print("封面: ", item["pic"])
    print("标题: ", item["title"])
    print(
        "作者: ",
        item["owner"]["name"],
        " bvid: ",
        item["bvid"],
        " 日期: ",
        datetime.datetime.fromtimestamp(
            item["pubdate"]).strftime("%Y-%m-%d %H:%M:%S"),
        " 视频时长:",
        format_time(item["duration"]),
        " 观看量: ",
        item["stat"]["view"],
    )


def show_help():
    print(
        """帮助菜单：
recommend/r: 推荐
login/l: 登录
logout/lo: 登出
address/a: 按地址播放
bangumi/b: 按地址播放番剧
favorite/f: 查看收藏夹
search/s: 搜索
quit/q: 退出
enable_online_watching: 开启在线观看
disable_online_watching: 关闭在线观看
clean_cache: 清除缓存
refresh_login_state: 刷新登录状态
export_favorite: 导出收藏夹
export_all_favorite: 导出所有收藏夹
download_favorite: 下载收藏夹视频
history: 查看历史记录
view_self: 查看自己的空间
view_user: 查看用户空间
    """
    )


class BilibiliLogin:
    temp_header = {
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) "
                      "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
        "Referer": "https://www.bilibili.com",
    }

    temp_login_header = temp_header.copy()

    @staticmethod
    def generate_cookie():
        r = requests.get("https://www.bilibili.com",
                         headers=BilibiliLogin.temp_header)
        cookie = ""
        for i, j in r.cookies.items():
            cookie += f"{i}={j}; "
        BilibiliLogin.temp_login_header["Cookie"] = cookie[:-2]

    @staticmethod
    def logout():
        r = user_manager.post(
            "https://passport.bilibili.com/login/exit/v2", data={"biliCSRF": user_manager.csrf})
        rsp_json = r.json()
        if rsp_json["code"] == 0:
            print("退出登录成功.")
            with open("cookie.txt", "w") as f:
                f.write("")
            user_manager.refresh_login()

    @staticmethod
    def login_by_password(username: str, password: str):
        token, challenge, validate = BilibiliLogin.generate_captcha()
        hash_, key = BilibiliLogin.get_key()
        pk = rsa.PublicKey.load_pkcs1_openssl_pem(key.encode())
        password_hash = rsa.encrypt((hash_ + password).encode(), pk)
        password_base64 = base64.b64encode(password_hash)
        data = {"username": username, "password": password_base64, "keep": 0, "token": token, "challenge": challenge,
                "validate": validate, "seccode": validate + "|jordan"}
        r = requests.post("https://passport.bilibili.com/x/passport-login/web/login", data=data,
                          headers=BilibiliLogin.temp_login_header)
        if r.json()["code"] != 0 or r.json()["data"]["message"].startswith("本次登录"):
            print("登录失败!")
            print(r.json()["message"])
            print(r.json()["data"]["message"])
            return False
        cookie = ""
        for i, j in r.cookies.items():
            cookie += f"{i}={j}; "
        return cookie[:-2] + "; " + BilibiliLogin.temp_login_header["Cookie"]

    @staticmethod
    def send_sms(phone_number: str) -> str | bool:
        token, challenge, validate = BilibiliLogin.generate_captcha()
        data = {"cid": 86, "tel": phone_number, "challenge": challenge, "seccode": validate + "|jordan",
                "validate": validate, "token": token,
                "source": "main-fe-header"}
        r = requests.post("https://passport.bilibili.com/x/passport-login/web/sms/send", data=data,
                          headers=BilibiliLogin.temp_login_header)
        if r.json()["code"] != 0:
            print("发送短信认证码失败! ")
            print(r.json()["code"])
            print(r.json()["message"])
            return False
        return r.json()["data"]["captcha_key"]

    @staticmethod
    def login_by_sms(phone_number: str, captcha_key: str, sms_code: str) -> str | bool:
        data = {"cid": 86, "tel": phone_number, "captcha_key": captcha_key, "code": sms_code, "keep": True,
                "source": "main_mini"}
        r = requests.post("https://passport.bilibili.com/x/passport-login/web/login/sms", data=data,
                          headers=BilibiliLogin.temp_login_header)
        if r.json()["code"] != 0:
            print("登录失败! ")
            print(r.json()["message"])
            return False
        cookie = ""
        for i, j in r.cookies.items():
            cookie += f"{i}={j}; "
        return cookie[:-2] + "; " + BilibiliLogin.temp_login_header["Cookie"]

    @staticmethod
    def generate_captcha():
        r = requests.get("https://passport.bilibili.com/x/passport-login/captcha",
                         headers=BilibiliLogin.temp_login_header)
        data = r.json()
        challenge = data["data"]["geetest"]["challenge"]
        gt = data["data"]["geetest"]["gt"]
        print("gt: ", gt, "challenge: ", challenge)
        print("请到 https://kuresaru.github.io/geetest-validator/ 进行认证.")
        while True:
            validate = input("请输入得到的 validate: ")
            if len(validate.strip()) != 32:
                print("validate 长度错误! ")
                continue
            break
        return data["data"]["token"], challenge, validate

    @staticmethod
    def get_key() -> tuple[str, str]:
        r = requests.get("https://passport.bilibili.com/x/passport-login/web/key",
                         headers=BilibiliLogin.temp_login_header)
        return r.json()["data"]["hash"], r.json()["data"]["key"]


# https://github.com/SocialSisterYi/bilibili-API-collect/issues/1168
#
# class BilibiliManga:
#     @staticmethod
#     def get_manga_detail(manga_id: int) -> dict:
#         detail_request = user_manager.post(
#             "https://manga.bilibili.com/twirp/comic.v1.Comic/ComicDetail?device=pc&platform=web",
#             data={"comic_id": manga_id},
#         )
#         return detail_request.json()
#
#     @staticmethod
#     def list_history() -> dict:
#         history = user_manager.post(
#             "https://manga.bilibili.com/twirp/bookshelf.v1.Bookshelf/ListHistory?device=pc&platform=web",
#             data={"page_num": 1, "page_size": 50},
#         )
#         return history.json()
#
#     @staticmethod
#     def get_image_list(epid) -> dict:
#         images = user_manager.post(
#             "https://manga.bilibili.com/twirp/comic.v1.Comic/GetImageIndex?device=pc&platform=web",
#             data={"ep_id": epid},
#         )
#         return images.json()
#
#     @staticmethod
#     def get_token(image: str) -> dict:
#         token = user_manager.post(
#             "https://manga.bilibili.com/twirp/comic.v1.Comic/ImageToken?device=pc&platform=web",
#             data={"urls": '["{}"]'.format(image)},
#         )
#         return token.json()
#
#     @classmethod
#     def download_manga(cls, manga_id: int) -> bool:
#         manga_info = cls.get_manga_detail(manga_id)
#         ep_info = manga_info["data"]["ep_list"]
#         name = manga_info["data"]["title"]
#         if not os.path.exists("download/manga"):
#             os.mkdir("download/manga")
#         if not os.path.exists("download/manga/" + validate_title(name)):
#             os.mkdir("download/manga/" + validate_title(name))
#         first, end = input("选择回目范围 (1-{}): ".format(len(ep_info))).split("-")
#         try:
#             # first, end str值如果不可转换为 int 会直接跳出函数, 故对其忽略类型检查
#             first = int(first)  # type: ignore
#             end = int(end)  # type: ignore
#         except ValueError:
#             print("输入回目范围错误!")
#             return False
#         download_manga_epid = []
#         download_manga_name = []
#         locked = 0
#         for i in list(reversed(ep_info)):
#             if first <= i["ord"] <= end:
#                 if i["is_locked"]:
#                     locked += 1
#                     continue
#                 download_manga_epid.append(i["id"])
#                 download_manga_name.append(i["title"])
#         print(f"有{locked}篇被上锁, 需要购买" if locked else "")
#         download_image = {}
#         cursor = 0
#         picture_count = 0
#         print("获取图片信息中.")
#         # 忽略原因同上
#         with tqdm(total=end) as progress_bar:  # type: ignore
#             for i in download_manga_epid:
#                 download_image_prefix = []
#                 image_list = cls.get_image_list(i)
#                 for j in image_list["data"]["images"]:
#                     download_image_prefix.append(j["path"])
#                     picture_count += 1
#                 download_image[download_manga_name[cursor]
#                 ] = download_image_prefix
#                 progress_bar.update(1)
#                 cursor += 1
#         download_image_url = {}
#         print("获取图片token中.")
#         with tqdm(total=picture_count) as progress_bar:
#             for i, j in download_image.items():
#                 download_image_url_local = []
#                 for k in j:
#                     token = cls.get_token(k)["data"][0]
#                     download_image_url_local.append(
#                         "{}?token={}".format(token["url"], token["token"])
#                     )
#                     progress_bar.update(1)
#                 download_image_url[i] = download_image_url_local
#         print("下载图片中.")
#         byte = 0
#         with tqdm(total=picture_count) as progress_bar:
#             for i, j in download_image_url.items():
#                 filename = 0
#                 for k in j:
#                     path = (
#                             "download/manga/"
#                             + validate_title(name)
#                             + "/"
#                             + validate_title(i)
#                             + "/"
#                     )
#                     file = path + f"{filename}.jpg"
#                     if not os.path.exists(path):
#                         os.mkdir(path)
#                     with open(file, "wb") as f:
#                         byte += f.write(user_manager.get(k).content)
#                         progress_bar.update(1)
#                         filename += 1
#         print("下载完成. 总计下载了 {} 字节 ({})".format(byte, hum_convert(byte)))
#         return True


class BilibiliUserSpace:
    @staticmethod
    def get_following_list(mid: int):
        following_list = []
        pre_page = 20
        r = user_manager.get(
            f"https://api.bilibili.com/x/relation/fans?vmid={mid}&pn=1&ps={pre_page}"
        )
        total = r.json()["data"]["total"]
        for i in range(1, total // pre_page + 2):
            if i == 5:
                break
            r = user_manager.get(
                f"https://api.bilibili.com/x/relation/fans?vmid={mid}&pn={i}&ps={pre_page}"
            )
            following_list += r.json()["data"]["list"]
        return following_list

    @staticmethod
    def get_followed_list(mid: int):
        followed_list = []
        pre_page = 20
        r = user_manager.get(
            f"https://api.bilibili.com/x/relation/followings?vmid={mid}&pn=1&ps={pre_page}"
        )
        total = r.json()["data"]["total"]
        for i in range(1, total // pre_page + 2):
            if i == 5:
                break
            r = user_manager.get(
                f"https://api.bilibili.com/x/relation/followings?vmid={mid}&pn={i}&ps={pre_page}"
            )
            followed_list += r.json()["data"]["list"]
        return followed_list

    # follow_type 1 关注 2 取关
    @staticmethod
    def modify_relation(mid: int, modify_type: int = 1):
        data = {"fid": mid, "act": modify_type, "csrf": user_manager.csrf}
        r = user_manager.post(
            "https://api.bilibili.com/x/relation/modify", data=data)
        if r.json()["code"] == 0:
            print("更改用户关系成功.")
        else:
            print("更改用户关系失败!")
            print(r.json()["message"])

    @staticmethod
    def get_user_data(mid: int):
        user_info = user_manager.get(
            "https://api.bilibili.com/x/space/wbi/acc/info?"
            + encrypt_wbi("mid=" + str(mid))
        )
        return user_info.json()["data"]

    @staticmethod
    def get_user_video(mid: int):
        pre_page = 5
        cursor = 1
        request = user_manager.get(
            "https://api.bilibili.com/x/space/wbi/arc/search?"
            + encrypt_wbi(f"mid={mid}&ps={pre_page}"),
            cache=True,
        )
        total = request.json()["data"]["page"]["count"] // pre_page + 1
        while True:
            ls = user_manager.get(
                "https://api.bilibili.com/x/space/wbi/arc/search?"
                + encrypt_wbi(f"mid={mid}&ps={pre_page}&pn={cursor}"),
                cache=True,
            )
            if total < cursor:
                break
            yield ls.json()["data"]["list"]["vlist"]
            cursor += 1


class BilibiliBangumi:
    def __init__(self, quality: int):
        self.quality = quality

    @staticmethod
    def get_follow_bangumi(mid) -> list:
        r = user_manager.get(
            f"https://api.bilibili.com/x/space/bangumi/follow/list?type=1&follow_status=0&pn=1&ps=15"
            + f"&vmid={mid}",
            cache=True,
        )
        if r.json()["code"] != 0:
            raise Exception(r.json()["message"])
        datas = []
        for i in r.json()["data"]["list"]:
            datas.append(
                {
                    "watch_progress": i["progress"],
                    "img": i["cover"],
                    "title": i["title"],
                    "bangumi_type": i["season_type_name"],
                    "areas": i["areas"][0]["name"],
                    "update_progress": i["new_ep"]["index_show"],
                }
            )
        return datas

    @staticmethod
    def get_self_follow_bangumi():
        return BilibiliBangumi.get_follow_bangumi(user_manager.mid)

    @staticmethod
    def follow_bangumi(season_id):
        data = {"season_id": season_id, "csrf": user_manager.csrf}
        r = user_manager.post(
            "https://api.bilibili.com/pgc/web/follow/add", data=data)
        if r.json()["code"] == 0:
            print("追番成功.")
        else:
            print("追番失败!")
            print(f"失败信息: {r.json()['message']}")

    @staticmethod
    def cancel_follow_bangumi(season_id):
        data = {"season_id": season_id, "csrf": user_manager.csrf}
        r = user_manager.post(
            "https://api.bilibili.com/pgc/web/follow/del", data=data)
        if r.json()["code"] == 0:
            print("取消追番成功.")
        else:
            print("取消追番失败!")
            print(f"失败信息: {r.json()['message']}")

    def select_bangumi(self, ssid="", epid=""):
        if not any([ssid, epid]):
            return
        if ssid:
            url = "https://api.bilibili.com/pgc/view/web/season?season_id=" + ssid
        else:
            url = "https://api.bilibili.com/pgc/view/web/season?ep_id=" + epid
        bangumi_url = user_manager.get(url)
        bangumi_page = bangumi_url.json()["result"]["episodes"]
        for i, j in enumerate(bangumi_page):
            print(f"{i + 1}: {j['share_copy']} ({j['badge']})")
        print("请以冒号前面的数字为准选择视频.")
        while True:
            page = input("选择视频: ")
            if page == "quit" or page == "q":
                break
            if not page:
                continue
            if not page.isdigit():
                continue
            if int(page) > len(bangumi_page) or int(page) <= 0:
                print("选视频错误!")
                continue
            cid = bangumi_page[int(page) - 1]["cid"]
            bvid = bangumi_page[int(page) - 1]["bvid"]
            epid = bangumi_page[int(page) - 1]["id"]
            title = bangumi_page[int(page) - 1]["share_copy"]
            video = BilibiliVideo(
                bvid=bvid, epid=epid, bangumi=True, quality=self.quality
            )
            video.play(cid, title=title)


# search_type

# article 专栏
# video 视频
# bili_user 用户
# live 直播
# media_ft 影视
# media_bangumi 番剧

# order
# click 播放量
# pubdate 最新
# dm 弹幕
# stow 收藏
# 空 综合


class BilibiliSearch:
    @staticmethod
    def search(keyword, search_type="video", order=""):
        """
        搜索
        :param keyword: 搜索关键词
        :param search_type: 搜索类型 article 专栏 video 视频 bili_user 用户 live 直播 media_ft 影视 media_bangumi 番剧
        :param order: 搜索排序 click 播放量 pubdate 最新 dm 弹幕 stow 收藏 空 综合
        :return: 搜索结果
        """
        pre_page = 5
        cursor = 1
        while True:
            ls = user_manager.get(
                f"https://api.bilibili.com/x/web-interface/wbi/search/type?page={cursor}"
                f"&page_size={pre_page}&keyword={keyword}&search_type={search_type}"
                + (f"&order={order}" if order else ""),
                cache=True,
            )
            if len(ls.json()["data"]["result"]) == 0:
                break
            result = ls.json()["data"]["result"]
            for i in result:
                i["title"] = remove(i["title"], '<em class="keyword">')
                i["title"] = remove(i["title"], "</em>")
            yield result
            cursor += 1


class BilibiliHistory:
    def __init__(self, csrf):
        self.csrf = csrf

    @staticmethod
    def get_history():
        url = "https://api.bilibili.com/x/web-interface/history/cursor?max={}&view_at={}&business={}"
        max_ = 0
        view_at = 0
        business = ""
        history = user_manager.get(url.format(max_, view_at, business))
        while history.json()["data"]["cursor"]["max"] != 0:
            data = history.json()["data"]["list"]
            for cursor in range(0, len(data), 5):
                yield data[cursor:cursor + 5]
            max_ = history.json()["data"]["cursor"]["max"]
            view_at = history.json()["data"]["cursor"]["view_at"]
            business = history.json()["data"]["cursor"]["business"]
            history = user_manager.get(url.format(max_, view_at, business))

    def set_record_history(self, stop=True):
        req = user_manager.post(
            "https://api.bilibili.com/x/v2/history/shadow/set",
            data={"jsonp": "jsonp", "csrf": self.csrf, "switch": stop},
        )
        if req.json()["code"] == 0:
            print(("停止" if stop else "开启") + "记录历史成功.")
        else:
            print(("停止" if stop else "开启") + "记录历史失败!")
            print("错误代码: ", req.json()["code"])
            print("错误信息: ", req.json()["message"])

    @staticmethod
    def search_history(search=""):
        url = "https://api.bilibili.com/x/web-goblin/history/search?pn={}&keyword={}&business=all"
        cursor = 1
        req = user_manager.get(url.format(cursor, search))
        print("搜索数量: ", req.json()["data"]["page"]["total"])
        while req.json()["data"]["has_more"]:
            yield req.json()["data"]["list"]
            cursor += 1
            req = user_manager.get(url.format(cursor, search))

    @staticmethod
    def dump_history():
        return [j for i in BilibiliHistory.get_history() for j in i]


class BilibiliFavorite:
    @staticmethod
    def select_favorite(mid: int, aid: int = 0) -> list[int] | int:
        """
        选择收藏夹
        :param mid: 用户mid
        :param aid: 视频aid
        :return: 收藏夹id list or int
        """
        request = user_manager.get(
            f"https://api.bilibili.com/x/v3/fav/folder/created/list-all?type=2&rid={aid}&up_mid={mid}",
            cache=True,
        )
        print("\n")
        print("选择收藏夹")
        for index, item in enumerate(request.json()["data"]["list"]):
            print(
                f"{index + 1}: {item['title']} ({item['media_count']}) {'(已收藏)' if item['fav_state'] else ''}"
            )
        fail = False
        ids = []
        command = input("选择收藏夹(以逗号为分隔): ")
        if command == "quit" or command == "q":
            return 0
        for index, item in enumerate(command.split(",")):
            if not item.replace(" ", "").isdecimal():
                print(f"索引{index + 1} 错误: 输入的必须为数字!")
                fail = True
                break
            if int(item) - 1 < 0:
                print(f"索引{index + 1} 错误: 输入的必须为正数!")
                fail = True
                break
            try:
                if request.json()["data"]["list"][int(item) - 1]["fav_state"]:
                    print(f"索引{index + 1} 警告: 此收藏夹已收藏过该视频, 将不会重复收藏.")
                    continue
                ids.append(request.json()["data"]["list"][int(item) - 1]["id"])
            except IndexError:
                print(f"索引{index + 1} 错误: 索引超出收藏夹范围!")
                fail = True
        if fail:
            print("收藏失败!")
        return ids

    @staticmethod
    def select_one_favorite(mid: int, aid: int = 0):
        request = user_manager.get(
            f"https://api.bilibili.com/x/v3/fav/folder/created/list-all?type=2&rid={aid}&up_mid={mid}",
            cache=True,
        )
        for index, item in enumerate(request.json()["data"]["list"]):
            print(
                f"{index + 1}: {item['title']} ({item['media_count']}) {'(已收藏)' if item['fav_state'] else ''}"
            )
        command = input("选择收藏夹: ")
        if command == "quit" or command == "q":
            return 0
        if not command.isdecimal():
            print(f"错误: 输入的必须为数字!")
            return 0
        try:
            return request.json()["data"]["list"][int(command) - 1]["id"]
        except IndexError:
            print("错误: 索引超出收藏夹范围!")
            return 0
        except TypeError as e:
            print("错误: 收藏夹可能未开放")
            traceback.print_exc()

    @staticmethod
    def get_favorite(fav_id: int) -> Generator:
        """
        获取收藏夹
        :param fav_id: 收藏夹id
        :return: 收藏夹内容
        """
        pre_page = 5
        cursor = 1
        request = user_manager.get(
            f"https://api.bilibili.com/x/v3/fav/resource/list?ps=20&media_id={fav_id}",
            cache=True,
        )
        total = request.json()["data"]["info"]["media_count"] // pre_page + 1
        while True:
            ls = user_manager.get(
                f"https://api.bilibili.com/x/v3/fav/resource/list?ps=5&media_id={fav_id}&pn={cursor}",
                cache=True,
            )
            if total < cursor:
                break
            yield ls.json()["data"]["medias"]
            cursor += 1

    @staticmethod
    def get_favorite_information(fav_id: int) -> dict:
        """
        获取收藏夹信息
        :param fav_id:
        :return:
        """
        request = user_manager.get(
            f"https://api.bilibili.com/x/v3/fav/resource/list?ps=20&media_id={fav_id}"
        )
        return request.json()["data"]["info"]

    @staticmethod
    def export_favorite(fav_id: int):
        """
        导出收藏夹
        :param fav_id: 收藏夹id
        :return:
        """
        pre_page = 5
        cursor = 1
        r = user_manager.get(
            "https://api.bilibili.com/x/v3/fav/resource/list?ps=20&media_id="
            + str(fav_id)
        )
        total = r.json()["data"]["info"]["media_count"] // pre_page + (
            1 if r.json()["data"]["info"]["media_count"] % pre_page != 0 else 0
        )
        print(f"正在导出收藏夹\"{r.json()['data']['info']['title']}\".")
        # 导出格式
        export = {
            "id": r.json()["data"]["info"]["id"],
            "title": r.json()["data"]["info"]["title"],
            "cover": r.json()["data"]["info"]["cover"].replace("http", "https"),
            "media_count": r.json()["data"]["info"]["media_count"],
            "view": r.json()["data"]["info"]["cnt_info"]["play"],
            "user": {
                "name": r.json()["data"]["info"]["upper"]["name"],
                "mid": r.json()["data"]["info"]["upper"]["mid"],
                "create_time": r.json()["data"]["info"]["mtime"],
            },
            "medias": [],
        }
        with tqdm(total=total, desc=r.json()["data"]["info"]["title"]) as progress_bar:
            while True:
                if total < cursor:
                    break
                medias: List[dict] = user_manager.get(
                    f"https://api.bilibili.com/x/v3/fav/resource/list?ps=5&media_id={fav_id}&pn={cursor}"
                ).json()["data"]["medias"]
                for i in medias:
                    # 清理数据
                    del i["type"]
                    del i["bv_id"]
                    del i["ugc"]
                    del i["season"]
                    del i["ogv"]
                    del i["link"]
                    i["publish_time"] = i["pubtime"]
                    del i["pubtime"]
                    del i["ctime"]
                    i["cover"] = i["cover"].replace("http", "https")
                export["medias"] += medias
                cursor += 1
                progress_bar.update(1)
        with open(f"favorite_{str(fav_id)}_{str(round(time.time()))}.json", "w", encoding="utf-8") as f:
            json.dump(export, f, indent=4, ensure_ascii=False)
        print(f"导出收藏夹\"{r.json()['data']['info']['title']}\"成功.")

    @staticmethod
    def list_favorite(mid):
        ls = []
        request = user_manager.get(
            f"https://api.bilibili.com/x/v3/fav/folder/created/list-all?type=2&up_mid={mid}",
            cache=True,
        )
        for i in request.json()["data"]["list"]:
            ls.append(i["id"])
        return ls


class BilibiliInteraction:
    @staticmethod
    def like(bvid: str, unlike=False):
        r = user_manager.post(
            "https://api.bilibili.com/x/web-interface/archive/like",
            data={"bvid": bvid, "like": 2 if unlike else 1,
                  "csrf": user_manager.csrf},
        )
        if r.json()["code"] != 0:
            print("点赞或取消点赞失败!")
            print(f"错误信息: {r.json()['message']}")
        else:
            if unlike:
                print("取消点赞成功!")
            else:
                print("点赞成功!")

    @staticmethod
    def coin(bvid: str, count: int):
        r = user_manager.post(
            "https://api.bilibili.com/x/web-interface/coin/add",
            data={"bvid": bvid, "csrf": user_manager.csrf, "multiply": count},
        )
        if r.json()["code"] == 0:
            print("投币成功!")
        else:
            print("投币失败!")
            print(f"错误信息: {r.json()['message']}")

    @staticmethod
    def triple(bvid: str):
        r = user_manager.post(
            "https://api.bilibili.com/x/web-interface/archive/like/triple",
            data={"bvid": bvid, "csrf": user_manager.csrf},
        )
        if r.json()["code"] == 0:
            print("三联成功!")
        else:
            print("三联失败!")
            print(f"错误信息: {r.json()['message']}")

    @staticmethod
    def mark_interact_video(bvid: str, score: int):
        r = user_manager.post(
            "https://api.bilibili.com/x/stein/mark",
            data={"bvid": bvid, "csrf": user_manager.csrf, "mark": score},
        )
        if r.json()["code"] == 0:
            print("评分成功!")
        else:
            print("评分失败!")
            print(f"错误信息: {r.json()['message']}")

    @staticmethod
    def favorite(aid: int, favorite_list: list):
        if not favorite_list:
            print("收藏列表为空!")
            return
        r = user_manager.post(
            "https://api.bilibili.com/x/v3/fav/resource/deal",
            data={
                "rid": aid,
                "type": 2,
                "add_media_ids": ",".join("%s" % fav_id for fav_id in favorite_list),
                "csrf": user_manager.csrf,
            },
        )
        if r.json()["code"] == 0:
            print("收藏成功!")
        else:
            print("收藏失败!")
            print(f"错误信息: {r.json()['message']}")


# type
# 1	    视频稿件	稿件 aid
# 2	    话题	话题 id
# 4	    活动	活动 id
# 5	    小视频	小视频 id
# 6	    小黑屋封禁信息	封禁公示 id
# 7	    公告信息	公告 id
# 8	    直播活动	直播间 id
# 9	    活动稿件	(?)
# 10	直播公告	(?)
# 11	相簿（图片动态）	相簿 id
# 12	专栏	专栏 cvid
# 13	票务	(?)
# 14	音频	音频 auid
# 15	风纪委员会	众裁项目 id
# 16	点评	(?)
# 17	动态（纯文字动态&分享）	动态 id
# 18	播单	(?)
# 19	音乐播单	(?)
# 20	漫画	(?)
# 21	漫画	(?)
# 22	漫画	漫画 mcid
# 33	课程	课程 epid

# sort_type
# 默认为0
# 0：按时间
# 1：按点赞数
# 2：按回复数
# https://api.bilibili.com/x/v2/reply/reply?oid=113858106693946&type=1&root=252881092688&ps=10&pn=1&web_location=333.788
class BilibiliComment:
    @staticmethod
    def get_comment(content_type: int, content_id: int, sort_type: int = 0):
        pre_page = 10
        cursor = 1
        while True:
            datas = []
            try:
                ls = user_manager.get(
                    f"https://api.bilibili.com/x/v2/reply?type={content_type}&oid={content_id}&sort={sort_type}&ps={pre_page}"
                    f"&pn={cursor}",
                    cache=True,
                )
            except json.decoder.JSONDecodeError:
                time.sleep(1200)
                continue
            if not ls.json()["data"]["replies"]:
                break
            for i in ls.json()["data"]["replies"]:
                data = {"content": i["content"], "rpid": i["rpid"], "reply_count": i["rcount"], "like": i["like"],
                        "send_time": i["ctime"],
                        "user": {"mid": i["mid"], "uname": i["member"]["uname"],
                                 "level": i["member"]["level_info"]["current_level"]}}
                datas.append(data)
            yield datas
            cursor += 1

    @staticmethod
    def like_comment():
        pass

    @staticmethod
    def get_comment_reply(content_type: int, oid: int, comment_id: int, sort_type: int = 0):
        pre_page = 10
        cursor = 1
        while True:
            datas = []
            try:
                ls = user_manager.get(
                    f"https://api.bilibili.com/x/v2/reply/reply?type={content_type}&oid={oid}&sort={sort_type}&root={comment_id}&ps={pre_page}"
                    f"&pn={cursor}",
                    cache=True,
                )
            except json.decoder.JSONDecodeError:
                time.sleep(1200)
                continue
            if not ls.json()["data"]["replies"]:
                break
            for i in ls.json()["data"]["replies"]:
                data = {"content": i["content"], "rpid": i["rpid"], "like": i["like"],
                        "send_time": i["ctime"],
                        "user": {"mid": i["mid"], "uname": i["member"]["uname"],
                                 "level": i["member"]["level_info"]["current_level"]}}
                datas.append(data)
            yield datas
            cursor += 1


class BilibiliVideo:
    def __init__(
            self,
            bvid: str = "",
            aid: int = 0,
            epid: str = "",
            season_id: str = "",
            quality=80,
            view_online_watch=True,
            audio_quality=30280,
            bangumi=False,
            source="backup"
    ):
        if not any([bvid, aid, epid, season_id]):
            raise Exception("Video id can't be null.")
        self.bvid = bvid if bvid else av2bv(aid)
        self.aid = aid if aid else bv2av(bvid)
        self.epid = epid
        self.season_id = season_id
        self.bangumi = bangumi
        self.quality = quality
        self.audio_quality = audio_quality
        self.view_online_watch = view_online_watch
        self.author_mid = self.get_author_mid()
        self.source = source
        self.see_message = False

    def select_video(self, return_information=False):
        r = user_manager.get(
            "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + self.bvid,
            cache=True,
        )
        if r.json()["code"] != 0:
            print("获取视频信息错误!")
            print(r.json()["code"])
            print(r.json()["message"])
            return
        # if r.json()['data']["View"]['stat']['evaluation']:
        #     print("你播放的视频是一个互动视频.")
        #     base_cid = r.json()['data']["View"]['cid']
        #     self.play_interact_video(bvid, base_cid)
        #     return
        video = r.json()["data"]["View"]["pages"]
        title = r.json()["data"]["View"]["title"]
        pic = r.json()["data"]["View"]["pic"]
        if len(video) == 1:
            if not return_information:
                self.play(video[0]["cid"], title)
                return
            else:
                return (
                    video[0]["cid"],
                    title,
                    video[0]["part"],
                    pic,
                    r.json()["data"]["View"]["stat"]["evaluation"],
                )
        print("\n")
        print("视频选集")
        for i in video:
            print(f"{i['page']}: {i['part']}")
        print("\n")
        while True:
            page = input("选择视频: ")
            if page == "quit" or page == "q":
                break
            elif not page:
                continue
            elif not page.isdigit():
                print("输入的并不是数字!")
                continue
            elif int(page) > len(video) or int(page) <= 0:
                print("选视频超出范围!")
                continue
            if not return_information:
                self.play(video[int(page) - 1]["cid"], self.bvid)
            else:
                return (
                    video[int(page) - 1]["cid"],
                    title,
                    video[int(page) - 1]["part"],
                    pic,
                    True if r.json()[
                        "data"]["View"]["stat"]["evaluation"] else False,
                )
            break

    def get_author_mid(self):
        return user_manager.get(
            "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + self.bvid,
            cache=True,
        ).json()["data"]["Card"]["card"]["mid"]

    def select_video_collection(self):
        r = user_manager.get(
            f"https://api.bilibili.com/x/web-interface/view/detail?bvid={self.bvid}", cache=True)
        if r.json()["code"] != 0:
            print("获取视频信息错误!")
            print(r.json()["code"])
            print(r.json()["message"])
            return
        if not r.json()["data"]["View"].get("ugc_season"):
            print("视频并没有合集!")
            return
        video = r.json()["data"]["View"]["ugc_season"]["sections"]
        videos = []
        for i in video:
            videos += i["episodes"]
        print("\n")
        print("视频合集选集")
        for i, j in enumerate(videos):
            print(f"{i + 1}: {j['title']}")
        while True:
            page = input("选择视频: ")
            if page == "quit" or page == "q":
                break
            elif not page:
                continue
            elif not page.isdigit():
                print("输入的并不是数字!")
                continue
            elif int(page) > len(video) or int(page) <= 0:
                print("选视频超出范围!")
                continue
            view_short_video_info(videos[int(page) - 1]["bvid"])
            selected_video = BilibiliVideo(
                bvid=videos[int(page) - 1]["bvid"],
                quality=self.quality,
                view_online_watch=self.view_online_watch,
            )
            selected_video.select_video()
            break

    def switch_quality(self, cid):
        if self.bangumi:
            url = f"https://api.bilibili.com/pgc/player/web/playurl?cid={cid}&fnval=16&qn={self.quality}"
        else:
            url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={self.bvid}&fnval=16"
        play_url_request = user_manager.get(url, cache=True)
        can_use_quality = {v["id"] for v in play_url_request.json()["data"]["dash"]["video"]}
        can_use_quality_description = [quality_mapping[v] for v in can_use_quality]
        quality_description_number_mapping = list(zip(can_use_quality_description, can_use_quality))
        for index, description in enumerate(quality_description_number_mapping):
            print(f"{index + 1}: {description[0]}")
        quality = input("选择画质: ")
        if quality.isdigit() and int(quality) > 0 and int(quality) < len(quality_description_number_mapping) + 1:
            self.quality = quality_description_number_mapping[int(quality) - 1][1]
            print("更改成功! ")
        else:
            print("输入不正确! ")

    def get_video_and_audio_url(self, cid):
        if self.bangumi:
            url = f"https://api.bilibili.com/pgc/player/web/playurl?cid={cid}&fnval=16&qn={self.quality}"
        else:
            url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={self.bvid}&fnval=16"
        play_url_request = user_manager.get(url, cache=True)

        videos = play_url_request.json()["data" if not self.bangumi else "result"][
            "dash"
        ]["video"]
        audios = play_url_request.json()["data" if not self.bangumi else "result"][
            "dash"
        ]["audio"]
        video_mapping = {}
        audio_mapping = {}

        for i in videos:
            if i["codecs"].startswith("avc"):
                video_mapping[i["id"]] = {
                    "id": i["id"],
                    "url": i["backup_url"][0] if self.source == "backup" else i['base_url'],
                    "width": i["width"],
                    "height": i["height"],
                }

        for i in audios:
            audio_mapping[i["id"]] = i["backup_url"][0]

        default_audio = sorted(list(audio_mapping.keys()), reverse=True)[0]
        default_video = sorted(list(video_mapping.keys()), reverse=True)[0]

        try:
            audio_url = audio_mapping[self.audio_quality]
        except KeyError:
            audio_url = audio_mapping[default_audio]
        try:
            video_url = video_mapping[self.quality]["url"]
            width = video_mapping[self.quality]["width"]
            height = video_mapping[self.quality]["height"]
        except KeyError:
            video_url = video_mapping[default_video]["url"]
            width = video_mapping[default_video]["width"]
            height = video_mapping[default_video]["height"]
        return video_url, width, height, audio_url

    def play(self, cid, title=""):
        global saw
        if not os.path.exists("cached"):
            os.mkdir("cached")
        video_url, width, height, audio_url = self.get_video_and_audio_url(cid)

        if not os.path.exists(f"cached/{cid}.ass"):
            a = danmaku_provider()(
                get_danmaku(cid),
                width,
                height,
                reserve_blank=0,
                font_face="SimHei",
                font_size=25,
                alpha=0.8,
                duration_marquee=15.0,
                duration_still=10.0,
                comment_filter="",
                reduced=False
            )
            with open(f"cached/{cid}.ass", "w", encoding="utf-8") as f:
                f.write(a)
        command = (
            f"mpv "
            f'--sub-file="cached/{cid}.ass" '
            f'--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            f'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53" '
            f'--referrer="https://www.bilibili.com"  '
            f'--audio-file="{audio_url}" '
            f'--title="{title}" '
            f'"{video_url}"'
        )
        if not saw:
            print("如有未显示视频或加载过卡可以在主选项中输入 switch_source 以换视频源. 该信息仅会在第一次播放时显示.")
            saw = True
        with subprocess.Popen(command, shell=True) as p:
            if self.view_online_watch:
                try:
                    while p.poll() is None:
                        people_watching = user_manager.get(
                            f"https://api.bilibili.com/x/player/online/total?cid={cid}&bvid="
                            f"{self.bvid}"
                        )
                        people = f"\r{people_watching.json()['data']['total']} 人正在看"
                        print(people, end="", flush=True)
                        time.sleep(3)
                except (TypeError, requests.exceptions.RequestException):
                    print("获取观看人数时发生错误!\n")
                    traceback.print_exc()
                except KeyboardInterrupt:
                    return
            print("\n")

    def download_one(
            self,
            cid: int,
            pic_url: str,
            title: str = "",
            part_title: str = "",
            base_dir: str = "",
    ):
        if not self.bangumi:
            url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn={self.quality}&bvid={self.bvid}"
        else:
            url = f"https://api.bilibili.com/pgc/player/web/playurl?qn={self.quality}&cid={cid}&ep_id={self.bvid}"

        req = user_manager.get(url)
        download_url = req.json()["data" if not self.bangumi else "result"]["durl"][0][
            "url"
        ]
        # width = req.json()["data" if not self.bangumi else "result"]["durl"][0]["width"]
        # height = req.json()["data" if not self.bangumi else "result"]["durl"][0]["height"]
        if base_dir:
            download_dir = "download/" + base_dir + \
                           "/" + validate_title(title) + "/"
        else:
            download_dir = "download/" + validate_title(title) + "/"
        res = user_manager.get(download_url, stream=True)
        length = float(res.headers["content-length"])
        if not os.path.exists("download"):
            os.mkdir("download")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        dts = download_dir + validate_title(part_title) + ".mp4"
        if os.path.exists(dts):
            c = input("文件已存在, 是否覆盖(y/n)? ")
            if c != "y":
                print("停止操作.")
                return -100
        file = open(dts, "wb")
        progress = tqdm(
            total=length,
            initial=os.path.getsize(dts),
            unit_scale=True,
            desc=reprlib.repr(validate_title(part_title)
                              ).replace("'", "") + ".mp4",
            unit="B",
        )
        try:
            for chuck in res.iter_content(chunk_size=1024):
                file.write(chuck)
                progress.update(1024)
        except KeyboardInterrupt:
            file.close()
            os.remove(dts)
            if len(os.listdir(download_dir)) == 0:
                os.rmdir(download_dir)
            print("取消下载.")
            return False
        if not file.closed:
            file.close()
        if not os.path.exists(download_dir + validate_title(title) + ".jpg"):
            print("下载封面中...")
            with open(download_dir + validate_title(title) + ".jpg", "wb") as file:
                file.write(user_manager.get(pic_url).content)
        if not os.path.exists(download_dir + validate_title(part_title) + ".xml"):
            print("下载弹幕中...")
            with open(
                    download_dir + validate_title(part_title) + ".xml",
                    "w",
                    encoding="utf-8",
            ) as danmaku:
                danmaku.write(
                    user_manager.get(
                        f"https://comment.bilibili.com/{cid}.xml"
                    ).content.decode("utf-8")
                )
            with open(download_dir + validate_title(part_title) + ".proto", "wb") as danmaku:
                view = parse_view(cid)
                total = int(view['dmSge']['total'])
                danmaku_byte = [get_danmaku(cid, i)
                                for i in range(1, total + 1)]
                # a = danmaku_provider()(
                #     b"".join(danmaku_byte),
                #     width,
                #     height,
                #     reserve_blank=0,
                #     font_face="SimHei",
                #     font_size=25,
                #     alpha=0.8,
                #     duration_marquee=15.0,
                #     duration_still=10.0,
                #     comment_filter=None,
                #     reduced=False
                # )
                danmaku.write(b"".join(danmaku_byte))
        return True

    def download_video_list(self, base_dir=""):
        url = "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + self.bvid
        request = user_manager.get(url, cache=True)
        video = request.json()["data"]["View"]["pages"]
        title = request.json()["data"]["View"]["title"]
        pic = request.json()["data"]["View"]["pic"]
        total = len(video)
        count = 0
        for i in video:
            count += 1
            print(f"{count} / {total}")
            cid = i["cid"]
            part_title = i["part"]
            if not self.download_one(
                    cid, pic, title=title, part_title=part_title, base_dir=base_dir
            ):
                return False
        return True


class BilibiliMain:
    @staticmethod
    def recommend() -> list:
        r = user_manager.get(
            "https://api.bilibili.com/x/web-interface/wbi/index/top/feed/rcmd?"
            + encrypt_wbi("ps=5")
        )
        return r.json()["data"]["item"]

    @staticmethod
    def get_media_list(media_id: int):
        r = user_manager.get(
            f"https://api.bilibili.com/x/v3/fav/resource/ids?media_id={media_id}&platform=web"
        )
        return r.json()["data"]

    @staticmethod
    def media_list_info(media_id: int):
        r = user_manager.get(
            f"https://api.bilibili.com/x/v3/fav/folder/info?media_id={media_id}"
        )
        return r.json()["data"]


class BilibiliInterface:
    def __init__(self):
        self.audio = 30280
        self.quality: int = 32 if not user_manager.mid else 80
        self.view_online_watch = True
        self.source = "main"
        self.bilibili_favorite = BilibiliFavorite()
        self.interaction: BilibiliInteraction = BilibiliInteraction()
        # self.manga = BilibiliManga()
        self.history = BilibiliHistory(user_manager.csrf)
        self.bangumi = BilibiliBangumi(self.quality)
        self.delay = 1

    def favorite(self, mid=0):
        if not user_manager.is_login:
            print("请先登录!")
            return
        fav_id = self.bilibili_favorite.select_one_favorite(
            user_manager.mid if not mid else mid)
        if not fav_id:
            return
        all_request = self.bilibili_favorite.get_favorite(fav_id)
        for i in all_request:
            for num, item in enumerate(i):
                print(num + 1, ":")
                print("封面: ", item["cover"])
                print("标题: ", item["title"])
                print(
                    "作者: ",
                    item["upper"]["name"],
                    " bvid: ",
                    item["bvid"],
                    " 日期: ",
                    datetime.datetime.fromtimestamp(item["pubtime"]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    " 视频时长:",
                    format_time(item["duration"]),
                    " 观看量: ",
                    item["cnt_info"]["play"],
                )
            while True:
                command = input("选择视频: ")
                if command == "quit" or command == "q":
                    return
                elif not command:
                    break
                elif not command.isdecimal():
                    print("输入的不是整数!")
                    continue
                elif int(command) > len(i) or int(command) <= 0:
                    print("选视频超出范围!")
                    continue
                bvid = i[int(command) - 1]["bvid"]
                self.view_video(bvid, no_favorite=True)

    def recommend(self):
        print("推荐界面")
        while True:
            recommend_content = BilibiliMain.recommend()
            for num, item in enumerate(recommend_content):
                print(num + 1, ":")
                print("封面: ", item["pic"])
                print("标题: ", item["title"])
                print(
                    "作者: ",
                    item["owner"]["name"],
                    " bvid: ",
                    item["bvid"],
                    " 日期: ",
                    datetime.datetime.fromtimestamp(item["pubdate"]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    " 视频时长:",
                    format_time(item["duration"]),
                    " 观看量: ",
                    item["stat"]["view"],
                )
            while True:
                command = input("选择视频: ")
                if command == "quit" or command == "q":
                    return
                elif not command:
                    break
                elif not command.isdecimal():
                    print("输入的不是整数!")
                    continue
                elif int(command) > len(recommend_content) or int(command) <= 0:
                    print("选视频超出范围!")
                    continue
                bvid = recommend_content[int(command) - 1]["bvid"]
                # title = recommend_request.json()['data']['item'][int(command) - 1]['title']
                self.view_video(bvid)

    def address(self):
        video_address = input("输入地址: ")
        if "b23.tv" in video_address:
            video_address = user_manager.get(video_address).url

        url_split = video_address.split("/")
        if url_split[-1].startswith("?") or not url_split[-1]:
            video_id = url_split[-2]
        else:
            video_id = url_split[-1].split("?")[0]

        if video_id.startswith("BV"):
            view_short_video_info(video_id)
            self.view_video(bvid=video_id)
        else:
            try:
                view_short_video_info(av2bv(int(video_id.strip("av"))))
            except (KeyError, ValueError):
                traceback.print_exc()
                print("视频解析错误, 请确保你输入的视频地址正确.")
                return
            self.view_video(bvid=av2bv(int(video_id.strip("av"))))

    # def play_interact_video(self, bvid: str, cid: int):
    #     self.play(bvid, cid, view_online_watch=False)
    #
    #     graph_version = request_manager.get(f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}")
    #     graph_version = graph_version.json()['data']['interaction']['graph_version']
    #
    #     edge_id = ""
    #
    #     while True:
    #         edge_info = f"https://api.bilibili.com/x/stein/edgeinfo_v2" \
    #                     f"?graph_version={graph_version}" \
    #                     f"&bvid={bvid}" \
    #                     f"&edge_id={edge_id}"
    #         r = request_manager.get(edge_info)
    #         if not r.json()['data']['edges'].get('questions'):
    #             print("互动视频已到达末尾.")
    #             score = input("是否评分? (y/n): ")
    #             if score == "y":
    #                 score = input("评几分? (1-5): ")
    #                 if not score.isdecimal():
    #                     print("输入错误! 将停止评分")
    #                     return
    #                 self.interaction.mark_interact_video(bvid, int(score))
    #             break
    #         for i, j in enumerate(r.json()['data']['edges']['questions'][0]['choices']):
    #             print(f"{i + 1}: {j['option']}")
    #         while True:
    #             index = input("选择选项: ")
    #             if index.isdecimal():
    #                 break
    #             else:
    #                 print("请输入数字!")
    #         edge_id = r.json()['data']['edges']['questions'][0]['choices'][int(index) + 1]['id']
    #         cid = r.json()['data']['edges']['questions'][0]['choices'][int(index) + 1]['cid']
    #         self.play(bvid, cid, view_online_watch=False)

    def like(self, bvid, unlike=False):
        if not user_manager.is_login:
            print("请先登录!")
            return
        self.interaction.like(bvid, unlike=unlike)

    def coin(self, bvid):
        if not user_manager.is_login:
            print("请先登录!")
            return
        coin_count = input("输入币数(1-2): ")
        if coin_count != "1" and coin_count != "2":
            print("币数错误!")
            return
        self.interaction.coin(bvid, int(coin_count))

    def triple(self, bvid):
        if not user_manager.is_login:
            print("请先登录!")
            return
        self.interaction.triple(bvid)

    def add_favorite(self, aid):
        if not user_manager.is_login:
            print("请先登录!")
            return
        fav_id = self.bilibili_favorite.select_favorite(user_manager.mid, aid)
        if fav_id == 0:
            return
        self.interaction.favorite(aid, fav_id)  # type: ignore

    def download_favorite_video(self):
        if not user_manager.is_login:
            print("请先登录!")
            return
        fav_id = self.bilibili_favorite.select_one_favorite(user_manager.mid)
        if fav_id == 0:
            return
        info = self.bilibili_favorite.get_favorite_information(fav_id)
        count = 0
        total = info["media_count"]
        for i in self.bilibili_favorite.get_favorite(fav_id):
            for j in i:
                count += 1
                print(f"收藏夹进度: {count} / {total}")
                video = BilibiliVideo(bvid=j["bvid"], quality=80)
                if not video.download_video_list(
                        base_dir=validate_title(info["title"])
                ):
                    return

    # def download_manga(self):
    #     if not user_manager.is_login:
    #         print("请先登录!")
    #         return
    #     print("漫画id: 即 https://manga.bilibili.com/detail/mc29410 中的 29410")
    #     try:
    #         comic_id = input("请输入漫画id或url: ")
    #         if comic_id.startswith("https"):
    #             comic_id = comic_id.split("mc")[1]
    #         self.manga.download_manga(int(comic_id))
    #     except (ValueError, IndexError):
    #         print("id输入错误.")
    #     except KeyboardInterrupt:
    #         print("停止下载.")

    def export_favorite(self):
        if not user_manager.is_login:
            print("请先登录!")
            return
        fav_id = self.bilibili_favorite.select_one_favorite(user_manager.mid)
        if fav_id == 0:
            return
        self.bilibili_favorite.export_favorite(fav_id)

    def export_history(self):
        if not user_manager.is_login:
            print("请先登录!")
            return
        with open(f"history_{str(round(time.time()))}.json", "w", encoding="utf-8") as f:
            json.dump(self.history.dump_history(), f,
                      ensure_ascii=False, indent=4)

    def export_all_favorite(self):
        if not user_manager.is_login:
            print("请先登录!")
            return
        fav_id = self.bilibili_favorite.list_favorite(user_manager.mid)
        for i in fav_id:
            self.bilibili_favorite.export_favorite(i)

    def view_history(self):
        if not user_manager.is_login:
            print("请先登录!")
            return
        print("历史界面")
        print()
        for history in BilibiliHistory.get_history():
            flag = True
            while flag:
                for num, item in enumerate(history):
                    if item["history"]["business"] != "archive":
                        print("该类型的历史记录不支持播放.")
                        continue
                    print(num + 1, ":")
                    print("封面: ", item["cover"])
                    print("标题: ", item["title"])
                    print(
                        "作者: ",
                        item["author_name"],
                        " bvid: ",
                        item["history"]["bvid"],
                        " 视频时长:",
                        format_time(item["progress"]),
                        "/",
                        format_time(item["duration"]),
                    )
                    print(
                        "观看时间: ",
                        datetime.datetime.fromtimestamp(item["view_at"]).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    )
                while True:
                    command = input("选择视频: ")
                    if command == "quit" or command == "q":
                        return
                    elif not command:
                        flag = False
                        break
                    elif not command.isdecimal():
                        print("输入的不是整数!")
                        continue
                    elif int(command) > len(history) or int(command) <= 0:
                        print("选视频超出范围!")
                        continue
                    bvid = history[int(command) - 1]["history"]["bvid"]
                    if not bvid:
                        print("该类型的历史记录不支持播放.")
                        continue
                    # title = recommend_request.json()['data']['item'][int(command) - 1]['title']
                    self.view_video(bvid)

    def user_space(self, mid: int):
        user_data = BilibiliUserSpace.get_user_data(mid)
        print("用户空间")
        print("")
        print("用户名: " + user_data["name"])
        print("头像: " + user_data["face"])
        print(
            "Level: "
            + str(user_data["level"])
            + (" 硬核会员" if user_data["is_senior_member"] == 1 else "")
        )
        print("个性签名: " + user_data["sign"])
        print("")
        while True:
            command = input("用户空间选项: ")
            if command == "list_video":
                self.list_user_video(mid)
            elif command == "get_follow_bangumi":
                for i, j in enumerate(BilibiliBangumi.get_follow_bangumi(mid)):
                    print(f"{i + 1}: ")
                    print(f"封面: {j['img']}")
                    print(
                        f"名称: {j['title']} 更新进度: {j['update_progress']} 观看进度: {j['watch_progress']}"
                    )
            elif command == "quit" or command == "q":
                return
            elif command == "list_fans":
                self.list_fans(mid)
            elif command == "list_followed":
                self.list_followed(mid)
            elif command == "list_favorite":
                self.favorite(mid)
            elif command:
                print("未知命令!")

    def list_fans(self, mid: int):
        fans_list = BilibiliUserSpace.get_following_list(mid)
        print("粉丝数: " + str(len(fans_list)))
        if len(fans_list) > 100:
            print("注意: 粉丝数超过100, 根据b站系统限制默认只能获取100条信息.")
        for i, j in enumerate(fans_list):
            print(f"{i + 1}:")
            print(f"头像: {j['face']}")
            print(f"昵称: {j['uname']} mid: {j['mid']}")
            print(f"签名: {j['sign']}")
        while True:
            select = input("选择用户: ")
            if select == "quit" or select == "q":
                return
            elif not select.isdecimal():
                print("输入的不是整数!")
                continue
            elif int(select) > len(fans_list) or int(select) <= 0:
                print("选择用户超出范围!")
                continue
            while True:
                command = input("粉丝选项: ")
                if command == "user_space":
                    self.user_space(fans_list[int(select) - 1]['mid'])
                elif command == "quit" or command == "q":
                    break
                else:
                    print("未知命令! ")

    def list_followed(self, mid: int):
        fans_list = BilibiliUserSpace.get_followed_list(mid)
        print("关注数: " + str(len(fans_list)))
        if len(fans_list) > 100:
            print("注意: 关注数超过100, 根据b站系统限制默认只能获取100条信息.")
        for i, j in enumerate(fans_list):
            print(f"{i + 1}:")
            print(f"头像: {j['face']}")
            print(f"昵称: {j['uname']} mid: {j['mid']}")
            print(f"签名: {j['sign']}")
        while True:
            select = input("选择用户: ")
            if select == "quit" or select == "q":
                return
            elif not select.isdecimal():
                print("输入的不是整数!")
                continue
            elif int(select) > len(fans_list) or int(select) <= 0:
                print("选择用户超出范围!")
                continue
            while True:
                command = input("关注选项: ")
                if command == "user_space":
                    self.user_space(fans_list[int(select) - 1]['mid'])
                elif command == "quit" or command == "q":
                    break
                else:
                    print("未知命令! ")

    def list_user_video(self, mid: int):
        for i in BilibiliUserSpace.get_user_video(mid):
            if not i:
                print("该UP主未发送过视频.")
                return
            for num, item in enumerate(i):
                print(num + 1, ":")
                print("封面: ", item["pic"])
                print("标题: ", item["title"])
                print(
                    "作者: ",
                    item["author"],
                    " bvid: ",
                    item["bvid"],
                    " 日期: ",
                    datetime.datetime.fromtimestamp(item["created"]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    " 视频时长:",
                    item["length"],
                    " 观看量: ",
                    item["play"],
                )
            while True:
                command = input("选择视频: ")
                if command == "quit" or command == "q":
                    return
                if not command:
                    break
                elif not command.isdecimal():
                    print("输入的不是整数!")
                    continue
                elif int(command) > len(i) or int(command) <= 0:
                    print("选视频超出范围!")
                    continue
                bvid = i[int(command) - 1]["bvid"]
                self.view_video(bvid)

    def search(self):
        keyword = input("输入关键词: ")
        if keyword == "quit" or keyword == "q":
            return
        for i in BilibiliSearch.search(keyword):
            for index, result in enumerate(i):
                print(index + 1, ":")
                print("封面: ", "https:" + result["pic"])
                print("标题: ", result["title"])
                print(
                    "作者: ",
                    result["author"],
                    " bvid: ",
                    result["bvid"],
                    " 日期: ",
                    datetime.datetime.fromtimestamp(result["pubdate"]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    " 视频时长:",
                    result["duration"],
                    " 观看量: ",
                    result["play"],
                )
            while True:
                command = input("选择视频: ")
                if command == "quit" or command == "q":
                    return
                if not command:
                    break
                elif not command.isdecimal():
                    print("输入的不是整数!")
                    continue
                elif int(command) > len(i) or int(command) <= 0:
                    print("选视频超出范围!")
                    continue
                bvid = i[int(command) - 1]["bvid"]
                self.view_video(bvid)

    def view_comment(self, bvid):
        comment_generator = BilibiliComment.get_comment(1, bv2av(bvid))
        for i in comment_generator:
            for index, result in enumerate(i):
                print(index + 1, ":")
                print(
                    "作者: ",
                    result["member"]["uname"],
                    " 日期: ",
                    datetime.datetime.fromtimestamp(result["ctime"]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    " 点赞量: ",
                    result["like"],
                )
                print("内容: ", result["content"]["message"])
            while True:
                command = input("评论选项: ")
                if command == "quit" or command == "q":
                    return
                if command == "next":
                    break
                else:
                    print("未知命令!")

    def view_video(self, bvid, no_favorite=False):
        video = BilibiliVideo(
            bvid=bvid, quality=self.quality, view_online_watch=self.view_online_watch, source=self.source
        )
        while True:
            command = input("视频选项(p/l/ul/c/t/f/d/da/q/fo/ufo/cm): ")
            if command == "quit" or command == "q":
                return
            if command == "play" or command == "p":
                video.select_video()
            elif command == "switch_quality":
                cid, title, _, _, _ = video.select_video(
                    return_information=True
                )
                video.switch_quality(cid)
            elif command == "download" or command == "d":
                cid, title, part_title, pic, is_dynamic = video.select_video(
                    return_information=True
                )
                print(is_dynamic)
                if is_dynamic:
                    print("互动视频无法下载! ")
                    return
                video.download_one(
                    cid, pic_url=pic, title=title, part_title=part_title)
            elif command == "download_video_list" or command == "da":
                video.download_video_list(bvid)
            elif command == "like" or command == "l":
                self.like(bvid)
            elif command == "unlike" or command == "ul":
                self.like(bvid, unlike=True)
            elif command == "coin" or command == "c":
                self.coin(bvid)
            elif command == "triple" or command == "t":
                self.triple(bvid)
            elif (command == "favorite" or command == "f") and not no_favorite:
                self.add_favorite(bv2av(bvid))
                user_manager.cached_response = {}
            elif command == "follow" or command == "fo":
                BilibiliUserSpace.modify_relation(
                    video.get_author_mid(), modify_type=1)
            elif command == "unfollow" or command == "ufo":
                BilibiliUserSpace.modify_relation(
                    video.get_author_mid(), modify_type=2)
            elif command == "comment" or command == "cm":
                self.view_comment(bvid)
            elif command == "export_comment":
                data = []
                for i in BilibiliComment.get_comment(1, bv2av(bvid)):
                    for j in i:
                        data.append(j)
                    time.sleep(self.delay)
                for i in data:
                    if i["reply_count"] > 0:
                        replies = BilibiliComment.get_comment_reply(1, bv2av(bvid), i["rpid"])
                        replies_data = []
                        for reply in replies:
                            replies_data.append(reply)
                            time.sleep(self.delay)
                        i["reply"] = replies_data
                with open(f"comment_{bvid}.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            elif command == "export_danmaku":
                cid, title, _, _, _ = video.select_video(
                    return_information=True
                )
                view = parse_view(cid)
                total = int(view['dmSge']['total'])
                danmaku_byte_list = [get_danmaku(
                    cid, i) for i in range(1, total + 1)]
                danmaku_byte = b"".join(danmaku_byte_list)
                DM = DmSegMobileReply()
                DM.ParseFromString(danmaku_byte)
                with open(f"{cid}.json", "w", encoding="utf-8") as f:
                    json.dump(MessageToJson(DM), f,
                              indent=4, ensure_ascii=False)
            elif command == "view_user":
                self.user_space(video.get_author_mid())
            elif command == "view_video_collection":
                video.select_video_collection()
            else:
                print("未知命令!")

    def login(self):
        if user_manager.is_login:
            print("已经登录!")
        else:
            cookies = ""
            BilibiliLogin.generate_cookie()
            login_method = input("登录方式 (sms/password): ")
            if login_method == "password":
                username = input("输入用户名: ")
                password = getpass.getpass("输入密码: ")
                cookies = BilibiliLogin.login_by_password(
                    username, password)
            elif login_method == "sms":
                print("默认区号为 +86 (中国).")
                tel = input("输入电话号码: ")
                captcha_key = BilibiliLogin.send_sms(tel)
                if captcha_key:
                    sms_code = input("输入认证码: ")
                    cookies = BilibiliLogin.login_by_sms(tel, captcha_key, sms_code)
            if cookies:
                print("登录成功!")
                with open("cookie.txt", "w") as f:
                    f.write(cookies)
                user_manager.refresh_login()

    def main(self):
        while True:
            command = input("主选项(r/a/b/f/s/q/l): ")
            command = command.lower().strip()
            if command == "recommend" or command == "r":
                self.recommend()
            elif command == "address" or command == "a":
                self.address()
            elif command == "help" or command == "h":
                show_help()
            elif command == "bangumi" or command == "b":
                bangumi_address = input("输入地址: ")
                if bangumi_address.split("/")[-1].startswith("ep"):
                    self.bangumi.select_bangumi(
                        epid=bangumi_address.split("/")[-1].strip("ep")
                    )
                else:
                    self.bangumi.select_bangumi(
                        ssid=bangumi_address.split("/")[-1].strip("ss")
                    )
            elif command == "favorite" or command == "f":
                self.favorite()
            elif command == "quit" or command == "q":
                sys.exit(0)
            elif command == "search" or command == "s":
                self.search()
            elif command == "enable_online_watching":
                self.view_online_watch = True
            elif command == "disable_online_watching":
                self.view_online_watch = False
            elif command == "clean_cache":
                shutil.rmtree("cached")
                os.mkdir("cached")
            elif command == "refresh_login":
                user_manager.refresh_login()
            elif command == "export_favorite":
                self.export_favorite()
            elif command == "export_history":
                self.export_history()
            elif command == "export_all_favorite":
                self.export_all_favorite()
            elif command == "download_favorite":
                self.download_favorite_video()
            elif command == "history":
                self.view_history()
            elif command == "view_self":
                if user_manager.is_login:
                    self.user_space(user_manager.mid)
                else:
                    print("用户未登录!")
            elif command == "view_user":
                self.user_space(int(input("请输入用户mid: ")))
            # elif command == "download_manga":
            #     self.download_manga()
            elif command == "switch_source":
                print("切换播放源成功")
                if self.source == "backup":
                    self.source = ""
                else:
                    self.source = "backup"
            elif command == "login" or command == "l":
                self.login()
            elif command == "logout" or command == "lo":
                if input("确定退出? (y/n)").lower() == "y":
                    BilibiliLogin.logout()
            elif command == "set_export_delay":
                self.delay = int(input("输入导出延迟: "))
            else:
                print("未知命令!")


print(f"LBCC v{__version__}.")
print()
print("Type \"help\" for more information.")
print()

if __name__ == "__main__":
    user_manager.login()
    bilibili = BilibiliInterface()
    bilibili.main()
