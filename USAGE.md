# LBCC使用教程

## 1.1 下载并安装

首先安装 [python](http://www.python.org/downloads) 和 [mpv](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/mpv.exe)

然后 `git clone https://github.com/12345-mcpython/bilibili-console` 或

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011121641.png)

并解压zip

打开命令行，切换到此文件夹或对文件夹Shift+右键，点击"在命令行打开此文件夹" (在Win11中可以直接右键打开终端)

输入 `pip install -r requirements.txt`

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011122441.png)

~~根据情况配置cookie.~~

到b站网页端, 手动拷贝cookie(按F12, 到Network 网络 标签页, 按F12, 翻到最上面找到第一个www.bilibili.com点击, 找到Response Header 请求标头 找到cookie选择并复杂这堆cookie)并新建文件cookie.txt, 把拷贝内容复制到这个文件.

每次使用LBCC都需要这么做.(似乎b站网页版cookie时长减小很多)

输入 `python main.py`

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011205705.png)

## 1.2 主界面命令

### 1.2.1 address ~~+ <url/bvid/aid>~~ 通过地址播放

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011205914.png)

先输入视频前面的数字选择, 再输入操作指令.

1. `play` 播放视频
2. `download` 下载视频
~~2. 输入 `like` 点赞视频~~
~~3. 输入 `unlike` 取消点赞~~
~~4. 输入 `coin <投币数 1-2>` 投币视频~~
~~5. 输入 `triple` 三连~~
~~6. 输入 `collection` 收藏视频~~
~~7. 输入 `view_collection` 查看视频合集~~
~~8. 输入 `video_info` 查看视频详细信息~~
~~9. 输入 `view_comment` 查看视频评论~~

### 1.2.2 recommend 推荐界面

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221015195209.png)

~~操作命令与 `address` 命令相同.~~

(以下全为失效内容, 仅供存档)

~~### 1.2.3 favorite 收藏夹界面~~

~~输入 `recommend` 进入收藏夹界面~~

~~选择一个收藏夹~~

~~操作命令除了删除了命令 `collection` 了与 `address` 命令相同.~~

~~### 1.2.4 search 搜索界面~~

~~输入 `search` 进入搜索界面~~

~~操作命令与 `address` 命令相同.~~

~~### 1.2.5 manage_user 管理用户~~

~~### 1.2.6 config 设置~~

~~清空本地缓存可以清除弹幕的缓存, 清空内存缓存可以清除缓存的请求, 调整分辨率可以调整视频的分辨率.~~



