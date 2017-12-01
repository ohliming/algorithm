#!/bin/bash
# ===============================================================
#   Copyright (C) 2015 Bigdata Inc. All rights reserved.
#
#   @file：send_spider_mail.sh
#   @author：Song Wanli <wanli.song@foxmail.com>
#   @date：2015-04-10
#   @desc：
#    send spider mail of ann9, baidu_rel, weibo index, haosou index.
#   @update：
# ================================================================

cd `dirname $0`
today=`date -d yesterday "+%Y%m%d"`
path=`pwd`

## 1.insight for stat
cd $path/stat_report && sh start.sh

## 2.insight for api
cd $path/api_report && sh start.sh

## 3.get stat info
cd $path
data=`cat stat_report/data/insight_stat_${today}.txt`
ta=${data#*kr_daily_user_pv_list\": \"}
tb=${ta%%\"*}
tb=${tb//\\t/            }
tbc=`echo -e ${tb}`
td=`cat api_report/data/insight_stat_api_${today}.txt`

## 4.send mail
to="lijiong@36kr.com,songwanli@36kr.com,cuiyan@36kr.com,huangteng@36kr.com,shenlei@36kr.com"
subject="[氪指数每日监控-$today]"
body="1.每日用户点击数如下：
${tbc}
2.每日数据api访问行为：
${td}"

python /usr/bin/sendmail.py --to="$to" --subject="$subject" --body="$body" --from-name="internal"

