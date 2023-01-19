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
import shutil
import subprocess
import sys
import time
import traceback

import requests
from tqdm import tqdm

from bilibili.biliass import Danmaku2ASS
from bilibili.utils import enc, format_time, validateTitle, read_cookie, convert_cookies_to_dict, clean_cookie, dec


class RequestManager:
    __instance = None
    __first = True

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, cookie=""):
        if self.__first:
            self.cached_response: dict[str, requests.Response] = {}
            self.session = requests.session()
            self.session.headers.update(
                {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
                 "referer": "https://www.bilibili.com"})
            self.session.headers.update({"cookie": cookie})
            self.__class__.__first = False

    def get(self, url: str, params=None, cache=False, **kwargs) -> requests.Response:
        if self.cached_response.get(url):
            return self.cached_response.get(url)  # type: ignore
        else:
            count = 5
            while True:
                try:
                    r = self.session.get(url, params=params, timeout=5, **kwargs)
                    break
                except requests.exceptions.RequestException as request_error:
                    print("\n")
                    print(f"{url}请求错误! 将会重试{count}次! ")
                    count -= 1
                    if count <= 0:
                        raise request_error
            if cache:
                self.cached_response[url] = r
            return r

    def post(self, url: str, params=None, **kwargs) -> requests.Response:
        count = 5
        while True:
            try:
                r = self.session.post(url, params=params, timeout=5, **kwargs)
                break
            except requests.exceptions.RequestException as request_error:
                print("\n")
                print(f"{url}请求错误! 将会重试{count}次! ")
                count -= 1
                if count <= 0:
                    raise request_error
        return r

    def refresh_login_state(self):
        if os.path.exists("cookie.txt"):
            with open("cookie.txt") as f:
                cookie = f.read()
        self.session.headers['cookie'] = cookie
        print("刷新登录状态成功.")
        return self.is_login()

    def is_login(self) -> bool:
        r = self.session.get('https://api.bilibili.com/x/member/web/account')
        if r.json()['code'] == -101:
            print("账号尚未登录.")
            print()
            return False
        elif r.json()['code'] == 0:
            print("账号已登录.")
            print(f"欢迎{r.json()['data']['uname']}登录.")
            print()
            return r.json()['data']['mid']
        else:
            raise Exception("Invalid login code: " + str(r.json()['code']))

    def get_local_user_mid(self) -> int:
        r = self.session.get('https://api.bilibili.com/x/member/web/account')
        return r.json()['data']['mid']


class BilibiliFavorite:
    def __init__(self, mid: int):
        self.request_manager = RequestManager()
        self.mid = mid

    def choose_favorite(self, mid, avid: int = 0, one=False):
        r = self.request_manager.get(
            f"https://api.bilibili.com/x/v3/fav/folder/created/list-all?type=2&rid={avid}&up_mid={mid}", cache=True)
        print("\n")
        print("选择收藏夹")
        for index, item in enumerate(r.json()['data']['list']):
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
                    if r.json()['data']['list'][int(item) - 1]['fav_state']:
                        print(f"索引{index + 1} Warning: 此收藏夹已收藏过该视频, 将不会重复收藏.")
                    try:
                        ids.append(r.json()['data']['list'][int(item) - 1]['id'])
                    except IndexError:
                        print(f"索引{index + 1} Error: 索引超出收藏夹范围!")
                return ids
            else:
                choose = input("选择收藏夹: ")
                if not choose.isdecimal():
                    print(f"索引{index + 1} Error: 输入的必须为数字!")
                    continue
                try:
                    return r.json()['data']['list'][int(choose) - 1]['id']
                except IndexError:
                    print("Error: 索引超出收藏夹范围!")

    def get_favorite(self, fav_id: int):
        pre_page = 5
        cursor = 1
        r = self.request_manager.get("https://api.bilibili.com/x/v3/fav/resource/list?ps=20&media_id=" + str(fav_id),
                                     cache=True)
        total = r.json()['data']['info']['media_count'] // pre_page + 1
        while True:
            ls = self.request_manager.get(
                f"https://api.bilibili.com/x/v3/fav/resource/list?ps=5&media_id={fav_id}&pn={cursor}", cache=True)
            if total < cursor:
                break
            yield ls.json()['data']['medias']
            cursor += 1

    def export_favorite(self, fav_id: int):
        pre_page = 5
        cursor = 1
        r = self.request_manager.get("https://api.bilibili.com/x/v3/fav/resource/list?ps=20&media_id=" + str(fav_id))
        total = r.json()['data']['info']['media_count'] // pre_page + 1
        print("正在导出收藏夹" + r.json()['data']['info']['upper']['name'] + ".")
        export = {
            "id": r.json()['data']['info']['id'],
            "media_count": r.json()['data']['info']['media_count'],
            "title": r.json()['data']['info']['title'],
            "cover": r.json()['data']['info']['cover'],
            "create_user": {
                "name": r.json()['data']['info']['upper']['name'],
                "mid": r.json()['data']['info']['upper']['mid'],
                "time": r.json()['data']['info']['mtime'],
            },
            "medias": []
        }
        while True:
            if total < cursor:
                break
            export['medias'] += self.request_manager.get(
                f"https://api.bilibili.com/x/v3/fav/resource/list?ps=5&media_id={fav_id}&pn={cursor}").json()['data'][
                'medias']
            cursor += 1
        with open(str(fav_id) + '.json', "w", encoding="utf-8") as f:
            json.dump(export, f)
        print(f"导出收藏夹{r.json()['data']['info']['upper']['name']}成功.")


class BilibiliInteraction:
    def __init__(self, favorite: BilibiliFavorite):
        self.request_manager = RequestManager()
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


class BiliBili:
    def __init__(self, quality=32):
        self.request_manager = RequestManager(read_cookie())
        self.quality = quality
        self.audio = 30280
        self.codecs = "avc"
        self.login: bool = False
        self.mid: int = 0
        self.view_online_watch = True
        self.bilibili_favorite = BilibiliFavorite(self.mid)
        self.interaction: BilibiliInteraction = BilibiliInteraction(self.bilibili_favorite)

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
                "https://api.bilibili.com/x/web-interface/wbi/index/top/feed/rcmd?ps=5")
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
                # title = recommend_request.json()['data']['item'][int(command) - 1]['title']
                self.view_video(bvid)

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
            self.play(video_id=epid, cid=cid, bangumi=True, bangumi_bvid=bvid, title=title)

    def get_danmaku(self, cid):
        resp = self.request_manager.get(
            "https://api.bilibili.com/x/v2/dm/web/seg.so?type=1&oid={}&segment_index=1".format(cid),
            cache=True)
        return resp.content

    def play_interact_video(self, bvid, cid):
        self.play(bvid, cid, view_online_watch=False)

        graph_version = self.request_manager.get(f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}")
        graph_version = graph_version.json()['data']['interaction']['graph_version']

        edge_id = ""

        while True:
            edge_info = f"https://api.bilibili.com/x/stein/edgeinfo_v2" \
                        f"?graph_version={graph_version}" \
                        f"&bvid={bvid}" \
                        f"&edge_id={edge_id}"
            r = self.request_manager.get(edge_info)
            if not r.json()['data']['edges'].get('questions'):
                print("互动视频已到达末尾.")
                score = input("是否评分? (y/n): ")
                if score == "y":
                    score = input("评几分? (1-5): ")
                    if not score.isdecimal():
                        print("输入错误! 将停止评分")
                        return
                    self.interaction.mark_interact_video(bvid, int(score))
                break
            for i, j in enumerate(r.json()['data']['edges']['questions'][0]['choices']):
                print(f"{i + 1}: {j['option']}")
            while True:
                index = input("选择选项: ")
                if index.isdecimal():
                    break
                else:
                    print("请输入数字!")
            edge_id = r.json()['data']['edges']['questions'][0]['choices'][int(index) + 1]['id']
            cid = r.json()['data']['edges']['questions'][0]['choices'][int(index) + 1]['cid']
            self.play(bvid, cid, view_online_watch=False)

    def choose_video(self, bvid, cid_mode=False):
        url = "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + bvid
        # cache
        r = self.request_manager.get(url, cache=True)
        if r.json()['code'] != 0:
            print("获取视频信息错误!")
            print(r.json()['code'])
            print(r.json()['message'])
            return
        if r.json()['data']["View"]['stat']['evaluation']:
            print("你播放的视频是一个互动视频.")
            base_cid = r.json()['data']["View"]['cid']
            self.play_interact_video(bvid, base_cid)
            return
        video = r.json()['data']["View"]["pages"]
        title = r.json()['data']["View"]['title']
        pic = r.json()['data']["View"]['pic']
        if len(video) == 1:
            if not cid_mode:
                self.play(bvid, video[0]['cid'], title)
                return
            else:
                return video[0]['cid'], title, video[0]['part'], pic, True if \
                    r.json()['data']["View"]['dynamic'] \
                    else False
        print("\n")
        print("视频选集")
        for i in video:
            print(f"{i['page']}: {i['part']}")
        print("请以冒号前面的数字为准选择视频.")
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
            if not cid_mode:
                self.play(bvid, video[int(page) - 1]['cid'], title)
            else:
                return video[int(page) - 1]['cid'], title, video[int(page) - 1]['part'], pic, True if \
                    r.json()['data']["View"]['dynamic'] \
                    else False
            break

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
        print(self.bilibili_favorite.choose_favorite(self.bilibili_favorite.mid, avid))

    def play(self, video_id, cid, title="", bangumi=False, bangumi_bvid="", view_online_watch=True):
        """
        播放视频
        :param video_id: bvid, epid or ssid
        :param cid: cid
        :param title: video title
        :param bangumi: is bangumi
        :param bangumi_bvid: bangumi 's bvid
        :param view_online_watch: is view online watch
        :return: None
        """
        if bangumi:
            url = f"https://api.bilibili.com/pgc/player/web/playurl?cid={cid}&fnval=16&qn={self.quality}"
        else:
            url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={video_id}&fnval=16"
        # cache
        play_url_request = self.request_manager.get(url, cache=True)

        if not bangumi:
            videos = play_url_request.json()['data']['dash']["video"]
            audios = play_url_request.json()['data']['dash']["audio"]
        else:
            videos = play_url_request.json()['result']['dash']["video"]
            audios = play_url_request.json()['result']['dash']["audio"]

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
            audio_url = audio_mapping[self.audio]
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
        if not os.path.exists("cached"):
            os.mkdir("cached")
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
        p = subprocess.Popen(command, shell=True)
        if self.view_online_watch and view_online_watch:
            try:
                while p.poll() is None:
                    people_watching = self.request_manager.get(
                        f"https://api.bilibili.com/x/player/online/total?cid={cid}&bvid={video_id if not bangumi else bangumi_bvid}")
                    people = f"\r{people_watching.json()['data']['total']} 人正在看"
                    print(people, end="", flush=True)
                    time.sleep(3)
            except (TypeError, requests.exceptions.RequestException):
                print("获取观看人数时发生错误!")
                traceback.print_exc()
            except KeyboardInterrupt:
                return
        print("\n")

    def download_one(self, bvid, cid, pic_url, bangumi=False, title="", part_title=""):
        if not bangumi:
            url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn={self.quality}&bvid={bvid}"
        else:
            url = f"https://api.bilibili.com/pgc/player/web/playurl?qn={self.quality}&cid={cid}&ep_id={bvid}"

        req = self.request_manager.get(url)
        download_url = req.json()["data" if not bangumi else "result"]["durl"][0]["url"]

        res = self.request_manager.get(download_url, stream=True)
        length = float(res.headers['content-length'])
        if not os.path.exists("download"):
            os.mkdir("download")
        if not os.path.exists("download/" + validateTitle(title)):
            os.mkdir("download/" + validateTitle(title))
        dts = "download/" + validateTitle(title) + "/" + validateTitle(part_title) + ".mp4"
        if os.path.exists(dts):
            c = input("文件已存在, 是否覆盖(y/n)? ")
            if c != "y":
                print("停止操作.")
                return -100
        file = open(dts, 'wb')
        progress = tqdm(total=length, initial=os.path.getsize(dts), unit_scale=True,
                        desc=validateTitle(part_title) + ".mp4", unit="B")
        try:
            for chuck in res.iter_content(chunk_size=1024):
                file.write(chuck)
                progress.update(1024)
        except KeyboardInterrupt:
            file.close()
            os.remove(dts)
            if len(os.listdir("download/" + validateTitle(title))) == 0:
                os.rmdir("download/" + validateTitle(title))
            print("取消下载.")
            return False
        if not file.closed:
            file.close()
        if not os.path.exists("download/" + validateTitle(title) + "/" + validateTitle(title) + ".jpg"):
            print("下载封面中...")
            with open("download/" + validateTitle(title) + "/" + validateTitle(title) + ".jpg", "wb") as file:
                file.write(self.request_manager.get(pic_url).content)
        if not os.path.exists("download/" + validateTitle(title) + "/" + validateTitle(part_title) + ".xml"):
            print("下载弹幕中...")
            with open("download/" + validateTitle(title) + "/" + validateTitle(part_title) + ".xml", "w",
                      encoding="utf-8") as danmaku:
                danmaku.write(
                    self.request_manager.get(f"https://comment.bilibili.com/{cid}.xml").content.decode("utf-8"))
        return True

    def download_video_list(self, bvid):
        url = "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + bvid
        r = self.request_manager.get(url, cache=True)
        video = r.json()['data']["View"]["pages"]
        title = r.json()['data']["View"]['title']
        pic = r.json()['data']["View"]['pic']
        total = len(video)
        count = 0
        for i in video:
            count += 1
            print(f"{count} / {total}")
            cid = i['cid']
            part_title = i['part']
            if not self.download_one(bvid, cid, pic, title=title, part_title=part_title):
                break

    def login_init(self, mid):
        self.quality = 80
        self.login = True
        self.mid = mid
        self.bilibili_favorite = BilibiliFavorite(self.mid)
        self.interaction: BilibiliInteraction = BilibiliInteraction(self.bilibili_favorite)

    def view_video(self, bvid, no_favorite=False):
        while True:
            command = input("视频选项: ")
            if not command:
                return
            elif command == "play":
                self.choose_video(bvid)
            elif command == "download":
                cid, title, part_title, pic, is_dynamic = self.choose_video(bvid, cid_mode=True)
                if is_dynamic:
                    print("互动视频无法下载! ")
                    return
                self.download_one(bvid, cid, pic_url=pic, title=title, part_title=part_title)
            elif command == "download_video_list":
                self.download_video_list(bvid)
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
            else:
                print("未知命令!")

    def main(self):
        mid = self.request_manager.is_login()
        if mid:
            self.login_init(mid)
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
