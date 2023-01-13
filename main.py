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
import shutil
import subprocess
import sys
import time
import traceback

import requests
from tqdm import tqdm

from bilibili.biliass import Danmaku2ASS
from bilibili.utils import enc, dec, format_time, validateTitle, read_cookie, convert_cookies_to_dict, clean_cookie


class RequestManager:
    def __init__(self, cookie):
        self.cached_response: dict[str, requests.Response] = {}
        # self.cookie = cookie
        self.session = requests.session()
        self.session.headers.update(
            {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
             "referer": "https://www.bilibili.com"})
        self.session.headers.update({"cookie": cookie})

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
            return True
        else:
            raise Exception("Invalid login code: " + str(r.json()['code']))

    def get_local_user_mid(self) -> int:
        r = self.session.get('https://api.bilibili.com/x/member/web/account')
        return r.json()['data']['mid']


class BilibiliFavorite:
    def __init__(self, session: requests.Session):
        self.session = session

    def favorite(self, avid):
        pass


class BilibiliVideo:
    def __init__(self, avid: int = 0, bvid: str = ""):
        self.avid = avid if avid else dec(bvid)
        self.bvid = bvid if bvid else enc(avid)

    # TODO: Write play outside
    def play(self, page):
        pass

    # TODO: Write choose video outside
    def choose_video(self):
        pass


class BilibiliInteraction:
    def __init__(self, session: requests.Session):
        self.session: requests.Session = session
        self.csrf: str = clean_cookie(convert_cookies_to_dict(session.headers.get("cookie"))).get("bili_jct", "")

    def like(self, bvid: str, unlike=False):
        r = self.session.post("https://api.bilibili.com/x/web-interface/archive/like",
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
        r = self.session.post("https://api.bilibili.com/x/web-interface/coin/add",
                              data={"bvid": bvid, 'csrf': self.csrf, 'multiply': count})
        if r.json()['code'] == 0:
            print("投币成功!")
        else:
            print("投币失败!")
            print(f"错误信息: {r.json()['message']}")

    def triple(self, bvid: str):
        r = self.session.post("https://api.bilibili.com/x/web-interface/archive/like/triple",
                              data={"bvid": bvid, "csrf": self.csrf})
        if r.json()['code'] == 0:
            print("三联成功!")
        else:
            print("三联失败!")
            print(f"错误信息: {r.json()['message']}")

    # TODO: Write favorite to video.
    def favorite(self, avid):
        pass
        # https://api.bilibili.com/x/v3/fav/folder/created/list-all?type=2&rid=691183515&up_mid=450196722&jsonp=jsonp&callback=jsonCallback_bili_185514247489901420


class BiliBili:
    def __init__(self, quality=32):
        self.request_manager = RequestManager(read_cookie())
        self.interaction: BilibiliInteraction = BilibiliInteraction(self.request_manager.session)
        self.quality = quality
        self.audio = 30280
        self.codecs = "avc"
        self.login: bool = False
        self.mid: int = 0
        self.view_online_watch = True

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
            self.play(bvid=epid, cid=cid, bangumi=True, bangumi_bvid=bvid, title=title)

    def get_danmaku(self, cid):
        resp = self.request_manager.get(
            "https://api.bilibili.com/x/v2/dm/web/seg.so?type=1&oid={}&segment_index=1".format(cid),
            cache=True)
        return resp.content

    def choose_video(self, bvid, cid_mode=False):
        url = "https://api.bilibili.com/x/web-interface/view/detail?bvid=" + bvid
        # cache
        r = self.request_manager.get(url, cache=True)
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
                self.play(bvid, video[int(page) - 1]['cid'], title)
            else:
                return video[int(page) - 1]['cid'], title, video[int(page) - 1]['part'], pic
            break
        return

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

    def play(self, bvid, cid, title="", bangumi=False, bangumi_bvid=""):
        if bangumi:
            url = f"https://api.bilibili.com/pgc/player/web/playurl?cid={cid}&fnval=16&qn={self.quality}"
        else:
            url = f"https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={bvid}&fnval=16"
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
        if self.view_online_watch:
            try:
                while p.poll() is None:
                    if bangumi:
                        people_watching = self.request_manager.get(
                            f"https://api.bilibili.com/x/player/online/total?cid={cid}&bvid={bangumi_bvid}")
                    else:
                        people_watching = self.request_manager.get(
                            f"https://api.bilibili.com/x/player/online/total?cid={cid}&bvid={bvid}")
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

    def login_init(self):
        self.quality = 80
        self.login = True
        self.interaction = BilibiliInteraction(self.request_manager.session)

    def view_video(self, bvid):
        while True:
            command = input("视频选项: ")
            if not command:
                return
            elif command == "play":
                self.choose_video(bvid)
            elif command == "download":
                cid, title, part_title, pic = self.choose_video(bvid, cid_mode=True)
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
            else:
                print("未知命令!")

    def main(self):
        if self.request_manager.is_login():
            self.login_init()
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
            elif command == "refresh_login_state":
                if self.request_manager.refresh_login_state():
                    self.login_init()
            elif command == "clean_cache":
                shutil.rmtree("cached")
                os.mkdir("cached")
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
