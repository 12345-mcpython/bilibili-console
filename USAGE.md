# LBCC使用教程

## 1.1 下载并安装

首先安装 [python](http://www.python.org/downloads)
和 [mpv](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/mpv.exe)

然后 `git clone https://github.com/12345-mcpython/bilibili-console` 或

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011121641.png)

并解压zip

打开命令行，切换到此文件夹或对文件夹Shift+右键，点击"在命令行打开此文件夹" (在Win11中可以直接右键打开终端)

输入 `pip install -r requirements.txt`

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011122441.png)

登录b站网页端, 手动拷贝cookie一次(按F12, 到Network 网络 标签页, 按F5, 翻到最上面找到第一个www.bilibili.com点击,
找到Response Header 请求标头 找到cookie选择并复杂这堆cookie) 并新建文件cookie.txt, 把拷贝内容复制到这个文件.

如果懒得复制可以通过删除 localStorage 的 ac_time_value 延长时间

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20230225201606.png)

输入 `python main.py`

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011205705.png)

## 1.2 主界面指令集

1. `recommend` 根据你账号的个性化需求推荐视频.
2. `address` 根据地址播放视频. 支持 b23.tv 短链接.
3. `bangumi` 番剧界面.
4. `favorite` 预览当前已登录账号的收藏夹.
5. `view_self` 预览当前已登录账号的个人空间.
6. `view_user` 根据mid预览账号的个人空间.
7. `export_favorite` 导出收藏夹为JSON. JSON格式见下.
8. `download_favorite` 下载收藏夹内全部视频.
9. `refresh_login_state` 重载登录状态, 重新加载cookie.txt文件内cookie.
10. `clean_cache` 清空缓存的弹幕文件.
11. `enable_online_watching` 与 `disable_online_watching` 启用或禁用正在观看的人数.

## 1.3 视频选项指令集

1. `play` 播放视频.
2. `like` 与 `unlike` 点赞或取消点赞视频.
3. `unlike` 取消点赞.
4. `coin` 投币视频.
5. `triple` 三连视频.
6. `download` 下载视频.
7. `download_video_list` 下载全部视频.
8. `view_user` 预览视频作者的用户空间.

## 1.4 个人空间指令

1. `list_video` 列出所有个人空间的视频.

## 附录 导出的收藏夹JSON格式

<details>

```json
{
    "cover": "https://i1.hdslb.com/bfs/archive/903a7e34a064a8b4b0a4cf5d72c32a9344c6d30c.jpg",
    "id": 1872753922,
    "media_count": 19,
    "medias": [
        {
            "attr": 0,
            "bvid": "BV1R54y1N7nu",
            "cnt_info": {
                "collect": 11918,
                "danmaku": 33,
                "play": 190535
            },
            "cover": "https://i1.hdslb.com/bfs/archive/903a7e34a064a8b4b0a4cf5d72c32a9344c6d30c.jpg",
            "duration": 645,
            "fav_time": 1676978493,
            "id": 864204502,
            "intro": "1w摩拉换80原石！老米你真能藏！1w摩拉是本派蒙的工资！",
            "page": 1,
            "publish_time": 1676088688,
            "title": "1w摩拉换80原石！老米你真能藏！1w摩拉是本派蒙的工资！",
            "upper": {
                "face": "https://i2.hdslb.com/bfs/face/7d874b93b83da539871f1d5df455819826d95491.jpg",
                "mid": 3493086890035370,
                "name": "游戏小驴大解密"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1oM41147ER",
            "cnt_info": {
                "collect": 17658,
                "danmaku": 575,
                "play": 894611
            },
            "cover": "https://i0.hdslb.com/bfs/archive/7abd49be4afa4ba9fe203b3b55f300303003eba9.jpg",
            "duration": 63,
            "fav_time": 1675262946,
            "id": 523013198,
            "intro": "还是当哥哥跟美少女贴贴有代入感啊",
            "page": 1,
            "publish_time": 1674124056,
            "title": "【原神】我好后悔当初没选哥哥当主角呀",
            "upper": {
                "face": "https://i2.hdslb.com/bfs/face/4d81826ee190a55593a7f2ae1e20b8fbc8e6b3c0.jpg",
                "mid": 1540103078,
                "name": "不长草的树根"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1hg41137ES",
            "cnt_info": {
                "collect": 3,
                "danmaku": 0,
                "play": 836
            },
            "cover": "https://i1.hdslb.com/bfs/archive/cabea28b765a573847a2e1e988a4d6eb08298fb1.jpg",
            "duration": 51,
            "fav_time": 1674198735,
            "id": 503342351,
            "intro": "源关卡（要科学上网）：https://www.youtube.com/watch?v=SYlFCYdqjQs",
            "page": 1,
            "publish_time": 1622298603,
            "title": "[小鳄鱼][每周关卡还原]搭桥前进",
            "upper": {
                "face": "https://i0.hdslb.com/bfs/face/03cfc671b0c356a34dfd1614903b50a464d42735.jpg",
                "mid": 349112658,
                "name": "呵哈呵啊呵哈呵"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1Wz411z7aG",
            "cnt_info": {
                "collect": 56,
                "danmaku": 18,
                "play": 21177
            },
            "cover": "https://i2.hdslb.com/bfs/archive/20687314f2f2ba70d4c5191df2c76ce93bb6392e.jpg",
            "duration": 36,
            "fav_time": 1674197311,
            "id": 200502341,
            "intro": "mega mega mega mega mega\n好昏呐\n等我睡会\n游戏:鳄鱼小顽皮爱洗澡",
            "page": 1,
            "publish_time": 1588425315,
            "title": "建议改为:群 魔 乱 舞",
            "upper": {
                "face": "https://i0.hdslb.com/bfs/face/da67a317123e8271967b2aa39291587f4b49587a.jpg",
                "mid": 348887631,
                "name": "拿着skull的老爹"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1pi4y1x797",
            "cnt_info": {
                "collect": 3,
                "danmaku": 1,
                "play": 2140
            },
            "cover": "https://i0.hdslb.com/bfs/archive/222f412c748727e4553c396b257a223d3bd564a7.jpg",
            "duration": 19,
            "fav_time": 1674196919,
            "id": 541027250,
            "intro": "游戏：鳄鱼小顽皮爱洗澡\n如果你看到了这行字，就给我点个赞吧～",
            "page": 1,
            "publish_time": 1592112164,
            "title": "【挑战NO.2】零鸭挑战F1-5",
            "upper": {
                "face": "https://i0.hdslb.com/bfs/face/21a97a0109123cf59956257a56a34172bf61c192.jpg",
                "mid": 389116215,
                "name": "芝士-cheese-"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1pe411s7rN",
            "cnt_info": {
                "collect": 240,
                "danmaku": 81,
                "play": 170968
            },
            "cover": "https://i0.hdslb.com/bfs/archive/c44a6c51293c4f715a521ed5caac93b631b4fb29.jpg",
            "duration": 264,
            "fav_time": 1674196333,
            "id": 242895142,
            "intro": "-",
            "page": 1,
            "publish_time": 1588135368,
            "title": "【喜羊羊】给 我 毒 水 灭 火",
            "upper": {
                "face": "https://i2.hdslb.com/bfs/face/8777c8bd3083f9f823445e84f46c3b5dd8b93380.jpg",
                "mid": 520011242,
                "name": "MED_Lucient__"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1624y1e7JJ",
            "cnt_info": {
                "collect": 1400,
                "danmaku": 44,
                "play": 80243
            },
            "cover": "https://i2.hdslb.com/bfs/archive/35998b53f5bddbc92ea9007d97d65071208553d4.jpg",
            "duration": 112,
            "fav_time": 1674031386,
            "id": 692510702,
            "intro": "模型作者by_takoyaki.raw",
            "page": 1,
            "publish_time": 1673492400,
            "title": "[原神] x [莉可丽丝] “今天天气很好，我也精神满满，真好”Lycoris所属，代号LC2808，锦木千束，登陆！",
            "upper": {
                "face": "https://i1.hdslb.com/bfs/face/9d998af488de31883abb56d416c5b393f90a0415.gif",
                "mid": 769105,
                "name": "嫁人的少女"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1yM411h74d",
            "cnt_info": {
                "collect": 119586,
                "danmaku": 303,
                "play": 932450
            },
            "cover": "https://i0.hdslb.com/bfs/archive/31eda1f16f6d6ee6cfaf7fe87bb1848b511d8faa.jpg",
            "duration": 70,
            "fav_time": 1673177354,
            "id": 522207629,
            "intro": "-",
            "page": 1,
            "publish_time": 1672631267,
            "title": "惊天Bug??下线重上就能刷新宝箱",
            "upper": {
                "face": "https://i0.hdslb.com/bfs/face/561d9cfadbc943aabf7f4ff777d0eafcbeda89f5.jpg",
                "mid": 3493089123502938,
                "name": "流浪者小散兵"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1g14y1p7nH",
            "cnt_info": {
                "collect": 4945,
                "danmaku": 0,
                "play": 39473
            },
            "cover": "https://i1.hdslb.com/bfs/archive/0fca9b8e8f11ab97213dc329b851a77e2e12000e.jpg",
            "duration": 614,
            "fav_time": 1672578295,
            "id": 775415118,
            "intro": "白铁矿 高效速刷路线！",
            "page": 1,
            "publish_time": 1669208926,
            "title": "原神白铁矿速刷点位，7分钟111个高效便捷。",
            "upper": {
                "face": "https://i1.hdslb.com/bfs/face/dd1d66600cb3e4f24fc79c716ca106eeda0ece9f.jpg",
                "mid": 412276207,
                "name": "阿炜原神"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1Z84y167cY",
            "cnt_info": {
                "collect": 55347,
                "danmaku": 916,
                "play": 764598
            },
            "cover": "https://i2.hdslb.com/bfs/archive/0baf4deb80d9bda50180a0deb817504cf1958461.jpg",
            "duration": 191,
            "fav_time": 1672573323,
            "id": 605959769,
            "intro": "",
            "page": 1,
            "publish_time": 1670342559,
            "title": "原神：从欧皇那里偷学的玄学抽卡技巧！",
            "upper": {
                "face": "https://i0.hdslb.com/bfs/face/8f5b0cca8c28d0e0c2ad8d19d96c19de64b14d6c.jpg",
                "mid": 26705184,
                "name": "拾柒酱紫吖"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1Qe411j7xa",
            "cnt_info": {
                "collect": 183560,
                "danmaku": 1282,
                "play": 3077608
            },
            "cover": "https://i0.hdslb.com/bfs/archive/a3b09e634451961e11d47c19024a0dcdce3ceca4.jpg",
            "duration": 673,
            "fav_time": 1672569723,
            "id": 261352890,
            "intro": "1 须弥哈哈镜\n2须弥花样跳水\n3须弥悬崖双人打卡点\n4须弥滑滑梯\n5群玉阁夕阳红\n6璃月跑步机\n7比翼双飞\n8小个快乐坡\n9风龙废墟打卡点\n10须弥空气墙\n11梯子走秀\n12骑士踢\n13原魔小姐姐之舞\n14五香岩见证的爱情\n15早柚画爱心\n16流星时刻\n17踏鞴砂浪漫海滩\n18蒙德城神像\n19渊下宫打卡点\n20须弥雨幕\n21璃月滑滑梯\n22明蕴镇双人看日落\n23猫猫云\n24双人快乐菇\n25花之桥\n26-30爱心打卡点\n31-39其他打卡点\n末尾：彩蛋",
            "page": 1,
            "publish_time": 1664974912,
            "title": "盘点39个你不一定知道原神网红打卡点",
            "upper": {
                "face": "https://i1.hdslb.com/bfs/face/a990d058125253dc0cffa66aa27f2a298108fbb0.jpg",
                "mid": 1756185076,
                "name": "提瓦特老村长"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1HM411z75u",
            "cnt_info": {
                "collect": 26849,
                "danmaku": 160,
                "play": 770741
            },
            "cover": "https://i0.hdslb.com/bfs/archive/f8ca72527a9fb51c8328f1cfd6a76a1ea860efa8.jpg",
            "duration": 179,
            "fav_time": 1671619135,
            "id": 521074242,
            "intro": "",
            "page": 1,
            "publish_time": 1670555842,
            "title": "原神1级就能从蒙德偷渡到稻妻的方法，我们好像走到了世界的尽头",
            "upper": {
                "face": "https://i1.hdslb.com/bfs/face/76a805cc27075752fdee4dd6aa35a393e0582afc.jpg",
                "mid": 1896554362,
                "name": "易神易魔啊"
            }
        },
        {
            "attr": 0,
            "bvid": "BV19G4y1G7fF",
            "cnt_info": {
                "collect": 34123,
                "danmaku": 676,
                "play": 408608
            },
            "cover": "https://i0.hdslb.com/bfs/archive/c9aa2bcfb8d33e3477bf588915dda50138393402.jpg",
            "duration": 243,
            "fav_time": 1671274399,
            "id": 818298593,
            "intro": "做了很长时间的男生女生都能看的散兵/流浪者声线教学来啦！大家在伪音过程中一定要注意保护嗓子哦！视频仅代表个人观点，如有错误，欢迎在评论区指出！最后喜欢记得点个关注点个赞，下期更新会更快！",
            "page": 1,
            "publish_time": 1670082311,
            "title": "流浪者(散兵)的声线教学——男生女生都能学！",
            "upper": {
                "face": "https://i1.hdslb.com/bfs/face/921ecd1778c9ee92698fa755dde7ffbb380aedd8.jpg",
                "mid": 405845641,
                "name": "Happy_Twins"
            }
        },
        {
            "attr": 0,
            "bvid": "BV14G4y1R7Ps",
            "cnt_info": {
                "collect": 38623,
                "danmaku": 273,
                "play": 494590
            },
            "cover": "https://i1.hdslb.com/bfs/archive/659bbdc24377531951356ba9b2c69fda02659e3f.jpg",
            "duration": 142,
            "fav_time": 1670845515,
            "id": 860843467,
            "intro": "-",
            "page": 1,
            "publish_time": 1670050979,
            "title": "一个视频让萌新旅行者赢在起跑线上",
            "upper": {
                "face": "https://i1.hdslb.com/bfs/face/a990d058125253dc0cffa66aa27f2a298108fbb0.jpg",
                "mid": 1756185076,
                "name": "提瓦特老村长"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1SM411r7Nc",
            "cnt_info": {
                "collect": 35749,
                "danmaku": 421,
                "play": 586445
            },
            "cover": "https://i2.hdslb.com/bfs/archive/0fdf544b029894d2b07788a9c8c4a8bcd83efd6f.jpg",
            "duration": 63,
            "fav_time": 1670844684,
            "id": 520504184,
            "intro": "-",
            "page": 1,
            "publish_time": 1669450087,
            "title": "让旅行者记忆犹新的NPC们",
            "upper": {
                "face": "https://i1.hdslb.com/bfs/face/a990d058125253dc0cffa66aa27f2a298108fbb0.jpg",
                "mid": 1756185076,
                "name": "提瓦特老村长"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1uP411P7KR",
            "cnt_info": {
                "collect": 30166,
                "danmaku": 1128,
                "play": 1034118
            },
            "cover": "https://i2.hdslb.com/bfs/archive/735cdfe0b2e0e566011815bede42b26be56b1ee7.jpg",
            "duration": 601,
            "fav_time": 1670815335,
            "id": 304505198,
            "intro": "相关游戏：《纪念碑谷》",
            "page": 1,
            "publish_time": 1667016284,
            "title": "14年爆火的解谜游戏，《纪念碑谷》竟然隐藏了如此压抑的剧情？！",
            "upper": {
                "face": "https://i1.hdslb.com/bfs/face/22d1ece56cd2a3a82dfe626469fd8837826e3552.jpg",
                "mid": 293846287,
                "name": "硬的小软"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1RV4y1M7dY",
            "cnt_info": {
                "collect": 26028,
                "danmaku": 581,
                "play": 1622085
            },
            "cover": "https://i0.hdslb.com/bfs/archive/3958faf29152c47c8fe272caf9590087fc00ca9b.jpg",
            "duration": 109,
            "fav_time": 1670815247,
            "id": 858197915,
            "intro": "整点旧活，趁着烟花穿墙还没和谐，赶紧下来探索探索",
            "page": 1,
            "publish_time": 1663388801,
            "title": "【原神】离谱！风龙废墟下的隐藏彩蛋（地下还有空间？）",
            "upper": {
                "face": "https://i2.hdslb.com/bfs/face/1e100316a9fb4b2c09bdc3409b26c1b1ee25f04b.jpg",
                "mid": 15112013,
                "name": "一半月X"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1r8411j7in",
            "cnt_info": {
                "collect": 36749,
                "danmaku": 236,
                "play": 884923
            },
            "cover": "https://i1.hdslb.com/bfs/archive/8df3790e8d8f33ff989bcb3048cf01673d545c3f.jpg",
            "duration": 102,
            "fav_time": 1670815194,
            "id": 220210985,
            "intro": "-",
            "page": 1,
            "publish_time": 1668515207,
            "title": "7个牺牲旅行者才能完成的成就",
            "upper": {
                "face": "https://i1.hdslb.com/bfs/face/a990d058125253dc0cffa66aa27f2a298108fbb0.jpg",
                "mid": 1756185076,
                "name": "提瓦特老村长"
            }
        },
        {
            "attr": 0,
            "bvid": "BV1N24y1f7ae",
            "cnt_info": {
                "collect": 121722,
                "danmaku": 334,
                "play": 995180
            },
            "cover": "https://i1.hdslb.com/bfs/archive/2c624885e2f7fd3a501c468c9b16c4b2b4e8e9ce.jpg",
            "duration": 456,
            "fav_time": 1670815194,
            "id": 689702440,
            "intro": "",
            "page": 1,
            "publish_time": 1667361128,
            "title": "远吕羽氏遗事任务全流程210原石一长枪图纸",
            "upper": {
                "face": "https://i2.hdslb.com/bfs/face/ad1f831bf06bdc970aae3b3ec4182234300d0701.jpg",
                "mid": 1662158531,
                "name": "小张张原神"
            }
        }
    ],
    "title": "其他游戏",
    "user": {
        "create_time": 1670815074,
        "mid": 450196722,
        "name": "grhrhd123"
    },
    "view": 0
}
```
</details>