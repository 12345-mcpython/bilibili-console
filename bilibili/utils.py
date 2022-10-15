import base64
import json
import os
import sys

import requests
import rsa

cached_response = {}


def encrypt_password(public_key, data):
    pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(public_key)
    return base64.urlsafe_b64encode(rsa.encrypt(data, pub_key))


def response_to_cookie(request: requests.Response):
    string = ""
    for i in request.cookies:
        string += i.name + "=" + i.value + ";"
    return string[:-1]


def format_long(long):
    if long > 60 * 60:
        fmt = "{}:{}:{}"
        hour = long // (60 * 60)
        minute = (long - (hour * 60 * 60)) // 60
        sec = long - (hour * 60 * 60) - minute * 60
        if minute < 10:
            fmt = "{}:0{}:{}"
        if sec < 10:
            fmt = "{}:{}:0{}"
        if sec < 10 and minute < 10:
            fmt = "{}:0{}:0{}"
        return fmt.format(hour, minute, sec)
    else:
        fmt = "{}:{}"
        minute = long // 60
        if minute < 10:
            fmt = "0{}:{}"
        sec = long - minute * 60
        if sec < 10:
            fmt = "{}:0{}"
        if sec < 10 and minute < 10:
            fmt = "0{}:0{}"
        return fmt.format(minute, sec)


def get(url: str, params=None, no_cache=False, **kwargs) -> requests.Response:
    if cached_response.get(url):
        return cached_response.get(url)
    else:
        count = 3
        while True:
            try:
                r = requests.get(url, params=params, timeout=5, **kwargs)
                break
            except requests.exceptions.RequestException as request_error:
                print(f"Request {url} error! Will try {count} counts!")
                count -= 1
                if count <= 0:
                    raise request_error
        if not no_cache:
            cached_response[url] = r
        return r


def post(url: str, params=None, **kwargs) -> requests.Response:
    count = 3
    while True:
        try:
            r = requests.post(url, params=params, timeout=5, **kwargs)
            break
        except requests.exceptions.RequestException as error:
            print(f"Request {url} error! Will try {count} counts!")
            count -= 1
            if count <= 0:
                print("Request error!")
                raise error
    return r
