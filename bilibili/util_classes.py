import json
import typing

import requests


class Command:
    def __init__(self, command, length=0, run=lambda: None, should_run=True, args=(), kwargs={}):
        self.command = command
        self.length = length
        self.run = run
        self.should_run = should_run
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return "<{} command={} length={}>".format(type(self).__name__, self.command, self.length)


class JSON:
    def __init__(self, json_str: typing.Union[str, requests.Response, dict]):
        if isinstance(json_str, requests.Response):
            self.json = json_str.json()
        elif isinstance(json_str, dict):
            self.json = json_str
        elif isinstance(json_str, JSON):
            self.json = json_str.json
        else:
            self.json = json.loads(json_str)

    def __getattr__(self, item):
        if isinstance(self.json[item], dict):
            return JSON(json.dumps(self.json[item], ensure_ascii=False))
        if isinstance(self.json[item], list):
            return [JSON(json.dumps(item, ensure_ascii=False)) for item in self.json[item]]
        return self.json[item]

    def __str__(self):
        return json.dumps(self.json, ensure_ascii=False)

    def __repr__(self):
        return json.dumps(self.json, ensure_ascii=False)

    def __getitem__(self, item):
        if isinstance(self.json[item], dict):
            return JSON(json.dumps(self.json[item], ensure_ascii=False))
        return self.json[item]
