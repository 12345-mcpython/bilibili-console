# LBCC使用教程

## 1.1 下载并安装

这些内容仅限于[ec225094](https://github.com/12345-mcpython/bilibili-console/commit/ec22509402d7519d868c46ae52bdac70f423e747) 这个提交之前。

首先安装 [python](http://www.python.org/downloads) 和 [mpv](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/mpv.exe)

然后 `git clone https://github.com/12345-mcpython/bilibili-console` 或

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011121641.png)

并解压zip

打开命令行，切换到此文件夹或对文件夹Shift+右键，点击"在命令行打开此文件夹" (在Win11中可以直接右键打开终端)

输入 `pip install -r requirements.txt`

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011122441.png)

等待安装完成, 输入 `python main.py`

根据情况配置cookie.

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011205556.png)

输入 `python main.py`

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011205705.png)

## 1.2 主界面命令

### 1.2.1 address + <url/bvid/aid> 通过地址播放

输入 `address <url/bvid/aid>` 比如 `address https://www.bilibili.com/video/BV16U4y1k7UU/` 按下回车. 进入播放界面。

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011205914.png)

1. 输入 `play` 播放视频
2. 输入 `like` 点赞视频
3. 输入 `unlike` 取消点赞
4. 输入 `coin <投币数 1-2>` 投币视频
5. 输入 `triple` 三连
6. 输入 `collection` 收藏视频
7. 输入 `view_collection` 查看视频合集
8. 输入 `video_info` 查看视频详细信息
9. 输入 `view_comment` 查看视频评论

### 1.2.2 recommend 推荐界面

输入 `recommend` 进入推荐界面

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221015195209.png)

操作命令与 `address` 命令相同.

### 1.2.3 favorite 收藏夹界面

输入 `recommend` 进入收藏夹界面

选择一个收藏夹

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221015202000.png)

操作命令除了删除了命令 `collection` 了与 `address` 命令相同. 

### 1.2.4 search 搜索界面

输入 `search` 进入搜索界面

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221015202341.png)

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221015202357.png)

操作命令与 `address` 命令相同.

### 1.2.5 manage_user 管理用户

### 1.2.6 config 设置

清空本地缓存可以清除弹幕的缓存, 清空内存缓存可以清除缓存的请求, 调整分辨率可以调整视频的分辨率.



