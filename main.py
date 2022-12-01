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
import os
import subprocess
import sys
import time

import requests
from requests.utils import dict_from_cookiejar

from bilibili.biliass import Danmaku2ASS
from bilibili.utils import format_time

headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
           "referer": "https://www.bilibili.com"}

if os.path.exists("cookie.txt"):
    with open("cookie.txt") as f:
        cookie = f.read()
else:
    b = requests.get("https://www.bilibili.com", headers=headers)
    cookie = ''
    for i, j in dict_from_cookiejar(b.cookies).items():
        cookie += "{}={};".format(i, j)
    cookie = cookie[:-1]


class BiliBili:
    def __init__(self, quality=32):
        self.cached_response = {}
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.session.headers.update({"cookie": cookie})
        self.quality = quality
        self.audio = 30280
        self.codecs = "avc"
        self.login = False

    def recommend(self):
        print("推荐界面")
        while True:
            # no cache
            recommend_request = self.get("https://api.bilibili.com/x/web-interface/index/top/feed/rcmd?ps=5")
            for num, item in enumerate(recommend_request.json()['data']['item']):
                print(num + 1, ":")
                print("封面: ", item['pic'])
                print("标题: ", item['title'])
                print("作者: ", item['owner']['name'], " bvid: ", item['bvid'], " 日期: ", datetime.datetime.fromtimestamp(
                    item['pubdate']).strftime("%Y-%m-%d %H:%M:%S"), " 视频时长:", format_time(item['duration']), " 观看量: ",
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
                avid = recommend_request.json()['data']['item'][int(command) - 1]['id']
                title = recommend_request.json()['data']['item'][int(command) - 1]['title']
                self.view_video(avid, bvid, title)

    def view_video(self, avid, bvid, title):
        while True:
            command = input("视频选项: ")
            if not command:
                return
            elif command == "play":
                self.choose_video(bvid, title=title, bvid=True)
            else:
                print("未知命令!")

    def main(self):
        self.is_login()
        self.recommend()

    def get_danmaku(self, cid):
        params = {
            'type': '1',
            'oid': cid,
            'segment_index': '1'
        }
        # cache
        resp = self.get("https://api.bilibili.com/x/v2/dm/web/seg.so", params=params, cache=True)
        return resp.content

    def choose_video(self, video_id, bvid=True, title=""):
        print("\n")
        print("视频选集")
        if bvid:
            url = "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + video_id
        else:
            url = "https://api.bilibili.com/x/web-interface/view/detail?aid=" + video_id
        # cache
        r = self.get(url, cache=True)
        video = r.json()['data']["View"]["pages"]
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
            self.play(video_id, video[int(page) - 1]['cid'], bvid, title)
            break
        return

    def play(self, video_id, cid, bvid=True, title="", danmaku=False, width=0, height=0):
        # width height 参数用于bangumi
        if danmaku:
            # danmaku 不需video_id, bvid
            url = f"https://api.bilibili.com/pgc/player/web/playurl?cid={cid}&fnval=16&qn={self.quality}"
        else:
            if bvid:
                url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={video_id}&fnval=16"
            else:
                url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&avid={video_id}&fnval=16"
        # cache
        play_url_request = self.get(url, cache=True)
        if not danmaku:
            videos = play_url_request.json()['data']['dash']["video"]
            audios = play_url_request.json()['data']['dash']["audio"]

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
        else:
            video_url = play_url_request.json()['result']['durl'][0]['url']
            audio_url = video_url
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
        p = subprocess.Popen(command, shell=True)
        while p.poll() is None:
            if bvid:
                people_watching = self.get(f"https://api.bilibili.com/x/player/online/total?cid={cid}&bvid={video_id}")
            else:
                people_watching = self.get(f"https://api.bilibili.com/x/player/online/total?cid={cid}&aid={video_id}")
            people = f"\r{people_watching.json()['data']['total']} 人正在看"
            print(people, end="", flush=True)
            time.sleep(2)
        print("\n")

    def is_login(self):
        # no cache
        r = self.get('https://api.bilibili.com/x/member/web/account')
        if r.json()['code'] == -101:
            return False
        elif r.json()['code'] == 0:
            # 登录才可使用32 80分辨率 大会员分辨率暂不支持
            self.quality = 80
            return True
        else:
            return None

    def get(self, url: str, params=None, cache=False, **kwargs) -> requests.Response:
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
            if cache:
                self.cached_response[url] = r
            return r


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
