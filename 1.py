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

import requests

from bs4 import BeautifulSoup

import os

with open("cookie.txt") as f:
    cookie = f.read()

public_header = {"cookie": cookie,
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77"}


def get_tag(avid, cid):
    ls = []
    url = f"https://api.bilibili.com/x/web-interface/view/detail/tag?aid={avid}&cid={cid}"
    r = requests.get(url, headers=public_header)
    for i in r.json()['data']:
        ls.append(i['tag_name'])
    return ls


def play(avid, cid):
    header = {
        'host': 'api.bilibili.com',
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
        'cookie': cookie
    }
    url1 = f"https://api.bilibili.com/x/player/playurl?avid={avid}&cid={cid}&qn=80&type=&otype=json"
    req = requests.get(url1, headers=header)
    url111 = req.json()["data"]["durl"][0]["url"]
    command = "mpv --user-agent=\"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0\" " \
              "--referrer=\"https://www.bilibili.com\" \"{}\"".format(
        url111)
    os.system(command)


def get_title(video_url, av_or_bv):
    soup = BeautifulSoup(requests.get(video_url if av_or_bv else "https://www.bilibili.com/video/" + str(video_url),
                                      headers=public_header).text, "lxml")
    return soup.find(class_="video-title").string


def get_author_name_video(video_url, av_or_bv, return_mid=False):
    soup = BeautifulSoup(requests.get(video_url if av_or_bv else "https://www.bilibili.com/video/" + str(video_url),
                                      headers=public_header).text, "lxml")
    a = soup.find(class_="username")
    a.find("span").extract()
    if return_mid:
        return a.string.strip(), a.get("href").split("/")[-1]
    return a.string.strip()


def download(avid, cid):
    pass


def write_local_collection(avid):
    with open("collection.txt", "a") as write:
        write.write(str(avid) + "\n")


def read_local_collection():
    with open("collection.txt") as read:
        return read.readlines()


def get_cid(avid):
    cid_url = "https://api.bilibili.com/x/player/pagelist?aid={aid}&jsonp=jsonp".format(aid=avid)
    return requests.get(cid_url, headers=public_header).json()["data"][0]["cid"]


def view_comment(avid, page=1):
    if not isinstance(avid, int):
        avid = avid.strip()
    url = f"http://api.bilibili.com/x/v2/reply/main?mode=0&oid={avid}&next={page}&type=1"
    r = requests.get(url, headers=public_header)
    return r.json()['data']['replies'], r.json()['data']['cursor']['all_count']


def video_status(av_or_bv: str):
    url = "http://api.bilibili.com/x/web-interface/archive/stat?aid={}"
    if av_or_bv.startswith('av'):
        av_or_bv = av_or_bv.strip("av")
        url = "http://api.bilibili.com/x/web-interface/archive/stat?aid={}".format(av_or_bv)
    if av_or_bv.startswith("BV"):
        url = "http://api.bilibili.com/x/web-interface/archive/stat?bvid={}".format(av_or_bv)
    r = requests.get(url.format(av_or_bv), headers=public_header)
    print(r.url)
    json = r.json()
    return json['data']['bvid'], json['data']['aid'], json['data']['view'], json['data']['danmaku'], json['data'][
        'like'], json['data']['coin'], json['data']['favorite'], json['data']['share'], json['data']['reply']


def get_author_avatar(mid):
    r = requests.get(f"https://api.bilibili.com/x/space/acc/info?mid={mid}&jsonp=jsonp", headers=public_header)
    return r.json()['data']['face']


def view_picture(url):
    os.system("mpv " + url)


while True:
    print("LBCC v1.0.0-dev by Laosun.")
    print("Type \"help\" for more information.")
    choose1 = input("选择一个选项: ")
    if choose1 == "recommend":
        flag = True
        while flag:
            url = "https://api.bilibili.com/x/web-interface/index/top/feed/rcmd?y_num=5&fresh_idx_1h=1&fresh_idx=1" \
                  "&feed_version=V4&fetch_row=1&homepage_ver=1&ps=11&fresh_type=3 "

            r = requests.get(url, headers=public_header)

            for i in r.json()["data"]['item']:
                flag1 = True
                avid = i['id']
                cid = i['cid']
                print("Title: ", i['title'])
                print("owner: ", i['owner']['name'])
                bvid, _, view, danmaku, like, coin, favorite, share, comment_count = video_status(i['bvid'])
                print('avid: ', avid)
                print("bvid: ", bvid)
                print("view: ", view)
                print("danmaku: ", danmaku)
                print("like: ", like)
                print("coin: ", coin)
                print("favorite: ", favorite)
                print("share: ", share)
                print("comment: ", comment_count)
                print("Tag: ", ", ".join(get_tag(avid, cid)))
                while True:
                    choose = input("选择一个选项： ")
                    if choose == "play":
                        play(avid, cid)
                    elif choose == "exit":
                        flag = False
                        flag1 = False
                        break
                    elif choose == "view_comment":
                        _, total = view_comment(avid)
                        print("总数: ", total)
                        max_page = total // 20 + 1
                        now = 1
                        while True:
                            data, _ = view_comment(avid, now)
                            if not data:
                                print("到头了!")
                                break
                            for i in data:
                                print("用户: ", i['member']['uname'])
                                print("内容: ")
                                print(i['content']['message'])
                                print("点赞量: ", i['like'])
                                print("\n")
                            message = input()
                            if message == "quit": break
                            now += 1
                    elif not choose:
                        break
                    elif choose == 'download':
                        download(avid, cid)
                    elif choose == "collection":
                        write_local_collection(avid)
                        print("成功! ")
                    else:
                        print("未知选项！")
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
        print("标题： ", get_title(video, av_or_bv=video.startswith("https")))
        av_or_bv = video.split("/")[-1].split("?")[0]
        print("信息: ")
        bvid, avid, view, danmaku, like, coin, favorite, share, comment_count = video_status(str(av_or_bv))
        print('avid: ', avid)
        print("bvid: ", bvid)
        print("view: ", view)
        print("danmaku: ", danmaku)
        print("like: ", like)
        print("coin: ", coin)
        print("favorite: ", favorite)
        print("share: ", share)
        print("comment: ", comment_count)
        if IS_AV:
            av_or_bv = av_or_bv.strip("av")
        if av_or_bv.startswith("BV"):
            av_or_bv = requests.get("http://api.bilibili.com/x/web-interface/archive/stat?bvid=" + av_or_bv,
                                    headers=public_header)
            av_or_bv = av_or_bv.json()['data']['aid']
        cid = get_cid(av_or_bv)
        play(av_or_bv, cid)
    elif choose1 == "exit":
        break
    elif choose1 == "collection":
        try:
            collection = read_local_collection()
        except FileNotFoundError as e:
            print("收藏文件未存在！")
            continue
        if not collection:
            print("收藏夹为空！")
            continue
        for i in collection:
            if not i.strip():
                print("end! ")
                break
            i = i[:-1]
            print("标题: ", get_title(f"av{i}", av_or_bv=False))
            bvid, avid, view, danmaku, like, coin, favorite, share, comment_count = video_status(i)
            username, mid = get_author_name_video(f"av{i}", av_or_bv=False, return_mid=True)
            print('avid: ', avid)
            print("bvid: ", bvid)
            print("view: ", view)
            print("danmaku: ", danmaku)
            print("like: ", like)
            print("coin: ", coin)
            print("favorite: ", favorite)
            print("share: ", share)
            print("comment: ", comment_count)
            print("author: ", username)
            flag = True
            while True:
                choose = input("选择一个选项： ")
                if choose == "play":
                    play(i, get_cid(i))
                elif choose == "exit":
                    flag = False
                    break
                elif not choose:
                    break
                elif choose == "view_author_avatar":
                    view_picture(get_author_avatar(mid))
                elif choose == "view_comment":
                    _, total = view_comment(i)
                    print("总数: ", total)
                    max_page = total // 20 + 1
                    now = 1
                    while True:
                        data, _ = view_comment(i, now)
                        if not data:
                            print("到头了!")
                            break
                        for i_ in data:
                            print("用户: ", i_['member']['uname'])
                            print("内容: ")
                            print(i_['content']['message'])
                            print("点赞量: ", i_['like'])
                            print("\n")
                        message = input()
                        if message == "quit": break
                        now += 1
                else:
                    print("未知选项！")
            if not flag: break
    elif choose1 == "search":
        search_url = "http://api.bilibili.com/x/web-interface/search/type?keyword={}&search_type=video&page={}"
        search_thing = input("请输入搜索的东西: ")
        page = 1
        flag_search = True
        while flag_search:
            r = requests.get(search_url.format(search_thing, page), headers=public_header)
            if not r.json()['data'].get("result"):
                print("到头了！")
                flag_search = False
                break
            for i in r.json()['data'].get("result"):
                print("avid: ", i['aid'])
                print('author: ', i['author'])
                print("bvid: ", i['bvid'])
                print("title: ", get_title("av" + str(i['aid']), av_or_bv=False))
                print("description:")
                print(i['description'])
                _, _, view, danmaku, like, coin, favorite, share, comment_count = video_status(str(i['aid']))
                print("view: ", view)
                print("danmaku: ", danmaku)
                print("like: ", like)
                print("coin: ", coin)
                print("favorite: ", favorite)
                print("share: ", share)
                print("comment: ", comment_count)
                while True:
                    choose = input("选择一个选项： ")
                    if choose == "play":
                        play(i['aid'], get_cid(i['aid']))
                    elif choose == "exit":
                        flag_search = False
                        break
                    elif not choose:
                        break
                    elif choose == "view_comment":
                        _, total = view_comment(i['aid'])
                        print("总数: ", total)
                        max_page = total // 20 + 1
                        print(max_page)
                        now = 1
                        while True:
                            data, _ = view_comment(i['aid'], now)
                            if not data:
                                print("到头了!")
                                break
                            for i_ in data:
                                print("用户: ", i_['member']['uname'])
                                print("内容: ")
                                print(i_['content']['message'])
                                print("点赞量: ", i_['like'])
                                print("\n")
                            message = input()
                            if message == "quit": break
                            now += 1
                    else:
                        print("未知选项！")
                if not flag_search:
                    break


    else:
        print("未知选项！")
