"""
Copyright (c) 2022 Laosun Studios. All Rights Reserved.

Distributed under MIT license.

The product is developing. Effect currently 
displayed is for reference only. Not indicative 
of final product.

MIT License

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
SOFTWARE.
"""

import shutil
from typing import Union
import os
import base64
import json
import datetime

import requests
from bs4 import BeautifulSoup
import rsa

from danmaku2ass import Danmaku2ASS


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

if cookie:
    for i in cookie.split(";"):
        a, b = i.strip().split("=")
        cookie_mapping[a] = b

csrf_token = cookie_mapping.get("bili_jct")

public_header = {"cookie": cookie,
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77"}

cached = {}

is_login = False

print("LBCC v1.0.0-dev.")
print("Type \"help\" for more information.")


def get_login_status():
    global is_login
    r = get('https://api.bilibili.com/x/member/web/account',
            headers=public_header)
    if r.json()['code'] == -101:
        print("账号尚未登录! ")
    elif r.json()['code'] == 0:
        print("账号已登录.")
        print("欢迎" + r.json()['data']['uname'] + "回来.")
        is_login = True


def logout():
    if not is_login:
        print("你未登录!")
    print("你确定要登出吗?(Y/N)")
    if input().lower() != "y":
        return
    r = post("https://passport.bilibili.com/login/exit/v2",
             headers=public_header, data={"biliCSRF": csrf_token})
    try:
        if r.json()['code'] == 0:
            print("登出成功!")
            with open("cookie.txt", "w") as f:
                f.truncate()
    except json.decoder.JSONDecodeError:
        print("登出失败!")


def login():
    if is_login:
        print("你已登录!")
        return
    while True:
        choose = input("选择登录方式(password/sms): ")
        if choose == "password":
            validate, seccode, key, challenge = verify_captcha_key()
            username = input("用户名: ")
            password = input("密码: ")
            login_by_password(username, password, validate,
                              seccode, key, challenge)
            break
        elif choose == "sms":
            print("默认手机号国家代码为中国代码(+86)")
            validate, seccode, token, challenge = verify_captcha_token()
            tel = input("请输入手机号: ")
            data = {"tel": tel, "cid": 86, "source": "main_web", "token": token,
                    "challenge": challenge, "validate": validate, "seccode": seccode}
            r = post("https://passport.bilibili.com/x/passport-login/web/sms/send",
                     data=data, headers=public_header)
            if r.json()['code'] == 0:
                captcha_key = r.json()['data']['captcha_key']
            else:
                print("error")
                print(r.json()['code'])
                break
            code = input("请输入短信认证码: ")
            data_login = {"code": code, "tel": tel, "cid": 86,
                          "source": "main_web", "captcha_key": captcha_key}
            r_login = post("https://passport.bilibili.com/x/passport-login/web/login/sms",
                           headers=public_header, data=data_login)
            if r_login.json()['code'] == 0:
                with open("cookie.txt") as f:
                    cookie_str = ""
                    for key, value in r_login.cookies.items():
                        cookie_str += "{}={};".format(key, value)
                        cookie_str = cookie_str[:-1]
                        f.write(cookie_str)
                print("登录成功!")

            else:
                print("登录失败!")
                print(r_login.json()['code'])
            break


def login_by_password(username, password, validate, seccode, token, challenge):
    key_request = get(
        'https://passport.bilibili.com/login?act=getkey', headers=public_header)
    hash, public_key = key_request.json()['hash'], key_request.json()['key']
    password_hashed = hash + password
    password_encrypt = encrypt_password(
        public_key.encode(), password_hashed.encode())
    data = {"captchaType": 6, "username": username, "password": password_encrypt.decode(
    ), "keep": True, "challenge": challenge, "key": token, "validate": validate, "seccode": seccode}
    r = post("https://passport.bilibili.com/web/login/v2",
             headers={}, data=data)
    if r.json()['code'] == 0:
        with open("cookie.txt") as f:
            cookie_str = ""
            for key, value in r.cookies.items():
                cookie_str += "{}={};".format(key, value)
                cookie_str = cookie_str[:-1]
                f.write(cookie_str)
    else:
        print("登录失败!")
        print(r.json()['code'])


def encrypt_password(public_key, data):
    pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(public_key)
    return base64.urlsafe_b64encode(rsa.encrypt(data, pub_key))


def verify_captcha_key():
    r = get("https://passport.bilibili.com/web/captcha/combine?plat=6",
            headers=public_header)
    a = r.json()
    key = a['data']['result']['key']
    print("gt: ", a['data']['result']['gt'],
          "challenge: ", a['data']['result']['challenge'])
    print("请到 https://kuresaru.github.io/geetest-validator/ 认证")
    validate = input("validate: ")
    seccode = input("seccode: ")
    return validate, seccode, key, a['data']['result']['challenge']


def verify_captcha_token():
    r = get("https://passport.bilibili.com/x/passport-login/captcha?source=main_web",
            headers=public_header)
    a = r.json()
    token = a['data']['token']
    print("gt: ", a['data']['geetest']['gt'],
          "challenge: ", a['data']['geetest']['challenge'])
    print("请到 https://kuresaru.github.io/geetest-validator/ 认证")
    validate = input("validate: ")
    seccode = input("seccode: ")
    return validate, seccode, token, a['data']['geetest']['challenge']


def check_av_or_bv(av_or_bv: str) -> bool:
    try:
        int(av_or_bv)
        return True
    except:
        return False


def like(abv: str, unlike: bool = False) -> None:
    data = {}
    IS_AV: bool = check_av_or_bv(abv)
    if IS_AV:
        data["aid"] = abv
    else:
        data['bvid'] = abv
    if not unlike:
        data['like'] = 1
    else:
        data['like'] = 2
    data['csrf'] = csrf_token
    r = post("http://api.bilibili.com/x/web-interface/archive/like",
             data=data, headers=public_header)
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


def triple(abv: bool):
    data = {}
    IS_AV: bool = check_av_or_bv(abv)
    if IS_AV:
        data["aid"] = abv
    else:
        data['bvid'] = abv
    data['csrf'] = csrf_token
    r = post("http://api.bilibili.com/x/web-interface/archive/like/triple",
             headers=public_header, data=data)
    code = r.json()['code']
    if code == 0:
        print("三连成功!")
    else:
        print("三连失败!")
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


def get_tag(avid: int, cid: int) -> list:
    ls = []
    url = f"https://api.bilibili.com/x/web-interface/view/detail/tag?aid={avid}&cid={cid}"
    r = get(url, headers=public_header)
    for i in r.json()['data']:
        ls.append(i['tag_name'])
    return ls


def play_with_cid(av_or_bv, cid: int) -> None:
    url1 = f"https://api.bilibili.com/x/player/playurl?cid={cid}&qn=80&type=&otype=json"
    IS_AV: bool = check_av_or_bv(av_or_bv)
    if IS_AV:
        url1 += "&avid=" + av_or_bv
    else:
        url1 += "&bvid=" + av_or_bv
    header = {
        'host': 'api.bilibili.com',
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
        'cookie': cookie
    }
    req = get(url1, headers=header, no_cache=True)
    if req.json()['code'] != 0:
        print("获取视频错误!")
        print(req.url)
        print(req.json())
        return
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


def play(av_or_bv):
    print("\n")
    print("视频选集")
    av_or_bv = str(av_or_bv)
    url = "http://api.bilibili.com/x/web-interface/view/detail"
    IS_AV: bool = check_av_or_bv(av_or_bv)
    if IS_AV:
        url += "?aid=" + av_or_bv
    else:
        url += "?bvid=" + av_or_bv
    r = get(url, headers=public_header)
    video = r.json()['data']["View"]["pages"]
    for i in video:
        print(f"{i['page']}: {i['part']}")
    print("请以冒号前面的数字为准选择视频.")    
    while True:    
        page = input("选择视频: ")
        if page == "exit":
            break
        if not page:
            continue
        if not page.isdigit():
            continue
        if int(page) > len(video) or int(page) <= 0:
            print("选视频错误!")
            continue
        cid = video[int(page)-1]['cid']
        play_with_cid(av_or_bv, cid)
        break
    return    


def play_b_collection(av_or_bv):   
    av_or_bv = str(av_or_bv)
    url = "http://api.bilibili.com/x/web-interface/view/detail"
    IS_AV: bool = check_av_or_bv(av_or_bv)
    if IS_AV:
        url += "?aid=" + av_or_bv
    else:
        url += "?bvid=" + av_or_bv
    r = get(url, headers=public_header)
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
        print(f"{i+1}: {j['title']}")
    print("请以冒号前面的数字为准选择视频.")    
    while True:    
        page = input("选择视频: ")
        if page == "exit":
            break
        if page.startswith("view_info"):
            page_ = page.strip("view_info").strip()
            if not page_.isdecimal():
                print("参数错误! ")
                continue
            get_video_info(b_collection_video[int(page_)-1]['bvid'])
        if not page:
            continue
        if not page.isdigit():
            continue
        if int(page) > len(b_collection_video) or int(page) <= 0:
            print("选视频错误!")
            continue
        cid = b_collection_video[int(page)-1]['cid']
        play_with_cid(b_collection_video[int(page)-1]['bvid'], cid)
    return    
    
    



def get_title(video_url: str, av_or_bv: bool) -> str:
    soup = BeautifulSoup(get(video_url if av_or_bv else "https://www.bilibili.com/video/" + str(video_url),
                             headers=public_header).text, "lxml")
    return soup.find(class_="video-title").string


def get_author_name_video(video_url: str, av_or_bv: bool, return_mid=False) -> Union[str, tuple]:
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


def write_local_collection(avid: int) -> None:
    with open("collection.txt", "a") as write:
        write.write(str(avid) + "\n")


def read_local_collection() -> list:
    with open("collection.txt") as read:
        return read.readlines()


def get_cid(avid: str) -> int:
    cid_url = "https://api.bilibili.com/x/player/pagelist?aid={aid}&jsonp=jsonp".format(
        aid=avid)
    return get(cid_url, headers=public_header).json()["data"][0]["cid"]


def view_comment(avid: Union[int, str], page=1):
    if not isinstance(avid, int):
        avid = avid.strip()
    url = f"http://api.bilibili.com/x/v2/reply/main?mode=0&oid={avid}&next={page}&type=1"
    r = get(url, headers=public_header, no_cache=True)
    return r.json()['data']['replies'], r.json()['data']['cursor']['all_count']


def video_status(av_or_bv: str):
    url = "http://api.bilibili.com/x/web-interface/archive/stat?aid={}"
    if av_or_bv.startswith('av'):
        av_or_bv = av_or_bv.strip("av")
        url = "http://api.bilibili.com/x/web-interface/archive/stat?aid={}".format(
            av_or_bv)
    if av_or_bv.startswith("BV"):
        url = "http://api.bilibili.com/x/web-interface/archive/stat?bvid={}".format(
            av_or_bv)

    r = get(url.format(av_or_bv), headers=public_header)
    json = r.json()
    return json['data']['bvid'], json['data']['aid'], json['data']['view'], json['data']['danmaku'], json['data'][
        'like'], json['data']['coin'], json['data']['favorite'], json['data']['share'], json['data']['reply']


def get_author_avatar(mid: int):
    r = get(
        f"https://api.bilibili.com/x/space/acc/info?mid={mid}&jsonp=jsonp", headers=public_header)
    return r.json()['data']['face']


def view_picture(url: str):
    os.system("mpv " + url)


def main_help():
    print("help 显示该内容")
    print("recommend 显示推荐内容")
    print("search 搜索功能")
    print("collection 使用本地收藏夹")
    print("address 使用地址&BV&av播放视频")
    print("login 登录")
    print("logout 退出")


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


def clean_cache():
    shutil.rmtree("cached")
    os.mkdir("cached")


def get_video_info(av_or_bv: str):
    av_or_bv = str(av_or_bv)
    url = "http://api.bilibili.com/x/web-interface/view/detail"
    IS_AV: bool = check_av_or_bv(av_or_bv)
    if IS_AV:
        url += "?aid=" + av_or_bv
    else:
        url += "?bvid=" + av_or_bv
    r = get(url, headers=public_header)
    video = r.json()['data']["View"]
    author = r.json()['data']["Card"]
    status = video['stat']
    print("长度: ", format_long(video['duration']))
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
    print("所有者名字: ", video['owner']['name'])
    print("mid: ", video['owner']['mid'])


def format_long(long):
    fmt = "{}:{}"
    if long > 60 * 60:
        fmt = "{}:{}:{}"
        hour = long // (60 * 60)
        minute = (long - (hour * 60 * 60)) // 60
        sec = long - (hour * 60 * 60) - minute * 60
    else:
        minute = (long) // 60
        sec = long - minute * 60
    if long > 60 * 60:
        return fmt.format(hour, minute, sec)
    else:
        return fmt.format(minute, sec)


def recommend():
    flag = True
    while flag:
        url = "https://api.bilibili.com/x/web-interface/index/top/feed/rcmd"
        r = get(url, headers=public_header, no_cache=True)

        for i in r.json()["data"]['item']:
            flag1 = True
            avid = i['id']
            cid = i['cid']
            bvid, _, view, danmaku, like_, coin, favorite, share, comment_count = video_status(
                i['bvid'])
            print("标题: ", i['title'])
            print("作者: ", i['owner']['name'])
            print("bvid: ", bvid)
            print("观看量: ", view)
            print("标签: ", ", ".join(get_tag(avid, cid)))
            while True:
                choose = input("推荐选项: ")
                if choose == "play":
                    play(avid)
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
                elif choose == "triple":
                    triple(avid)
                elif not choose:
                    break
                elif choose == 'download':
                    download(avid, cid)
                elif choose == "view_info":
                    get_video_info(avid)
                elif choose == "collection":
                    write_local_collection(avid)
                    print("收藏到本地收藏夹.")
                elif choose == "view_b_collection":
                    play_b_collection(avid)
                else:
                    print("未知选项!")
            if not flag1:
                break
            print("\n" * 2)


def address():
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
    bvid, avid, view, danmaku, like_, coin, favorite, share, comment_count = video_status(
        str(av_or_bv))
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
    play(av_or_bv)


def collection():
    try:
        collection = read_local_collection()
    except FileNotFoundError as e:
        print("收藏文件未存在!")
        return
    if not collection:
        print("收藏夹为空!")
        return
    for i in collection:
        if not i.strip():
            print("end! ")
            break
            return
        i = i[:-1]
        print("标题: ", get_title(f"av{i}", av_or_bv=False))
        bvid, avid, view, danmaku, like_, coin, favorite, share, comment_count = video_status(
            i)
        print("bvid: ", bvid)
        print("观看量: ", view)
        flag = True
        while True:
            choose = input("收藏选项: ")
            if choose == "play":
                play(i)
            elif choose == "exit":
                flag = False
                break
            elif not choose:
                break
            elif choose == "like":
                like(i)
            elif choose == "unlike":
                like(i, unlike=True)
            elif choose == "triple":
                triple(i)
            elif choose == "view_comment":
                comment_viewer(i)
            elif choose == "view_info":
                get_video_info(i)
            elif choose == "view_b_collection":
                play_b_collection(i)    
            else:
                print("未知选项!")
        if not flag:
            break


def search():
    search_url = "http://api.bilibili.com/x/web-interface/search/type?keyword={}&search_type=video&page={}"
    try:
        search_thing = input("请输入搜索的东西: ")
    except KeyboardInterrupt:
        print("\n取消搜索.")
        return
    page = 1
    flag_search = True
    while flag_search:
        r = get(search_url.format(search_thing, page), headers=public_header)
        if not r.json()['data'].get("result"):
            print("到头了!")
            flag_search = False
            break
        for i in r.json()['data'].get("result"):
            _, _, view, danmaku, like_, coin, favorite, share, comment_count = video_status(
                str(i['aid']))
            print("标题: ", get_title("av" + str(i['aid']), av_or_bv=False))
            print("观看量: ", view)
            print("bvid: ", i['bvid'])
            while True:
                choose = input("搜索选项: ")
                if choose == "play":
                    play(i['aid'])
                elif choose == "exit":
                    flag_search = False
                    break
                elif choose == "like":
                    like(i['aid'])
                elif choose == "unlike":
                    like(i['aid'], unlike=True)
                elif choose == "triple":
                    triple(i['aid'])
                elif not choose:
                    break
                elif choose == "view_comment":
                    comment_viewer(i['aid'])
                elif choose == "view_info":
                    get_video_info(i['aid'])
                elif choose == "view_b_collection":
                    play_b_collection(i['aid'])    
                else:
                    print("未知选项!")
            if not flag_search:
                break


get_login_status()


while True:
    choose1 = input("主选项: ")
    choose1 = choose1.strip()
    if choose1 == "recommend":
        recommend()
    elif choose1 == "address":
        address()
    elif choose1 == "collection":
        collection()
    elif choose1 == "search":
        search()
    elif choose1 == "logout":
        logout()
    elif choose1 == 'login':
        login()
    elif choose1 == "exit":
        print("\n")
        break
    elif choose1 == "help":
        main_help()
    elif choose1 == "clean_cache":
        clean_cache()
        print("成功清除缓存!")
    else:
        print("未知选项!")
