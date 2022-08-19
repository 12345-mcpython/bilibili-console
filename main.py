"""import random

_1 = 0
_2 = 0

for i in range(10000000):
    a = random.randint(1,2)
    if a == 1:
        _1 += 1
    else:
        _2 += 2
print(_1 > _2)"""
import shutil

import requests

from bs4 import BeautifulSoup

import os
from danmaku2ass import Danmaku2ASS


def check_av_or_bv(av_or_bv: str):
    try:
        int(av_or_bv)
        return True
    except:
        return False


def like(av_or_bv: str, unlike=False):
    data = {}
    IS_AV = check_av_or_bv(av_or_bv)
    if IS_AV:
        data["aid"] = av_or_bv
    else:
        data['bvid'] = av_or_bv
    if not unlike:
        data['like'] = 1
    else:
        data['like'] = 2
    data['csrf'] = csrf_token
    r = post("http://api.bilibili.com/x/web-interface/archive/like", data=data, headers=public_header)
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


def get(url: str, params=None, no_cache=False, **kwargs) -> requests.Response:
    if cached.get(url):
        return cached.get(url)
    else:
        count = 3
        while True:
            try:
                r = requests.get(url, params=params, **kwargs)
                break
            except requests.exceptions.RequestException as e:
                print(f"Request {url} error! Will try {count} counts!")
                count -= 1
                if count <= 0:
                    print("Request error!")
                    raise e
        if not no_cache:
            cached[url] = r
        return r


def post(url: str, params=None, **kwargs) -> requests.Response:
    count = 3
    while True:
        try:
            r = requests.post(url, params=params, **kwargs)
            break
        except requests.exceptions.RequestException as e:
            print(f"Request {url} error! Will try {count} counts!")
            count -= 1
            if count <= 0:
                print("Request error!")
                raise e
    return r


def get_tag(avid, cid) -> list:
    ls = []
    url = f"https://api.bilibili.com/x/web-interface/view/detail/tag?aid={avid}&cid={cid}"
    r = get(url, headers=public_header)
    for i in r.json()['data']:
        ls.append(i['tag_name'])
    return ls


def play(avid, cid) -> None:
    header = {
        'host': 'api.bilibili.com',
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
        'cookie': cookie
    }
    url1 = f"https://api.bilibili.com/x/player/playurl?avid={avid}&cid={cid}&qn=80&type=&otype=json"
    req = get(url1, headers=header, no_cache=True)
    url111 = str(req.json()["data"]["durl"][0]["url"])
    higher = req.json()['data']['quality']
    width, height = quality[higher]
    command = "mpv --sub-file=\"cached/{}.ass\" --user-agent=\"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0\" " \
              "--referrer=\"https://www.bilibili.com\" \"{}\"".format(cid,
                                                                      url111)
    if not os.path.exists("cached"):
        os.mkdir("cached")
    if not os.path.exists(f"cached/{cid}.xml"):
        r = requests.get(f"https://comment.bilibili.com/{cid}.xml")
        with open(f"cached/{cid}.xml", "wb") as f:
            f.write(r.content)
        Danmaku2ASS([f"cached/{cid}.xml"], "autodetect", f"cached/{cid}.ass", width, height, 0, "sans-serif", 25.0, 1.0,
                    10, 8, None,
                    None, False)
    os.system(command)


def get_title(video_url, av_or_bv) -> str:
    soup = BeautifulSoup(get(video_url if av_or_bv else "https://www.bilibili.com/video/" + str(video_url),
                             headers=public_header).text, "lxml")
    return soup.find(class_="video-title").string


def get_author_name_video(video_url, av_or_bv, return_mid=False) -> (str, tuple):
    print(video_url)
    soup = BeautifulSoup(get(video_url if av_or_bv else "https://www.bilibili.com/video/" + str(video_url),
                             headers=public_header).text, "lxml")
    a = soup.find(class_="username")
    if a:
        a.find("span").extract()
    else:
        print("多作者暂未实现!")
    if return_mid:
        return a.string.strip(), a.get("href").split("/")[-1]
    return a.string.strip()


def download(avid, cid):
    pass


def write_local_collection(avid) -> None:
    with open("collection.txt", "a") as write:
        write.write(str(avid) + "\n")


def read_local_collection() -> list:
    with open("collection.txt") as read:
        return read.readlines()


def get_cid(avid) -> int:
    cid_url = "https://api.bilibili.com/x/player/pagelist?aid={aid}&jsonp=jsonp".format(aid=avid)
    return get(cid_url, headers=public_header).json()["data"][0]["cid"]


def view_comment(avid, page=1):
    if not isinstance(avid, int):
        avid = avid.strip()
    url = f"http://api.bilibili.com/x/v2/reply/main?mode=0&oid={avid}&next={page}&type=1"
    r = get(url, headers=public_header, no_cache=True)
    return r.json()['data']['replies'], r.json()['data']['cursor']['all_count']


def video_status(av_or_bv: str):
    url = "http://api.bilibili.com/x/web-interface/archive/stat?aid={}"
    if av_or_bv.startswith('av'):
        av_or_bv = av_or_bv.strip("av")
        url = "http://api.bilibili.com/x/web-interface/archive/stat?aid={}".format(av_or_bv)
    if av_or_bv.startswith("BV"):
        url = "http://api.bilibili.com/x/web-interface/archive/stat?bvid={}".format(av_or_bv)

    r = get(url.format(av_or_bv), headers=public_header)
    json = r.json()
    return json['data']['bvid'], json['data']['aid'], json['data']['view'], json['data']['danmaku'], json['data'][
        'like'], json['data']['coin'], json['data']['favorite'], json['data']['share'], json['data']['reply']


def get_author_avatar(mid):
    r = get(f"https://api.bilibili.com/x/space/acc/info?mid={mid}&jsonp=jsonp", headers=public_header)
    return r.json()['data']['face']


def view_picture(url):
    os.system("mpv " + url)


def main_help():
    print("help 显示该内容")
    print("recommend 显示推荐内容")
    print("search 搜索功能")
    print("collection 使用本地收藏夹")
    print("address 使用地址&BV&av播放视频")


def comment_viewer(aid):
    _, total = view_comment(aid)
    print("总数: ", total)
    max_page = total // 20 + 1
    print(max_page)
    now = 1
    flag_comment = True
    while flag_comment:
        data, _ = view_comment(aid, now)
        if not data:
            print("到头了!")
            break
        for i_ in data:
            print("用户: ", i_['member']['uname'])
            print("内容: ")
            print(i_['content']['message'])
            print("点赞量: ", i_['like'])
            print("\n")
            while True:
                message = input("评论选项: ")
                if message == "quit":
                    flag_comment = False
                    break
                if not message:
                    break
                now += 1
            if not flag_comment:
                break


def licenses():
    print("""MIT License

Copyright (c) 2022 Laosun Studios.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""")


def clean_cache():
    shutil.rmtree("cached")
    os.mkdir("cached")


test_cookie = "_uuid=4D779741-5FF10-952C-D9E4-29DCDDC6B9AB38010infoc; b_nut=1658576443; " \
              "buvid3=A6E299C8-DE54-5E68-3E9C-1FC404F85D4342775infoc; " \
              "buvid4=8427C489-9DB8-44A3-B0DE-DFE66130D43E42775-022072319-kji2bknSwKd8UOWJnmLjdV80CM/2V0" \
              "+NqSg67PrOX099fj7ud7u2FQ%3D%3D; i-wanna-go-back=-1; b_ut=7; CURRENT_BLACKGAP=0; " \
              "rpdid=0zbfAHF9QV|RTEXDkOq|3Bt|3w1OffDf; PVID=1; fingerprint=844016f38fbc4bb4a65d3949861d2fb5; " \
              "buvid_fp_plain=undefined; buvid_fp=844016f38fbc4bb4a65d3949861d2fb5; nostalgia_conf=-1; " \
              "b_lsid=8D66F3E1_182719BCDD6; sid=7h0dsy5u; theme_style=light; " \
              "b_timer=%7B%22ffp%22%3A%7B%22333.788.fp.risk_A6E299C8%22%3A%22182719BD91C%22%2C%22333.1007.fp" \
              ".risk_A6E299C8%22%3A%22182719D8E0E%22%7D%7D; innersign=1; CURRENT_FNVAL=4048 "

quality = {
    112: (1920, 1080),
    80: (1920, 1080),
    64: (1280, 720),
    32: (720, 480),
    16: (480, 360)
}

with open("cookie.txt") as f:
    cookie = f.read()

cookie_mapping = {}

for i in cookie.split(";"):
    a, b = i.strip().split("=")
    cookie_mapping[a] = b

csrf_token = cookie_mapping['bili_jct']

public_header = {"cookie": cookie,
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77"}

cached = {}

print("LBCC v1.0.0-dev by Laosun.")
print("Type \"help\" or \"license\" for more information.")

while True:
    choose1 = input("主选项: ")
    choose1 = choose1.strip()
    if choose1 == "recommend":
        flag = True
        while flag:
            url = "https://api.bilibili.com/x/web-interface/index/top/feed/rcmd"
            r = get(url, headers=public_header, no_cache=True)

            for i in r.json()["data"]['item']:
                flag1 = True
                avid = i['id']
                cid = i['cid']
                bvid, _, view, danmaku, like_, coin, favorite, share, comment_count = video_status(i['bvid'])
                print("标题: ", i['title'])
                print("作者: ", i['owner']['name'])
                print('avid: ', avid)
                print("bvid: ", bvid)
                print("观看量: ", view)
                print("弹幕: ", danmaku)
                print("点赞量: ", like_)
                print("硬币量: ", coin)
                print("收藏量: ", favorite)
                print("转发量: ", share)
                print("评论量: ", comment_count)
                print("标签: ", ", ".join(get_tag(avid, cid)))
                while True:
                    choose = input("推荐选项: ")
                    if choose == "play":
                        play(avid, cid)
                    elif choose == "exit":
                        flag = False
                        flag1 = False
                        break
                    elif choose == "view_comment":
                        comment_viewer(avid)
                    elif choose == "like":
                        like(avid)
                    elif choose == "unlike":
                        like(avid, unlike=True)
                    elif not choose:
                        break
                    elif choose == 'download':
                        download(avid, cid)
                    elif choose == "collection":
                        write_local_collection(avid)
                        print("收藏到本地收藏夹.")
                    else:
                        print("未知选项!")
                if not flag1: break
                print("\n" * 2)
    elif choose1 == "address":
        IS_AV = False
        video = input("地址或av&bv号: ")
        try:
            int(video)
            video = "av" + video
            IS_AV = True
        except (TypeError, ValueError):
            pass
        if "b23.tv" in video:
            video = get(video).url
        print("标题: ", get_title(video, av_or_bv=video.startswith("https")))
        av_or_bv = video.split("/")[-1].split("?")[0]
        bvid, avid, view, danmaku, like_, coin, favorite, share, comment_count = video_status(str(av_or_bv))
        print('avid: ', avid)
        print("bvid: ", bvid)
        print("观看量: ", view)
        print("弹幕: ", danmaku)
        print("点赞量: ", like_)
        print("硬币量: ", coin)
        print("收藏量: ", favorite)
        print("转发量: ", share)
        print("评论量: ", comment_count)
        if IS_AV:
            av_or_bv = av_or_bv.strip("av")
        if av_or_bv.startswith("BV"):
            av_or_bv = get("http://api.bilibili.com/x/web-interface/archive/stat?bvid=" + av_or_bv,
                           headers=public_header)
            av_or_bv = av_or_bv.json()['data']['aid']
        cid = get_cid(av_or_bv)
        play(av_or_bv, cid)
    elif choose1 == "exit":
        break
    elif choose1 == "help":
        main_help()
    elif choose1 == 'license':
        licenses()
    elif choose1 == "collection":
        try:
            collection = read_local_collection()
        except FileNotFoundError as e:
            print("收藏文件未存在!")
            continue
        if not collection:
            print("收藏夹为空!")
            continue
        for i in collection:
            if not i.strip():
                print("end! ")
                break
            i = i[:-1]
            print("标题: ", get_title(f"av{i}", av_or_bv=False))
            bvid, avid, view, danmaku, like_, coin, favorite, share, comment_count = video_status(i)
            username, mid = get_author_name_video(f"av{i}", av_or_bv=False, return_mid=True)
            print("作者: ", username)
            print('avid: ', avid)
            print("bvid: ", bvid)
            print("观看量: ", view)
            print("弹幕: ", danmaku)
            print("点赞量: ", like_)
            print("硬币量: ", coin)
            print("收藏量: ", favorite)
            print("转发量: ", share)
            print("评论量: ", comment_count)
            flag = True
            while True:
                choose = input("收藏选项: ")
                if choose == "play":
                    play(i, get_cid(i))
                elif choose == "exit":
                    flag = False
                    break
                elif not choose:
                    break
                elif choose == "view_author_avatar":
                    view_picture(get_author_avatar(mid))
                elif choose == "like":
                    like(i)
                elif choose == "unlike":
                    like(i, unlike=True)
                elif choose == "view_comment":
                    comment_viewer(i)
                else:
                    print("未知选项!")
            if not flag: break
    elif choose1 == "search":
        search_url = "http://api.bilibili.com/x/web-interface/search/type?keyword={}&search_type=video&page={}"
        try:
            search_thing = input("请输入搜索的东西: ")
        except KeyboardInterrupt:
            print("\n取消搜索.")
            continue
        page = 1
        flag_search = True
        while flag_search:
            r = get(search_url.format(search_thing, page), headers=public_header)
            if not r.json()['data'].get("result"):
                print("到头了!")
                flag_search = False
                break
            for i in r.json()['data'].get("result"):
                _, _, view, danmaku, like_, coin, favorite, share, comment_count = video_status(str(i['aid']))
                print("标题: ", get_title("av" + str(i['aid']), av_or_bv=False))
                print('作者: ', i['author'])
                print("观看量: ", view)
                print("avid: ", i['aid'])
                print("bvid: ", i['bvid'])
                print("弹幕: ", danmaku)
                print("点赞量: ", like_)
                print("硬币量: ", coin)
                print("收藏量: ", favorite)
                print("转发量: ", share)
                print("评论量: ", comment_count)
                print("简介:")
                print(i['description'])
                print("")
                while True:
                    choose = input("搜索选项: ")
                    if choose == "play":
                        play(i['aid'], get_cid(i['aid']))
                    elif choose == "exit":
                        flag_search = False
                        break
                    elif choose == "like":
                        like(i['aid'])
                    elif choose == "unlike":
                        like(i['aid'], unlike=True)
                    elif not choose:
                        break
                    elif choose == "view_comment":
                        comment_viewer(i['aid'])
                    else:
                        print("未知选项!")
                if not flag_search:
                    break
    elif choose1 == "clean_cache":
        clean_cache()
        print("成功清除缓存!")
    else:
        print("未知选项!")
