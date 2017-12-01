#!/bin/bash
# ===============================================================
#   Copyright (C) 2015 Bigdata Inc. All rights reserved.
#
#   @file：cmd.sh
#   @author：Song Wanli <wanli.song@foxmail.com>
#   @date：2015-04-20
#   @desc： sh cmd.sh (start|stop|restart)
#   @update：
# ================================================================

## 1.global conf
run_cmd=$1
port=10192
process_num=4
if [ $# -ge 2 ];then
    process_num=$2
fi
thread_num=10
mode=0
. ../../common/mysql_account.sh
if [ ! -d "./log" ];then
  mkdir log
fi

## 2,run
case $run_cmd in
    start)
        ## start
        nohup ../tornado/babysitter -r data@36kr.com python ../seo/server.py --port=$port --mode=$mode --processes=$process_num --threads=$thread_num --logdir=./log/ >/dev/null 2>&1 &
        ;;
    stop)
        ## stop
        for pid in `ps aux|grep "server.py --port=$port " |grep -v grep| awk '{print $2}'`
        do
            echo $pid
            kill -9 $pid
        done
        ;;
    restart)
        ## restart
        for pid in `ps aux|grep "server.py --port=$port " |grep -v grep| awk '{print $2}'`
        do
            echo $pid
            kill -9 $pid
        done
        nohup ../tornado/babysitter -r data@36kr.com python ../seo/server.py --port=$port --mode=$mode --processes=$process_num --threads=$thread_num --logdir=./log/ >/dev/null 2>&1 &
        ;;
    *)
        ## test
        curl "127.0.0.1:10192?cmd=extractKeyWords&article=%7B%22content%22%3A%20%22%3Cp%3E%3Ca%20href%3D%5C%22http%3A//www.36kr.com/guoguo-instagram-for-video/attachment/002/%5C%22%3E%3C/a%3E%3Ca%20href%3D%5C%22http%3A//www.36kr.com/guoguo-instagram-for-video/attachment/001/%5C%22%3E%3Cimg%20src%3D%5C%22http%3A//static.36kr.com/wp-content/uploads/2011/03/001.jpg%5C%22%20alt%3D%5C%22%5C%22%20/%3E%3C/a%3E%3Cimg%20src%3D%5C%22http%3A//static.36kr.com/wp-content/uploads/2011/03/002.jpg%5C%22%20alt%3D%5C%22%5C%22%20/%3E%3Ca%20href%3D%5C%22http%3A//www.36kr.com/guoguo-instagram-for-video/attachment/003/%5C%22%3E%3Cimg%20src%3D%5C%22http%3A//static.36kr.com/wp-content/uploads/2011/03/003.jpg%5C%22%20alt%3D%5C%22%5C%22%20/%3E%3C/a%3E%3Cbr%20/%3E%E6%AF%8F%E5%A4%A9%E9%83%BD%E5%90%AC%E5%88%B0%E5%A4%A7%E5%AE%B6%E5%9C%A8%E8%B0%88%E8%AE%BA%E7%A4%BE%E4%BC%9A%E5%8C%96%E7%85%A7%E7%89%87%E5%88%86%E4%BA%AB%E5%BA%94%E7%94%A8Instagram%20%EF%BC%8C%E5%8F%AF%E6%98%AF%E4%BD%A0%E6%9C%89%E6%B2%A1%E6%9C%89%E6%83%B3%E8%BF%87%E8%BF%99%E4%B8%AA%E9%97%AE%E9%A2%98%EF%BC%9A%E4%B8%8B%E4%B8%80%E4%B8%AA%E7%A4%BE%E4%BC%9A%E5%8C%96%E5%86%85%E5%AE%B9%E5%88%86%E4%BA%AB%E7%9A%84%E6%B5%AA%E6%BD%AE%E4%BC%9A%E5%9C%A8%E4%BD%95%E6%97%B6%E4%BB%A5%E4%BD%95%E7%A7%8D%E6%96%B9%E5%BC%8F%E5%88%B0%E6%9D%A5%EF%BC%9F%E5%A6%82%E6%9E%9C%E4%BD%A0%E5%92%8C%E6%88%91%E4%B8%80%E6%A0%B7%E6%80%9D%E8%80%83%E8%BF%87%E8%BF%99%E4%B8%AA%E9%97%AE%E9%A2%98%EF%BC%8C%E4%BB%8A%E5%A4%A9%E4%BC%B0%E8%AE%A1%E5%B0%B1%E6%9C%89%E7%AD%94%E6%A1%88%E4%BA%86%E2%80%94%E2%80%94%E9%82%A3%E5%B0%B1%E6%98%AF%E7%A4%BE%E4%BC%9A%E5%8C%96%E8%A7%86%E9%A2%91%E5%88%86%E4%BA%AB%E5%BA%94%E7%94%A8%E3%80%82%3C/p%3E%3Cp%3E%E5%88%9B%E4%B8%9A%E5%85%AC%E5%8F%B8%40%E8%9D%88%E8%9D%88%E8%A7%86%E9%A2%91%20%E7%9A%84%E4%BA%A7%E5%93%81%E5%B0%B1%E6%98%AF%E4%B8%80%E4%B8%AA%E8%A7%86%E9%A2%91%E7%89%88%20Instagram%E3%80%82%E4%B8%80%E7%9B%B4%E5%85%B3%E6%B3%A8%3Cbr%20/%3E%3Ca%20href%3D%5C%22http%3A//t.sina.com.cn/wow36kr%5C%22%3E%3Ca%20href%3D%5C%22/36%5C%22%20title%3D%5C%22%4036%5C%22%3E%3Ci%3E%40%3C/i%3E36%3C/a%3E%E6%B0%AA%3C/a%3E%20%E7%9A%84%E8%AF%BB%E8%80%85%E5%BA%94%E8%AF%A5%E9%83%BD%E5%B7%B2%E7%BB%8F%E7%9F%A5%E9%81%93%EF%BC%8C%3Cbr%20/%3E%3Ca%20href%3D%5C%22http%3A//www.36kr.com/socialcam-justin-tv-instagram/%5C%22%3EJustin.tv%20%E4%B9%9F%E5%B0%86%E5%9C%A8%E4%B8%8B%E4%B8%AA%E6%9C%88%E5%87%BA%E5%93%81%E8%A7%86%E9%A2%91%E7%89%88%20Instagram%20%E2%80%94%C2%A0Socialcam%3C/a%3E%E3%80%82%E4%B8%8D%E8%BF%87%E8%BF%99%E6%AC%A1%E4%BC%B0%E8%AE%A1%E8%A6%81%E8%AE%A9%E5%8F%A6%E5%A4%96%E4%B8%80%E5%AE%B6%E5%88%9B%E4%B8%9A%E5%85%AC%E5%8F%B8%3Cbr%20/%3E%3Ca%20href%3D%5C%22http%3A//t.sina.com.cn/guoguoshipin%5C%22%3E%40%E8%9D%88%E8%9D%88%E8%A7%86%E9%A2%91%3C/a%3E%20%E6%8A%A2%E4%BA%86%E5%85%88%E4%BA%86%E3%80%82%3C/p%3E%3Cp%3E%E5%92%8CInstagram%20%E5%88%86%E4%BA%AB%E7%85%A7%E7%89%87%E4%B8%8D%E4%B8%80%E6%A0%B7%E7%9A%84%E6%98%AF%EF%BC%8C%40%E8%9D%88%E8%9D%88%E8%A7%86%E9%A2%91%20%E7%9A%84%E7%94%A8%E6%88%B7%E5%8F%AF%E4%BB%A5%E6%8B%8D%E6%91%84%E3%80%81%E4%B8%8A%E4%BC%A0%E5%88%86%E4%BA%AB%E7%9A%84%E6%98%AF%E6%9C%80%E9%95%BF3%E5%88%86%E9%92%9F%E7%9A%84%E8%A7%86%E9%A2%91%E3%80%82%E7%94%A8%E6%88%B7%E5%8F%AF%E4%BB%A5%E9%80%9A%E8%BF%87%E5%85%B3%E6%B3%A8%E5%A5%BD%E5%8F%8B%E6%88%96%E8%80%85%E9%99%8C%E7%94%9F%E4%BA%BA%EF%BC%8C%E8%B7%9F%E8%B8%AA%E4%BB%96%E4%BB%AC%E6%8B%8D%E6%91%84%E5%88%86%E4%BA%AB%E7%9A%84%E8%A7%86%E9%A2%91%EF%BC%9B%E8%BF%98%E5%8F%AF%E4%BB%A5%E5%8E%BB%E5%B9%BF%E5%9C%BA%E4%B8%AD%E7%9C%8B%E5%88%B0%E6%89%80%E6%9C%89%E7%94%A8%E6%88%B7%E6%8B%8D%E6%91%84%E5%88%86%E4%BA%AB%E7%9A%84%E8%A7%86%E9%A2%91%E3%80%82%E8%BF%99%E4%BA%9B%E5%9F%BA%E6%9C%AC%E7%9A%84%E9%80%BB%E8%BE%91%E4%B8%8EInstagram%20%E7%B1%BB%E4%BC%BC%E3%80%82%3C/p%3E%3Cp%3E%E4%B8%8D%E8%BF%87%E8%A7%86%E9%A2%91%E7%9B%B8%E8%BE%83%E4%BA%8E%E5%9B%BE%E7%89%87%EF%BC%8C%E5%A4%84%E7%90%86%E7%9A%84%E9%9A%BE%E5%BA%A6%E5%B0%B1%E8%A6%81%E5%A4%A7%E5%BE%88%E5%A4%9A%E4%BA%86%E3%80%82%E5%9B%A0%E6%AD%A4%E5%9C%A8%E7%94%A8%E6%88%B7%E4%BD%93%E9%AA%8C%E6%96%B9%E4%BE%BF%EF%BC%8C%E8%9D%88%E8%9D%88%E8%A7%86%E9%A2%91%E7%9A%84%E5%9B%A2%E9%98%9F%E4%B8%8B%E4%BA%86%E5%BE%88%E5%A4%A7%E5%8A%9F%E5%A4%AB%E3%80%82%3C/p%3E%3Cp%3E%E6%AF%94%E5%A6%82%EF%BC%8C%E2%80%9C%E4%B8%8A%E4%BC%A0%E2%80%9D%E8%BF%99%E4%B8%AA%E7%8A%B6%E6%80%81%E5%AF%B9%E7%94%A8%E6%88%B7%E6%9D%A5%E8%AF%B4%E6%98%AF%E4%B8%8D%E5%8F%AF%E8%A7%81%E7%9A%84%EF%BC%8C%E7%94%A8%E6%88%B7%E6%8B%8D%E5%AE%8C%E8%A7%86%E9%A2%91%E4%B8%8D%E9%9C%80%E8%A6%81%E7%AD%89%E5%BE%85%E5%B0%B1%E5%8F%AF%E4%BB%A5%E5%8E%BB%E5%B9%B2%E5%88%AB%E7%9A%84%E4%BA%8B%E6%83%85%E4%BA%86%E3%80%82%E5%9B%A0%E4%B8%BA%E7%94%A8%E6%88%B7%E5%9C%A8%E6%8B%8D%E6%91%84%E8%A7%86%E9%A2%91%E7%9A%84%E8%BF%87%E7%A8%8B%E4%B8%AD%EF%BC%8C%E8%A7%86%E9%A2%91%E5%B0%B1%E5%B7%B2%E7%BB%8F%E5%BC%80%E5%A7%8B%E4%B8%8A%E4%BC%A0%E3%80%82%E6%8B%8D%E6%91%84%E5%AE%8C%E6%88%90%E5%90%8E%EF%BC%8C%E7%94%A8%E6%88%B7%E7%82%B9%E5%87%BB%E2%80%9C%3Cbr%20/%3E%E7%BB%93%E6%9D%9F%E2%80%9D%E6%8C%89%E9%92%AE%E5%8D%B3%E5%8F%AF%E9%80%80%E5%87%BA%E5%BD%95%E5%88%B6%E3%80%82%E6%AD%A4%E6%97%B6%E5%A6%82%E6%9E%9C%E7%BD%91%E7%BB%9C%E7%8A%B6%E6%80%81%E5%BE%88%E5%A5%BD%EF%BC%8C%E8%A7%86%E9%A2%91%E5%8F%AF%E8%83%BD%E5%B7%B2%E7%BB%8F%E4%B8%8A%E4%BC%A0%E5%AE%8C%E6%88%90%EF%BC%8C%E4%BD%A0%E5%B0%B1%E5%8F%AF%E4%BB%A5%E5%88%B7%E6%96%B0%E8%87%AA%E5%B7%B1%E7%9A%84%E9%A1%B5%E9%9D%A2%E7%9C%8B%E5%88%B0%E5%88%9A%E5%88%9A%E5%BD%95%E5%88%B6%E7%9A%84%E8%A7%86%E9%A2%91%E4%BA%86%EF%BC%9B%E5%A6%82%E6%9E%9C%E7%BD%91%E7%BB%9C%E8%B4%A8%E9%87%8F%E4%B8%8D%E5%A4%AA%E5%A5%BD%EF%BC%8C%E8%A7%86%E9%A2%91%E4%B8%8A%E4%BC%A0%E4%BC%9A%E5%9C%A8%E5%90%8E%E5%8F%B0%E7%BB%A7%E7%BB%AD%E8%87%AA%E5%8A%A8%E8%BF%9B%E8%A1%8C%EF%BC%8C%E7%9B%B4%E5%88%B0%E5%AE%8C%E6%88%90%E3%80%82%3C/p%3E%3Cp%3E%E6%AD%A4%E5%A4%96%EF%BC%8C%E5%9C%A8%E8%A7%86%E9%A2%91%E5%A4%A7%E5%B0%8F%E3%80%81%E8%B4%A8%E9%87%8F%E4%B8%8A%EF%BC%8C%E8%9D%88%E8%9D%88%E8%A7%86%E9%A2%91%E5%9B%A2%E9%98%9F%E4%B9%9F%E8%BF%9B%E8%A1%8C%E4%BA%86%E5%BE%88%E5%A4%9A%E6%B5%8B%E8%AF%95%EF%BC%8C%E8%80%83%E8%99%91%E4%BA%86%E8%A7%86%E9%A2%91%E8%B4%A8%E9%87%8F%E5%92%8C%E7%BD%91%E7%BB%9C%E9%80%9F%E5%BA%A6%E7%AD%89%E5%A4%9A%E6%96%B9%E9%9D%A2%E5%9B%A0%E7%B4%A0%E3%80%82%3C/p%3E%3Cp%3E%E7%9B%AE%E5%89%8D%EF%BC%8C%E8%9D%88%E8%9D%88%E8%A7%86%E9%A2%91%E7%9A%84iOS%E3%80%81Android%20%E5%BA%94%E7%94%A8%E9%83%BD%E5%B7%B2%E7%BB%8F%E6%8E%A8%E5%87%BA%E5%B9%B6%E6%8F%90%E4%BE%9B%E4%B8%8B%E8%BD%BD%EF%BC%88%3Cbr%20/%3E%3Ca%20href%3D%5C%22http%3A//a.guoguo.me/GuoguoVideo.ipa%5C%22%3EiOS%E8%B6%8A%E7%8B%B1%E7%89%88%3C/a%3E%EF%BC%8C%3Cbr%20/%3E%3Ca%20href%3D%5C%22http%3A//a.guoguo.me/guoguoVideo.apk%5C%22%3EAndroid%E7%89%88%3C/a%3E%EF%BC%89%E3%80%82%E6%84%9F%E5%85%B4%E8%B6%A3%E7%9A%84%3Cbr%20/%3E%3Ca%20href%3D%5C%22http%3A//t.sina.com.cn/wow36kr%5C%22%3E%3Ca%20href%3D%5C%22/36%5C%22%20title%3D%5C%22%4036%5C%22%3E%3Ci%3E%40%3C/i%3E36%3C/a%3E%E6%B0%AA%3C/a%3E%20%E8%AF%BB%E8%80%85%E5%8F%AF%E4%BB%A5%E5%85%88%E5%8E%BB%E4%B8%8B%E8%BD%BD%E5%BA%94%E7%94%A8%E7%A8%8B%E5%BA%8F%EF%BC%8C%E7%84%B6%E5%90%8E%E6%89%93%E5%BC%80%E5%BA%94%E7%94%A8%E7%A8%8B%E5%BA%8F%EF%BC%8C%E5%9C%A8%E9%82%80%E8%AF%B7%E7%A0%81%E5%A4%84%E8%BE%93%E5%85%A5%3Cbr%20/%3E%E2%80%9836kr%E2%80%99%E5%8D%B3%E5%8F%AF%EF%BC%881000%E6%AC%A1%E5%90%8E%E8%87%AA%E5%8A%A8%E5%A4%B1%E6%95%88%EF%BC%89%EF%BC%8C%E6%95%B0%E9%87%8F%E6%9C%89%E9%99%90%EF%BC%8C%E5%85%88%E5%88%B0%E5%85%88%E5%BE%97%E5%93%A6%EF%BD%9E%EF%BC%88%E8%AF%B7%E5%9C%A8Wifi%E3%80%81WCDMA%E3%80%81CDMA2000%20%E7%BD%91%E7%BB%9C%E4%B8%8B%E4%BD%BF%E7%94%A8%EF%BC%89%E3%80%82%3C/p%3E%3Cp%3E%3Ca%20href%3D%5C%22http%3A//www.36kr.com/guoguo-instagram-for-video/guoguo-me/%5C%22%3E%3Cimg%20src%3D%5C%22http%3A//static.36kr.com/wp-content/uploads/2011/03/guoguo.me_.png%5C%22%20alt%3D%5C%22%5C%22%20/%3E%3C/a%3E%3C/p%3E%22%2C%20%22descrip%22%3A%20%22%E8%9D%88%E8%9D%88%E8%A7%86%E9%A2%91%22%2C%20%22tags%22%3A%20%5B%22%E7%A4%BE%E4%BA%A4%E7%BD%91%E7%BB%9C%22%2C%20%22%E8%AF%AD%E9%9F%B3%E8%A7%86%E9%A2%91%E7%A4%BE%E4%BA%A4%22%5D%2C%20%22title%22%3A%20%22%E7%A4%BE%E4%BC%9A%E5%8C%96%E5%86%85%E5%AE%B9%E5%88%86%E4%BA%AB%E7%9A%84%E4%B8%8B%E4%B8%80%E4%B8%AA%E6%B5%AA%E6%BD%AE%EF%BC%9F%E8%9D%88%E8%9D%88%E8%A7%86%E9%A2%91%E2%80%94%E2%80%94%E8%A7%86%E9%A2%91%E7%89%88%20Instagram%E3%80%90%E9%99%841000%E4%B8%AA%E9%82%80%E8%AF%B7%E7%A0%81%E3%80%91%22%7D"

        curl "127.0.0.1:10192?cmd=extractArticle&id=16560"
        curl  -d "cmd=extractArticle&content=%26lt%3bdiv+class%3d%26quot%3barccontent%26quot%3b%26gt%3b%0d%0a++++++++++++++++++++++++++++++++++%26lt%3bcenter%26gt%3b%26lt%3ba+href%3d%26quot%3bhttp%3a%2f%2flist.qq.com%2fcgi-bin%2fqf_invite%3fid%3d7423582f2418886676ddcc05a088c0a8b201e065c69f95cb%26quot%3b+title%3d%26quot%3b%e6%88%91%e4%bb%ac%e5%b0%86%e4%b8%8d%e5%ae%9a%e6%9c%9f%e5%90%91%e6%82%a8%e6%8e%a8%e9%80%81Web%e6%95%b0%e6%8d%ae%e6%8a%93%e5%8f%96%e6%96%b0%e6%8a%80%e6%9c%af%e3%80%81%e6%96%b0%e6%96%b9%e6%a1%88%e4%bb%a5%e5%8f%8a%e5%88%86%e4%ba%ab%e6%88%91%e4%bb%ac%e7%9a%84%e7%bb%8f%e9%aa%8c%e3%80%82%26quot%3b+target%3d%26quot%3b_blank%26quot%3b%26gt%3b%26lt%3bimg+alt%3d%26quot%3b%e8%ae%a2%e9%98%85%e5%88%b0%e9%82%ae%e7%ae%b1%26quot%3b+src%3d%26quot%3bhttp%3a%2f%2frescdn.list.qq.com%2fzh_CN%2fhtmledition%2fimages%2fqunfa%2fmanage%2fpicMode_light_s.png%26quot%3b%26gt%3b%26lt%3b%2fa%26gt%3b%26lt%3b%2fcenter%26gt%3b%0d%0a%09%09%09%09++%26lt%3bp%26gt%3b%e7%99%be%e5%ba%a6%e6%8c%87%e6%95%b0%e7%b3%bb%e7%bb%9f%e7%9a%84%e5%8f%8d%e9%87%87%e9%9b%86%e7%ad%96%e7%95%a5%e6%af%94%e8%be%83%e4%b8%a5%e6%a0%bc%ef%bc%8c%e4%b8%8d%e8%ae%ba%e6%98%af%e8%bf%87%e5%8e%bb%e7%9a%84Flash%e7%89%88%e6%9c%ac%e8%bf%98%e6%98%af%e7%8e%b0%e5%9c%a8%e7%9a%84Web%e7%89%88%e6%9c%ac%ef%bc%8c%e6%9c%8d%e5%8a%a1%e5%99%a8%e5%ba%94%e7%ad%94%e7%9a%84%e6%a0%b8%e5%bf%83%e6%95%b0%e6%8d%ae%e5%9d%87%e6%9c%89%e5%8a%a0%e5%af%86%ef%bc%8c%e4%bd%bf%e5%be%97%e6%88%91%e4%bb%ac%e4%b8%8d%e8%83%bd%e8%bd%bb%e6%98%93%e6%8a%93%e5%8f%96%e5%ae%83%e7%9a%84%e6%95%b0%e6%8d%ae%e3%80%82%26lt%3b%2fp%26gt%3b%0d%0a%26lt%3bp%26gt%3b%e9%b2%b2%e9%b9%8f%e6%95%b0%e6%8d%ae%e7%9a%84%e6%8a%80%e6%9c%af%e4%ba%ba%e5%91%98%e7%bb%8f%e8%bf%87%e7%a0%94%e7%a9%b6%ef%bc%8c%e6%9c%80%e7%bb%88%e6%88%90%e5%8a%9f%e7%bb%95%e8%bf%87%e4%ba%86%e5%85%b6%e5%8a%a0%e5%af%86%e7%ae%97%e6%b3%95%ef%bc%8c%e4%b8%8b%e9%9d%a2%e6%98%af%e6%88%91%e4%bb%ac%e4%bd%bf%e7%94%a8Python%e7%a8%8b%e5%ba%8f%e8%bf%9b%e8%a1%8c%e7%99%be%e5%ba%a6%e6%8c%87%e6%95%b0%e6%8a%93%e5%8f%96%e7%9a%84%e6%bc%94%e7%a4%ba%e8%a7%86%e9%a2%91%e3%80%82%26lt%3b%2fp%26gt%3b%0d%0a%26lt%3bp%26gt%3b%26lt%3bembed+src%3d%26quot%3bhttp%3a%2f%2fplayer.youku.com%2fplayer.php%2fsid%2fXNjgyOTM3Mzky%2fv.swf%26quot%3b+allowfullscreen%3d%26quot%3btrue%26quot%3b+quality%3d%26quot%3bhigh%26quot%3b+width%3d%26quot%3b480%26quot%3b+height%3d%26quot%3b400%26quot%3b+align%3d%26quot%3bmiddle%26quot%3b+allowscriptaccess%3d%26quot%3balways%26quot%3b+type%3d%26quot%3bapplication%2fx-shockwave-flash%26quot%3b%26gt%3b%26lt%3b%2fp%26gt%3b%0d%0a%26lt%3bp%26gt%3b%e8%a7%86%e9%a2%91%e4%b8%ad%e7%9a%84%e8%be%93%e5%87%ba%e6%96%87%e4%bb%b6%e4%b8%8b%e8%bd%bd%ef%bc%9a%26lt%3b%2fp%26gt%3b%0d%0a%26lt%3btable+width%3d%26quot%3b450%26quot%3b%26gt%3b%0d%0a++++%26lt%3btbody%26gt%3b%0d%0a++++++++%26lt%3btr%26gt%3b%0d%0a++++++++++++%26lt%3btd+height%3d%26quot%3b30%26quot%3b+width%3d%26quot%3b20%26quot%3b%26gt%3b%26lt%3ba+href%3d%26quot%3b%2fuploads%2fsoft%2f140309%2f1-140309211U3.csv%26quot%3b+target%3d%26quot%3b_blank%26quot%3b%26gt%3b%26lt%3bimg+src%3d%26quot%3b%2fplus%2fimg%2faddon.gif%26quot%3b+border%3d%26quot%3b0%26quot%3b+align%3d%26quot%3bcenter%26quot%3b+alt%3d%26quot%3b%26quot%3b%26gt%3b%26lt%3b%2fa%26gt%3b%26lt%3b%2ftd%26gt%3b%0d%0a++++++++++++%26lt%3btd%26gt%3b%26lt%3ba+href%3d%26quot%3b%2fuploads%2fsoft%2f140309%2f1-140309211U3.csv%26quot%3b+target%3d%26quot%3b_blank%26quot%3b%26gt%3b%26lt%3bu%26gt%3b%e6%9d%a5%e8%87%aa%e6%98%9f%e6%98%9f%e7%9a%84%e4%bd%a0-%e7%99%be%e5%ba%a6%e6%8c%87%e6%95%b0.csv%26lt%3b%2fu%26gt%3b%26lt%3b%2fa%26gt%3b%26lt%3b%2ftd%26gt%3b%0d%0a++++++++%26lt%3b%2ftr%26gt%3b%0d%0a++++%26lt%3b%2ftbody%26gt%3b%0d%0a%26lt%3b%2ftable%26gt%3b%0d%0a%26lt%3bp%26gt%3b%e5%a6%82%e6%9e%9c%e6%82%a8%e5%af%b9%e8%af%a5%e6%96%b9%e6%a1%88%e6%84%9f%e5%85%b4%e8%b6%a3%e5%8f%af%e4%bb%a5%e8%81%94%e7%b3%bb%e6%88%91%e4%bb%ac%e7%9a%84%e5%9c%a8%e7%ba%bfQQ%e5%ae%a2%e6%9c%8d%e3%80%82%26lt%3b%2fp%26gt%3b%0d%0a+++++++++++++++++++++++++++++++++%0d%0a++++++++++++++++++++++++++++++++++%26lt%3bdiv+class%3d%26quot%3bhltips%26quot%3b%26gt%3b%e7%89%b9%e5%88%ab%e8%af%b4%e6%98%8e%ef%bc%9a%e8%af%a5%e6%96%87%e7%ab%a0%e4%b8%ba%e9%b2%b2%e9%b9%8f%e6%95%b0%e6%8d%ae%e5%8e%9f%e5%88%9b%e6%96%87%e7%ab%a0+%ef%bc%8c%e4%bd%a0%e9%99%a4%e4%ba%86%e5%8f%af%e4%bb%a5%e5%8f%91%e8%a1%a8%e8%af%84%e8%ae%ba%e5%a4%96%ef%bc%8c%e8%bf%98%e5%8f%af%e4%bb%a5%e8%bd%ac%e8%bd%bd%e5%88%b0%e4%bd%a0%e7%9a%84%e7%bd%91%e7%ab%99%e6%88%96%e5%8d%9a%e5%ae%a2%ef%bc%8c%e4%bd%86%e6%98%af%e8%af%b7%e4%bf%9d%e7%95%99%e6%ba%90%e5%9c%b0%e5%9d%80%ef%bc%8c%e8%b0%a2%e8%b0%a2!!%ef%bc%88%e5%b0%8a%e9%87%8d%e4%bb%96%e4%ba%ba%e5%8a%b3%e5%8a%a8%ef%bc%8c%e4%bd%a0%e6%88%91%e5%85%b1%e5%90%8c%e5%8a%aa%e5%8a%9b%ef%bc%89%26lt%3b%2fdiv%26gt%3b%0d%0a%09%09%09+++%26lt%3b%2fdiv%26gt%3b" "127.0.0.1:10192"
        ;;
esac

echo "finish."
