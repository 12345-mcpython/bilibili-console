#!/usr/bin/env python3
"""
Copyright (c) 2023 Laosun Studios.

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
import reprlib
import shutil
import subprocess
import sys
import time
import traceback

import requests
from tqdm import tqdm

from bilibili.biliass import Danmaku2ASS
from bilibili.utils import enc, dec, format_time, validate_title, \
    convert_cookies_to_dict, clean_cookie, encrypt_wbi, request_manager, hum_convert

__version__ = '1.0.0-dev'

__year__ = 2023

__author__ = "Laosun Studios"


class BilibiliManga:
    def __init__(self):
        self.request_manager = request_manager

    def get_manga_detail(self, manga_id: int) -> dict:
        detail_request = self.request_manager.post(
            "https://manga.bilibili.com/twirp/comic.v1.Comic/ComicDetail?device=pc&platform=web",
            data={"comic_id": manga_id})
        return detail_request.json()

    def get_wallet(self) -> dict:
        wallet = self.request_manager.post("https://manga.bilibili.com/twirp/user.v1.User/GetWallet?device=pc&platform"
                                           "=web")
        return wallet.json()

    def list_history(self) -> dict:
        history = self.request_manager.post(
            "https://manga.bilibili.com/twirp/bookshelf.v1.Bookshelf/ListHistory?device=pc&platform=web",
            data={"page_num": 1, "page_size": 50})
        return history.json()

    def get_image_list(self, epid) -> dict:
        images = self.request_manager.post(
            "https://manga.bilibili.com/twirp/comic.v1.Comic/GetImageIndex?device=pc&platform=web",
            data={"ep_id": epid})
        return images.json()

    def get_token(self, image: str) -> dict:
        token = self.request_manager.post(
            "https://manga.bilibili.com/twirp/comic.v1.Comic/ImageToken?device=pc&platform=web",
            data={"urls": "[\"{}\"]".format(image)})
        return token.json()

    def download_manga(self, manga_id: int) -> dict:
        manga_info = self.get_manga_detail(manga_id)
        ep_info = manga_info['data']['ep_list']
        name = manga_info['data']['title']
        if not os.path.exists("download/manga"):
            os.mkdir("download/manga")
        if not os.path.exists("download/manga/" + validate_title(name)):
            os.mkdir("download/manga/" + validate_title(name))
        first, end = input("选择回目范围 (1-{}): ".format(len(ep_info))).split("-")
        first = int(first)
        end = int(end)
        download_manga_epid = []
        download_manga_name = []
        locked = 0
        for i in list(reversed(ep_info)):
            if i["ord"] >= first and i['ord'] <= end:
                if i['is_locked']:
                    locked += 1
                    continue
                download_manga_epid.append(i['id'])
                download_manga_name.append(i['title'])
        print(f"有{locked}篇被上锁, 需要购买" if locked else '')
        download_image = {}
        cursor = 0
        picture_count = 0
        print("获取图片信息中.")
        with tqdm(total=end) as progress_bar:
            for i in download_manga_epid:
                download_image_prefix = []
                image_list = self.get_image_list(i)
                for j in image_list['data']['images']:
                    download_image_prefix.append(j['path'])
                    picture_count += 1
                download_image[download_manga_name[cursor]] = download_image_prefix
                progress_bar.update(1)
                cursor += 1
        download_image_url = {}
        print("获取图片token中.")
        with tqdm(total=picture_count) as progress_bar:
            for i, j in download_image.items():
                download_image_url_local = []
                for k in j:
                    token = self.get_token(k)['data'][0]
                    download_image_url_local.append("{}?token={}".format(token['url'], token['token']))
                    progress_bar.update(1)
                download_image_url[i] = download_image_url_local
        print("下载图片中.")
        byte = 0
        with tqdm(total=picture_count) as progress_bar:
            for i, j in download_image_url.items():
                filename = 0
                for k in j:
                    path = "download/manga/" + validate_title(name) + "/" + validate_title(i) + "/"
                    file = path + f"{filename}.jpg"
                    if not os.path.exists(path):
                        os.mkdir(path)
                    with open(file, "wb") as f:
                        byte += f.write(request_manager.get(k).content)
                        progress_bar.update(1)
                        filename += 1
        print("下载完成. 总计下载了 {} 字节 ({})".format(byte, hum_convert(byte)))


class BilibiliFavorite:
    def __init__(self, mid: int):
        self.request_manager = request_manager
        self.mid = mid

    def choose_favorite(self, mid: int, avid: int = 0, one=False) -> list[int] | int:
        """
        选择收藏夹
        :param mid: 用户mid
        :param avid: 视频avid
        :param one: 是否为单选模式
        :return: 收藏夹id list or int
        """
        request = self.request_manager.get(
            f"https://api.bilibili.com/x/v3/fav/folder/created/list-all?type=2&rid={avid}&up_mid={mid}", cache=True)
        print("\n")
        print("选择收藏夹")
        for index, item in enumerate(request.json()['data']['list']):
            print(f"{index + 1}: {item['title']} ({item['media_count']}) {'(已收藏)' if item['fav_state'] else ''}")
        while True:
            if not one:
                ids = []
                choose = input("选择收藏夹(以逗号为分隔): ")
                for index, item in enumerate(choose.split(",")):
                    if not item.replace(" ", "").isdecimal():
                        print(f"索引{index + 1} Error: 输入的必须为数字!")
                        continue
                    if int(item) - 1 < 0:
                        print(f"索引{index + 1} Error: 输入的必须为正数!")
                        continue
                    if request.json()['data']['list'][int(item) - 1]['fav_state']:
                        print(f"索引{index + 1} Warning: 此收藏夹已收藏过该视频, 将不会重复收藏.")
                    try:
                        ids.append(request.json()['data']['list'][int(item) - 1]['id'])
                    except IndexError:
                        print(f"索引{index + 1} Error: 索引超出收藏夹范围!")
                return ids
            else:
                choose = input("选择收藏夹: ")
                if not choose.isdecimal():
                    print(f"Error: 输入的必须为数字!")
                    continue
                try:
                    return request.json()['data']['list'][int(choose) - 1]['id']
                except IndexError:
                    print("Error: 索引超出收藏夹范围!")

    def get_favorite(self, fav_id: int) -> list:
        """
        获取收藏夹
        :param fav_id: 收藏夹id
        :return: 收藏夹内容
        """
        pre_page = 5
        cursor = 1
        request = self.request_manager.get(f"https://api.bilibili.com/x/v3/fav/resource/list?ps=20&media_id={fav_id}",
                                           cache=True)
        total = request.json()['data']['info']['media_count'] // pre_page + 1
        while True:
            ls = self.request_manager.get(
                f"https://api.bilibili.com/x/v3/fav/resource/list?ps=5&media_id={fav_id}&pn={cursor}", cache=True)
            if total < cursor:
                break
            yield ls.json()['data']['medias']
            cursor += 1

    def get_favorite_information(self, fav_id: int) -> list:
        """
        获取收藏夹信息
        :param fav_id:
        :return:
        """
        request = self.request_manager.get(f"https://api.bilibili.com/x/v3/fav/resource/list?ps=20&media_id={fav_id}")
        return request.json()['data']['info']

    def export_favorite(self, fav_id: int):
        """
        导出收藏夹
        :param fav_id: 收藏夹id
        :return:
        """
        pre_page = 5
        cursor = 1
        r = self.request_manager.get("https://api.bilibili.com/x/v3/fav/resource/list?ps=20&media_id=" + str(fav_id))
        total = r.json()['data']['info']['media_count'] // pre_page + (
            1 if r.json()['data']['info']['media_count'] % pre_page != 0 else 0)
        print(f"正在导出收藏夹\"{r.json()['data']['info']['title']}\".")
        # 导出格式
        export = {
            "id": r.json()['data']['info']['id'],
            "title": r.json()['data']['info']['title'],
            "cover": r.json()['data']['info']['cover'].replace("http", "https"),
            "media_count": r.json()['data']['info']['media_count'],
            "view": r.json()['data']['info']['cnt_info']['play'],
            "user": {
                "name": r.json()['data']['info']['upper']['name'],
                "mid": r.json()['data']['info']['upper']['mid'],
                "create_time": r.json()['data']['info']['mtime'],
            },
            "medias": []
        }
        with tqdm(total=total, desc=r.json()['data']['info']['title']) as progress_bar:
            while True:
                if total < cursor:
                    break
                medias = self.request_manager.get(
                    f"https://api.bilibili.com/x/v3/fav/resource/list?ps=5&media_id={fav_id}&pn={cursor}")
                medias = medias.json()['data']['medias']
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
                    i['cover'] = i['cover'].replace("http", "https")
                export['medias'] += medias
                cursor += 1
                progress_bar.update(1)
        with open(str(fav_id) + '.json', "w", encoding="utf-8") as f:
            json.dump(export, f, ensure_ascii=False, sort_keys=True)
        print(f"导出收藏夹\"{r.json()['data']['info']['title']}\"成功.")

    def list_favorite(self, mid):
        ls = []
        request = self.request_manager.get(
            f"https://api.bilibili.com/x/v3/fav/folder/created/list-all?type=2&up_mid={mid}", cache=True)
        for i in request.json()['data']['list']:
            ls.append(i['id'])
        return ls


class BilibiliInteraction:
    def __init__(self, favorite: BilibiliFavorite):
        self.request_manager = request_manager
        self.csrf: str = clean_cookie(convert_cookies_to_dict(self.request_manager.session.headers.get("cookie"))).get(
            "bili_jct", "")
        self.favorite = favorite

    def like(self, bvid: str, unlike=False):

        r = self.request_manager.post("https://api.bilibili.com/x/web-interface/archive/like",
                                      data={"bvid": bvid, "like": 2 if unlike else 1, "csrf": self.csrf})
        if r.json()['code'] != 0:
            print("点赞或取消点赞失败!")
            print(f"错误信息: {r.json()['message']}")
        else:
            if unlike:
                print("取消点赞成功!")
            else:
                print("点赞成功!")

    def coin(self, bvid: str, count: int):

        r = self.request_manager.post("https://api.bilibili.com/x/web-interface/coin/add",
                                      data={"bvid": bvid, 'csrf': self.csrf, 'multiply': count})
        if r.json()['code'] == 0:
            print("投币成功!")
        else:
            print("投币失败!")
            print(f"错误信息: {r.json()['message']}")

    def triple(self, bvid: str):
        r = self.request_manager.post("https://api.bilibili.com/x/web-interface/archive/like/triple",
                                      data={"bvid": bvid, "csrf": self.csrf})
        if r.json()['code'] == 0:
            print("三联成功!")
        else:
            print("三联失败!")
            print(f"错误信息: {r.json()['message']}")

    def mark_interact_video(self, bvid: str, score: int):
        r = self.request_manager.post("https://api.bilibili.com/x/stein/mark",
                                      data={"bvid": bvid, "csrf": self.csrf, "mark": score})
        if r.json()['code'] == 0:
            print("评分成功!")
        else:
            print("评分失败!")
            print(f"错误信息: {r.json()['message']}")

    def favorite_video(self, aid: int, favorite_list: list):
        r = self.request_manager.post("https://api.bilibili.com/x/v3/fav/resource/deal",
                                      data={"rid": aid, "type": 2,
                                            "add_media_ids": ",".join('%s' % fav_id for fav_id in favorite_list),
                                            "csrf": self.csrf})
        if r.json()['code'] == 0:
            print("收藏成功!")
        else:
            print("收藏失败!")
            print(f"错误信息: {r.json()['message']}")


class BiliBiliVideo:
    def __init__(self, bvid="", aid="",
                 epid="", season_id="", quality=80, view_online_watch=True,
                 audio_quality=30280, bangumi=False):
        if not any([bvid, aid, epid, season_id]):
            raise Exception("Video id can't be null.")
        self.bvid = bvid if bvid else enc(aid)
        self.aid = aid if aid else dec(bvid)
        self.epid = epid
        self.season_id = season_id
        self.bangumi = bangumi
        self.request_manager = request_manager
        self.quality = quality
        self.audio_quality = audio_quality
        self.view_online_watch = view_online_watch

    def choose_video(self, return_information=False):
        url = "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + self.bvid
        r = self.request_manager.get(url, cache=True)
        if r.json()['code'] != 0:
            print("获取视频信息错误!")
            print(r.json()['code'])
            print(r.json()['message'])
            return
        # if r.json()['data']["View"]['stat']['evaluation']:
        #     print("你播放的视频是一个互动视频.")
        #     base_cid = r.json()['data']["View"]['cid']
        #     self.play_interact_video(bvid, base_cid)
        #     return
        video = r.json()['data']["View"]["pages"]
        title = r.json()['data']["View"]['title']
        pic = r.json()['data']["View"]['pic']
        if len(video) == 1:
            if not return_information:
                self.play(video[0]['cid'], title)
                return
            else:
                return video[0]['cid'], title, video[0]['part'], pic, r.json()['data']["View"]['stat']['evaluation']
        print("\n")
        print("视频选集")
        for i in video:
            print(f"{i['page']}: {i['part']}")
        print("\n")
        while True:
            page = input("选择视频: ")
            if page == "exit":
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
                self.play(self.bvid, video[int(page) - 1]['cid'], title)
            else:
                return video[int(page) - 1]['cid'], title, video[int(page) - 1]['part'], pic, True if \
                    r.json()['data']["View"]['stat']['evaluation'] \
                    else False
            break

    def choose_video_collection(self):
        url = "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + self.bvid
        r = self.request_manager.get(url, cache=True)
        if r.json()['code'] != 0:
            print("获取视频信息错误!")
            print(r.json()['code'])
            print(r.json()['message'])
            return
        if not r.json()['data']['View'].get("ugc_season"):
            print("视频并没有合集!")
            return
        video = r.json()['data']['View']['ugc_season']['sections']
        videos = []
        for i in video:
            videos += i['episodes']
        print("\n")
        print("视频合集选集")
        for i, j in enumerate(videos):
            print(f"{i + 1}: {j['title']}")
        while True:
            page = input("选择视频: ")
            if page == "exit":
                break
            elif not page:
                continue
            elif not page.isdigit():
                print("输入的并不是数字!")
                continue
            elif int(page) > len(video) or int(page) <= 0:
                print("选视频超出范围!")
                continue
            choose_video = BiliBiliVideo(bvid=videos[int(page) - 1]['bvid'],
                                         quality=self.quality,
                                         view_online_watch=self.view_online_watch)
            choose_video.choose_video()
            break

    def play(self, cid, title=""):
        if self.bangumi:
            url = f"https://api.bilibili.com/pgc/player/web/playurl?cid={cid}&fnval=16&qn={self.quality}"
        else:
            url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={self.bvid}&fnval=16"

        play_url_request = self.request_manager.get(url, cache=True)

        videos = play_url_request.json()['data' if not self.bangumi else 'result']['dash']["video"]
        audios = play_url_request.json()['data' if not self.bangumi else 'result']['dash']["audio"]
        video_mapping = {}
        audio_mapping = {}

        for i in videos:
            if i['codecs'].startswith('avc'):
                video_mapping[i['id']] = {"id": i['id'], "url": i['base_url'], "width": i['width'],
                                          "height": i['height']}

        for i in audios:
            audio_mapping[i['id']] = i['base_url']

        default_audio = sorted(list(audio_mapping.keys()), reverse=True)[0]
        default_video = sorted(list(video_mapping.keys()), reverse=True)[0]

        try:
            audio_url = audio_mapping[self.audio_quality]
        except KeyError:
            audio_url = audio_mapping[default_audio]
        try:
            video_url = video_mapping[self.quality]['url']
            width = video_mapping[self.quality]['width']
            height = video_mapping[self.quality]['height']
        except KeyError:
            video_url = video_mapping[default_video]['url']
            width = video_mapping[default_video]['width']
            height = video_mapping[default_video]['height']
        if not os.path.exists(f"cached/{cid}.ass"):
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
                  f"--referrer=\"https://www.bilibili.com\"  " \
                  f"--audio-file=\"{audio_url}\" " \
                  f"--title=\"{title}\" " \
                  f"--loop " \
                  f"\"{video_url}\""
        with subprocess.Popen(command, shell=True) as p:
            if self.view_online_watch:
                try:
                    while p.poll() is None:
                        people_watching = self.request_manager.get(
                            f"https://api.bilibili.com/x/player/online/total?cid={cid}&bvid="
                            f"{self.bvid}")
                        people = f"\r{people_watching.json()['data']['total']} 人正在看"
                        print(people, end="", flush=True)
                        time.sleep(3)
                except (TypeError, requests.exceptions.RequestException):
                    print("获取观看人数时发生错误!\n")
                    traceback.print_exc()
                except KeyboardInterrupt:
                    return
            print("\n")

    def get_danmaku(self, cid: int):
        resp = self.request_manager.get(
            "https://api.bilibili.com/x/v2/dm/web/seg.so?type=1&oid={}&segment_index=1".format(cid),
            cache=True)
        return resp.content

    def download_one(self, cid: int, pic_url: str, title: str = "", part_title: str = "", base_dir: str = ""):
        if not self.bangumi:
            url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn={self.quality}&bvid={self.bvid}"
        else:
            url = f"https://api.bilibili.com/pgc/player/web/playurl?qn={self.quality}&cid={cid}&ep_id={self.bvid}"

        req = self.request_manager.get(url)
        download_url = req.json()["data" if not self.bangumi else "result"]["durl"][0]["url"]
        if base_dir:
            download_dir = "download/" + base_dir + "/" + validate_title(title) + "/"
        else:
            download_dir = "download/" + validate_title(title) + "/"
        res = self.request_manager.get(download_url, stream=True)
        length = float(res.headers['content-length'])
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
        file = open(dts, 'wb')
        progress = tqdm(total=length, initial=os.path.getsize(dts), unit_scale=True,
                        desc=reprlib.repr(validate_title(part_title)).replace("'", "") + ".mp4", unit="B")
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
                file.write(self.request_manager.get(pic_url).content)
        if not os.path.exists(download_dir + validate_title(part_title) + ".xml"):
            print("下载弹幕中...")
            with open(download_dir + validate_title(part_title) + ".xml", "w",
                      encoding="utf-8") as danmaku:
                danmaku.write(
                    self.request_manager.get(f"https://comment.bilibili.com/{cid}.xml").content.decode("utf-8"))
        return True

    def download_video_list(self, base_dir=""):
        url = "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + self.bvid
        request = self.request_manager.get(url, cache=True)
        video = request.json()['data']["View"]["pages"]
        title = request.json()['data']["View"]['title']
        pic = request.json()['data']["View"]['pic']
        total = len(video)
        count = 0
        for i in video:
            count += 1
            print(f"{count} / {total}")
            cid = i['cid']
            part_title = i['part']
            if not self.download_one(cid, pic, title=title, part_title=part_title, base_dir=base_dir):
                return False
        return True


class BiliBili:
    def __init__(self, quality=32):
        self.request_manager = request_manager
        self.quality = quality
        self.audio = 30280
        self.mid: int = self.request_manager.is_login()
        if self.mid:
            self.login_init(self.mid)
        self.login: bool = False if not self.mid else True
        self.login_init(self.mid)
        self.view_online_watch = True
        self.bilibili_favorite = BilibiliFavorite(self.mid)
        self.interaction: BilibiliInteraction = BilibiliInteraction(self.bilibili_favorite)
        self.manga = BilibiliManga()

    def favorite(self):
        if not self.login:
            print("请先登录!")
        fav_id = self.bilibili_favorite.choose_favorite(self.mid, one=True)
        all_request = self.bilibili_favorite.get_favorite(fav_id)
        for i in all_request:
            for num, item in enumerate(i):
                print(num + 1, ":")
                print("封面: ", item['cover'])
                print("标题: ", item['title'])
                print("作者: ", item['upper']['name'], " bvid: ", item['bvid'], " 日期: ",
                      datetime.datetime.fromtimestamp(
                          item['pubtime']).strftime("%Y-%m-%d %H:%M:%S"), " 视频时长:", format_time(item['duration']),
                      " 观看量: ",
                      item['cnt_info']['play'])
            while True:
                command = input("选择视频: ")
                if command == "exit":
                    return
                elif not command:
                    break
                elif not command.isdecimal():
                    print("输入的不是整数!")
                    continue
                elif int(command) > len(i) or int(command) <= 0:
                    print("选视频超出范围!")
                    continue
                bvid = i[int(command) - 1]['bvid']
                self.view_video(bvid, no_favorite=True)

    def recommend(self):
        print("推荐界面")
        while True:
            # no cache
            recommend_request = self.request_manager.get(
                "https://api.bilibili.com/x/web-interface/wbi/index/top/feed/rcmd?" + encrypt_wbi("ps=5"))
            print(recommend_request.url)
            for num, item in enumerate(recommend_request.json()['data']['item']):
                print(num + 1, ":")
                print("封面: ", item['pic'])
                print("标题: ", item['title'])
                print("作者: ", item['owner']['name'], " bvid: ", item['bvid'], " 日期: ",
                      datetime.datetime.fromtimestamp(
                          item['pubdate']).strftime("%Y-%m-%d %H:%M:%S"), " 视频时长:", format_time(item['duration']),
                      " 观看量: ",
                      item['stat']['view'])
            while True:
                command = input("选择视频: ")
                if command == "exit":
                    return
                elif not command:
                    break
                elif not command.isdecimal():
                    print("输入的不是整数!")
                    continue
                elif int(command) > len(recommend_request.json()['data']['item']) or int(command) <= 0:
                    print("选视频超出范围!")
                    continue
                bvid = recommend_request.json()['data']['item'][int(command) - 1]['bvid']
                mid = recommend_request.json()['data']['item'][int(command) - 1]['owner']['mid']
                # title = recommend_request.json()['data']['item'][int(command) - 1]['title']
                self.view_video(bvid, mid=mid)

    def address(self):
        video_address = input("输入地址: ")
        if "b23.tv" in video_address:
            video_address = self.request_manager.get(video_address).url

        url_split = video_address.split("/")
        if url_split[-1].startswith("?"):
            video_id = url_split[-2]
        else:
            video_id = url_split[-1].split("?")[0]
        if video_id.startswith("BV"):
            self.view_short_video_info(video_id)
            self.view_video(bvid=video_id)
        else:
            self.view_short_video_info(enc(int(video_id.strip("av"))))
            self.view_video(bvid=enc(int(video_id.strip("av"))))

    def view_short_video_info(self, bvid):
        video = self.request_manager.get("https://api.bilibili.com/x/web-interface/view/detail?bvid=" + bvid)
        item = video.json()['data']['View']
        print("封面: ", item['pic'])
        print("标题: ", item['title'])
        print("作者: ", item['owner']['name'], " bvid: ", item['bvid'], " 日期: ", datetime.datetime.fromtimestamp(
            item['pubdate']).strftime("%Y-%m-%d %H:%M:%S"), " 视频时长:", format_time(item['duration']), " 观看量: ",
              item['stat']['view'])

    def bangumi(self):
        while True:
            choose_bangumi = input("番剧选项: ")
            if choose_bangumi == "address":
                url = input("输入地址: ")
                self.play_bangumi_by_address(url)
            elif choose_bangumi == "exit":
                return
            else:
                print("未知选项!")

    def play_bangumi_by_address(self, url):
        ssid_or_epid = url.split("/")[-1]
        ssid_or_epid = ssid_or_epid.split("?")[0]
        if ssid_or_epid.startswith("ss"):
            url = "https://api.bilibili.com/pgc/view/web/season?season_id=" + \
                  ssid_or_epid.strip("ss")
        else:
            url = "https://api.bilibili.com/pgc/view/web/season?ep_id=" + \
                  ssid_or_epid.strip('ep')
        bangumi_url = self.request_manager.get(url)
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
            bvid = bangumi_page[int(page) - 1]['bvid']
            epid = bangumi_page[int(page) - 1]['id']
            title = bangumi_page[int(page) - 1]['share_copy']
            video = BiliBiliVideo(bvid=bvid, epid=epid, bangumi=True, quality=self.quality,
                                  view_online_watch=self.view_online_watch)
            video.play(cid, title=title)

    def get_danmaku(self, cid: int):
        resp = self.request_manager.get(
            "https://api.bilibili.com/x/v2/dm/web/seg.so?type=1&oid={}&segment_index=1".format(cid),
            cache=True)
        return resp.content

    # def play_interact_video(self, bvid: str, cid: int):
    #     self.play(bvid, cid, view_online_watch=False)
    #
    #     graph_version = self.request_manager.get(f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}")
    #     graph_version = graph_version.json()['data']['interaction']['graph_version']
    #
    #     edge_id = ""
    #
    #     while True:
    #         edge_info = f"https://api.bilibili.com/x/stein/edgeinfo_v2" \
    #                     f"?graph_version={graph_version}" \
    #                     f"&bvid={bvid}" \
    #                     f"&edge_id={edge_id}"
    #         r = self.request_manager.get(edge_info)
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
        if not self.login:
            print("请先登录!")
            return
        self.interaction.like(bvid, unlike=unlike)

    def coin(self, bvid):
        if not self.login:
            print("请先登录!")
            return
        coin_count = input("输入币数(1-2): ")
        if coin_count != "1" and coin_count != "2":
            print("币数错误!")
            return
        self.interaction.coin(bvid, int(coin_count))

    def triple(self, bvid):
        if not self.login:
            print("请先登录!")
            return
        self.interaction.triple(bvid)

    def add_favorite(self, avid):
        if not self.login:
            print("请先登录!")
            return
        self.interaction.favorite_video(avid, self.bilibili_favorite.choose_favorite(self.bilibili_favorite.mid, avid))

    def download_favorite(self):
        fav_id = self.bilibili_favorite.choose_favorite(self.mid, one=True)
        info = self.bilibili_favorite.get_favorite_information(fav_id)
        count = 0
        total = info['media_count']
        for i in self.bilibili_favorite.get_favorite(fav_id):
            for j in i:
                count += 1
                print(f"收藏夹进度: {count} / {total}")
                video = BiliBiliVideo(bvid=j['bvid'], quality=80)
                if not video.download_video_list(base_dir=validate_title(info['title'])):
                    return

    def download_manga(self):
        print("漫画id: 即 https://manga.bilibili.com/detail/mc29410 中的 29410")
        try:
            comic_id = input("请输入漫画id或url: ")
            if comic_id.startswith("https"):
                comic_id = comic_id.split("mc")[1]
            self.manga.download_manga(comic_id)
        except (ValueError, IndexError):
            print("id输入错误.")
        except KeyboardInterrupt:
            print("停止下载.")

    def export_favorite(self):
        fav_id = self.bilibili_favorite.choose_favorite(self.mid, one=True)
        self.bilibili_favorite.export_favorite(fav_id)

    def export_all_favorite(self):
        fav_id = self.bilibili_favorite.list_favorite(self.mid)
        for i in fav_id:
            self.bilibili_favorite.export_favorite(i)

    def login_init(self, mid):
        self.quality = 80
        self.login = True
        self.mid = mid
        self.bilibili_favorite = BilibiliFavorite(self.mid)
        self.interaction: BilibiliInteraction = BilibiliInteraction(self.bilibili_favorite)
        self.manga = BilibiliManga()

    def view_video(self, bvid, mid=0, no_favorite=False):
        video = BiliBiliVideo(bvid=bvid, quality=self.quality, view_online_watch=self.view_online_watch)
        while True:
            command = input("视频选项: ")
            if command == "exit":
                return
            if command == "play":
                video.choose_video()
            elif command == "download":
                cid, title, part_title, pic, is_dynamic = video.choose_video(return_information=True)
                print(is_dynamic)
                if is_dynamic:
                    print("互动视频无法下载! ")
                    return
                video.download_one(cid, pic_url=pic, title=title, part_title=part_title)
            elif command == "download_video_list":
                video.download_video_list(bvid)
            elif command == "like":
                self.like(bvid)
            elif command == "unlike":
                self.like(bvid, unlike=True)
            elif command == "coin":
                self.coin(bvid)
            elif command == 'triple':
                self.triple(bvid)
            elif command == "favorite" and not no_favorite:
                self.add_favorite(dec(bvid))
                self.request_manager.cached_response = {}
            elif command == "view_user":
                self.user_space(mid)
            elif command:
                print("未知命令!")

    def main(self):
        while True:
            command = input("主选项: ")
            command = command.lower().strip()
            if command == "recommend":
                self.recommend()
            elif command == "address":
                self.address()
            elif command == "bangumi":
                self.bangumi()
            elif command == "favorite":
                self.favorite()
            elif command == "exit":
                sys.exit(0)
            elif command == "enable_online_watching":
                self.view_online_watch = True
            elif command == "disable_online_watching":
                self.view_online_watch = False
            elif command == "clean_cache":
                shutil.rmtree("cached")
                os.mkdir("cached")
            elif command == "refresh_login_state":
                mid = self.request_manager.refresh_login_state()
                if mid:
                    self.login_init(mid)
            elif command == "export_favorite":
                self.export_favorite()
            elif command == "export_all_favorite":
                self.export_all_favorite()
            elif command == "download_favorite":
                self.download_favorite()
            elif command == "view_self":
                if self.login:
                    self.user_space(self.mid)
                else:
                    print("用户未登录!")
            elif command == "view_user":
                self.user_space(int(input("请输入用户mid: ")))
            elif command == "download_manga":
                self.download_manga()
            elif command:
                print("未知命令!")

    def user_space(self, mid: int):
        user_info = self.request_manager.get("https://api.bilibili.com/x/space/wbi/acc/info?mid=" + str(mid))
        user_data = user_info.json()['data']
        print("用户空间")
        print("")
        print("用户名: " + user_data['name'])
        print("头像: " + user_data['face'])
        print("Level: " + str(user_data['level']) + (" 硬核会员" if user_data['is_senior_member'] == 1 else ""))
        print("个性签名: " + user_data['sign'])
        print("")
        while True:
            command = input("用户空间选项: ")
            if command == "list_video":
                self.list_user_video(mid)
            elif command == "exit":
                return
            elif command:
                print("未知命令!")

    def list_user_video(self, mid: int):
        pre_page = 5
        cursor = 1
        user_info = self.request_manager.get(f"https://api.bilibili.com/x/space/wbi/arc/search?mid={mid}&ps=5")
        total = user_info.json()['data']['page']['count'] // pre_page + 1
        while True:
            ls = self.request_manager.get(
                f"https://api.bilibili.com/x/space/wbi/arc/search?mid={mid}&ps=5&pn={cursor}", cache=True)
            if total < cursor:
                break
            if len(ls.json()['data']['list']['vlist']) == 0:
                print("该用户未发送视频!")
                return
            for num, item in enumerate(ls.json()['data']['list']['vlist']):
                print(num + 1, ":")
                print("封面: ", item['pic'])
                print("标题: ", item['title'])
                print("作者: ", item['author'], " bvid: ", item['bvid'], " 日期: ",
                      datetime.datetime.fromtimestamp(
                          item['created']).strftime("%Y-%m-%d %H:%M:%S"), " 视频时长:", item['length'],
                      " 观看量: ",
                      item['play'])
            while True:
                command = input("选择视频: ")
                if command == "exit":
                    return
                if not command:
                    break
                elif not command.isdecimal():
                    print("输入的不是整数!")
                    continue
                elif int(command) > len(ls.json()['data']['list']['vlist']) or int(command) <= 0:
                    print("选视频超出范围!")
                    continue
                bvid = ls.json()['data']['list']['vlist'][int(command) - 1]['bvid']
                self.view_video(bvid, mid=mid)
            cursor += 1


print(f"LBCC v{__version__}.")
print()

if __name__ == '__main__':
    bilibili = BiliBili()
    bilibili.main()
