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
import traceback

import requests
from requests.utils import dict_from_cookiejar
from tqdm import tqdm

from bilibili.biliass import Danmaku2ASS
from bilibili.utils import format_time, validateTitle, enc

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
        self.view_online_watch = True

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
                # title = recommend_request.json()['data']['item'][int(command) - 1]['title']
                self.view_video(bvid)

    def address(self):
        video_address = input("输入地址: ")
        if "b23.tv" in video_address:
            video_address = requests.get(video_address, headers=headers).url
        url_split = video_address.split("/")
        if url_split[-1].startswith("?"):
            video_id = url_split[-2]
        else:
            video_id = url_split[-1].split("?")[0]
        if video_id.startswith("BV"):
            self.view_video(bvid=video_id)
        else:
            self.view_video(bvid=enc(int(video_id.strip("av"))))

    def view_video(self, bvid):
        while True:
            command = input("视频选项: ")
            if not command:
                return
            elif command == "play":
                self.choose_video(bvid, bvid=True)
            elif command == "download":
                cid, title, part_title, pic = self.choose_video(bvid, bvid=True, cid_mode=True)
                self.download_one(bvid, cid, pic_url=pic, title=title, part_title=part_title)
            else:
                print("未知命令!")

    def main(self):
        self.is_login()
        while True:
            command = input("主选项: ")
            command = command.lower().strip()
            if command == "recommend":
                self.recommend()
            elif command == "address":
                self.address()
            elif command == "bangumi":
                self.bangumi()
            elif command == "exit":
                sys.exit(0)
            elif command == "enable_online_watching":
                self.view_online_watch = True
            elif command == "disable_online_watching":
                self.view_online_watch = False
            else:
                print("未知命令!")

    def bangumi(self):
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
                bangumi_url = self.get(url)
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
            elif choose_bangumi == "exit":
                return

    def get_danmaku(self, cid):
        resp = self.get("https://api.bilibili.com/x/v2/dm/web/seg.so?type=1&oid={}&segment_index=1".format(cid),
                        cache=True)
        return resp.content

    def choose_video(self, video_id, bvid=True, cid_mode=False):
        if bvid:
            url = "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + video_id
        else:
            url = "https://api.bilibili.com/x/web-interface/view/detail?aid=" + video_id
        # cache
        r = self.get(url, cache=True)
        if r.json()['code'] != 0:
            print("获取视频信息错误!")
            print(r.json()['code'])
            print(r.json()['message'])
            return
        print("\n")
        print("视频选集")
        video = r.json()['data']["View"]["pages"]
        title = r.json()['data']["View"]['title']
        pic = r.json()['data']["View"]['pic']
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
                self.play(video_id, video[int(page) - 1]['cid'], bvid, title)
            else:
                return video[int(page) - 1]['cid'], title, video[int(page) - 1]['part'], pic
            break
        return

    def play(self, video_id, cid, bvid=True, title="", bangumi=False, bangumi_bvid=""):
        if bangumi:
            url = f"https://api.bilibili.com/pgc/player/web/playurl?cid={cid}&fnval=16&qn={self.quality}"
        else:
            if bvid:
                url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={video_id}&fnval=16"
            else:
                url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&avid={video_id}&fnval=16"
        # cache
        play_url_request = self.get(url, cache=True)

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
        if self.view_online_watch:
            try:
                while p.poll() is None:
                    if bangumi:
                        people_watching = self.get(
                            f"https://api.bilibili.com/x/player/online/total?cid={cid}&bvid={bangumi_bvid}")
                    else:
                        if bvid:
                            people_watching = self.get(
                                f"https://api.bilibili.com/x/player/online/total?cid={cid}&bvid={video_id}")
                        else:
                            people_watching = self.get(
                                f"https://api.bilibili.com/x/player/online/total?cid={cid}&aid={video_id}")
                    people = f"\r{people_watching.json()['data']['total']} 人正在看"
                    print(people, end="", flush=True)
                    time.sleep(3)
            except (TypeError, requests.exceptions.RequestException) as e:
                print("获取观看人数时发生错误!")
                print(traceback.print_exc())
        print("\n")

    def download_one(self, video_id, cid, pic_url, bvid=True, bangumi=False, title="", part_title=""):
        if not bangumi:
            if bvid:
                url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn={self.quality}&ty" \
                      f"pe=&otype=json&bvid={video_id}"
            else:
                url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn={self.quality}&type=&oty" \
                      f"pe=json&avid={video_id}"
        else:
            url = f"https://api.bilibili.com/pgc/player/web/playurl?qn={self.quality}&cid={cid}&ep_id={video_id}"

        req = self.get(url)
        download_url = req.json()["data" if not bangumi else "result"]["durl"][0]["url"]

        res = self.get(download_url, stream=True)
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
                return
        file = open(dts, 'wb')
        progress = tqdm(total=length, initial=os.path.getsize(dts), unit_scale=True,
                        desc=validateTitle(part_title) + ".mp4", unit="B")
        try:
            for chuck in res.iter_content(chunk_size=1000):
                file.write(chuck)
                progress.update(1000)
        except KeyboardInterrupt:
            file.close()
            os.remove(dts)
            if len(os.listdir("download/" + validateTitle(title))) == 0:
                os.rmdir("download/" + validateTitle(title))
            print("取消下载.")
            return
        if not file.closed:
            file.close()
        print("下载封面中...")
        with open("download/" + validateTitle(title) + "/" + validateTitle(part_title) + ".jpg", "wb") as file:
            file.write(self.get(pic_url).content)
        print("下载弹幕中...")
        with open("download/" + validateTitle(title) + "/" + validateTitle(part_title) + ".xml", "w") as file:
            file.write(self.get(f"https://comment.bilibili.com/{cid}.xml").content.decode("utf-8"))

    def is_login(self):
        # no cache
        r = self.get('https://api.bilibili.com/x/member/web/account')
        if r.json()['code'] == -101:
            print("账号尚未登录.")
            print("")
            return False
        elif r.json()['code'] == 0:
            print("账号已登录.")
            print("")
            # 登录才可使用32 80分辨率 大会员分辨率暂不支持
            self.quality = 80
            return True
        else:
            return None

    def get(self, url: str, params=None, cache=False, **kwargs) -> requests.Response:
        if self.cached_response.get(url):
            return self.cached_response.get(url)
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
