"""
This file is part of bilibili-console.

bilibili-console is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

bilibili-console is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with bilibili-console. If not, see <https://www.gnu.org/licenses/>.
"""
import os
import sys
import time
import uuid
from random import random

import requests

from bilibili.util_classes import JSON


def set_user():
    ls = os.listdir("./users")
    print("选择cookie")
    for i, j in enumerate(ls):
        print(f"{i + 1}: {j.split('.')[0]}")
    while True:
        choose = input("选项: ")
        choose = int(choose)
        if choose > len(ls) or choose <= 0:
            print("输入错误.")
        print(f"你选择的是{ls[choose - 1].split('.')[0]}.")
        with open("user", "w") as f:
            f.write(ls[choose - 1].split(".")[0] + ".txt")
        print("配置成功. LBCC将会退出.")
        input()
        sys.exit(0)


def check_login(cookie):
    cached_header = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77",
        "referer": "https://www.bilibili.com", 'cookie': cookie}
    r = requests.get('https://api.bilibili.com/x/member/web/account',
                     headers=cached_header, no_cache=True)
    a = JSON(r)
    if a.code == -101:
        return False
    elif a.code == 0:
        return a.data.uname


def get_available_user():
    if not os.path.exists("cookie"):
        return False
    if os.path.exists("user"):
        with open("user") as f:
            return f.read()
    elif len(os.listdir("users")) != 0:
        return os.listdir("users")[0]
    else:
        return None


def ask_cookie(first_use):
    global local_cookie
    if first_use:
        print("第一次使用LBCC, 是否配置cookie? (y/n)")
        choose = input()
        if choose.lower() == "y":
            cookie_or_file = input("请输入cookies或文件路径: ")
            if os.path.exists(cookie_or_file):
                with open(cookie_or_file) as f:
                    local_cookie = f.read()
            else:
                local_cookie = cookie_or_file
            username = check_login(local_cookie)
            if username:
                print("Cookie指定的用户为: ", username)
            else:
                print("Cookie未指定用户,取消配置.")
                return
            with open(f"users/{username}.txt", "w") as f:
                f.write(local_cookie)
            with open("cookie", "w"):
                pass
            print("Cookie配置成功! LBCC将会退出. ")
            input()
            sys.exit(0)


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


def test_cookie():
    for i in os.listdir("users"):
        with open(f"users/{i}") as f:
            cookie = f.read()
        username = check_login(cookie)
        if username:
            print(f"Cookie {username} 有效.")
        else:
            print(f"Cookie {i} 无效或已登出.")
            return


def fake_buvid3():
    a = str(uuid.uuid4()).upper()
    for i in range(5):
        a += str(random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 0, "a", "b", "c", "d", "e", "f"])).upper()
    return a + "infoc"


def fake_search_cookie():
    return f"b_nut={int(time.time())};b_ut=7;buvid3={fake_buvid3()};i-wanna-go-back=-1;innersign=0"
