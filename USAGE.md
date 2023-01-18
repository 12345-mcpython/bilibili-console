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

使用LBCC就尽量不要使用b站网页端了.(似乎b站网页版会自动刷新并废弃cookie)

输入 `python main.py`

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011205705.png)

## 1.2 主界面指令

### 1.2.1 address 通过地址播放

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221011205914.png)

先输入视频前面的数字选择, 再输入指令.

### 指令集

1. `play` 播放视频
2. `download` 下载视频
3. `like` 点赞视频
4. `unlike` 取消点赞
5. `coin` 投币视频
6. `triple` 三连

### 1.2.2 recommend 推荐界面

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20221015195209.png)

指令集与 `address` 指令相同.




