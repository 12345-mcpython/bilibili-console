# LBCC

## 介绍
Laosun Bilibili Console Client(LBCC) 是一个Bilibili命令行客户端.

![](https://laosun-image.obs.cn-north-4.myhuaweicloud.com/20220926123050.png)

## 实现功能/将要实现的功能
----

- [ ] 用户
    - [x] 登录.
       - [x] 密码登录.
       - [x] 二维码登录.
       - [x] 手机验证码登录.
    - [x] 取消登录.
    - [ ] 消息中心.
    - [ ] 个人中心.
   
- [ ] 视频.
   - [x] 推荐
   - [x] 播放
   - [x] 视频信息
   - [x] 合集预览与播放
   - [x] 预览评论.
   - [x] 点赞 & 投币 & 收藏
   - [ ] 评论.
   - [ ] 转发.
   - [ ] *发送弹幕.
   - [ ] -投稿视频.

- [ ] 排行榜
  - [ ] 入站必刷
  - [ ] 排行榜
  - [ ] 综合热门
  - [ ] 每周必看
   
- [ ] 番剧.
   - [ ] 推荐
   - [ ] 基本信息
   - [x] 通过地址播放   

- [ ] 搜索
  - [x] 视频搜索
  - [ ] 热搜
  - [ ] *搜索建议
  
   
- [x] 收藏夹
   - [x] 预览收藏夹
   - [ ] 创建收藏夹
   - [ ] 删除收藏夹  
   - [ ] 删除收藏内容
   
- [ ] 专栏

(带*的表示目前技术(播放器,控制台等)暂不可实现的功能)

(带-的表示有风险的功能)

## 使用

0. 安装python与mpv
1. pip install -r requirements.txt
2. python main.py

## 致谢

[yutto-dev/biliass](https://github.com/yutto-dev/biliass/) 提供弹幕转换

[mpv-player/mpv](https://github.com/mpv-player/mpv/issues) 提供播放器

[SocialSisterYi/bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect/) 提供部分b站API
