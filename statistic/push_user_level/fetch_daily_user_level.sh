#!/bin/bash
# ===============================================================
#   Copyright (C) 2015 Bigdata Inc. All rights reserved.
#
#   @file：fetch_daily_user_level.sh
#   @author：Song Wanli <wanli.song@foxmail.com>
#   @date：2015-12-29
#   @desc：
#   @update：
# ================================================================

path=`pwd`
yesday=`date -d yesterday +"%Y%m%d"`
yesday2=`date -d yesterday +"%Y-%m-%d"`

## fetch log
stat_log_file=/data/work/daily_bak/nginx_stat/nginx.krplus.stat-${yesday2}_00000
cat $stat_log_file >nginx_log/t.log
cp nginx_log/aliyun_nginx.log nginx_log/aliyun_nginx.log.bak
cat nginx_log/t.log| grep 'u=%2Fcompany%2F[0-9]*%2FcrowFunding' >> nginx_log/aliyun_nginx.log
cat nginx_log/t.log| grep 'u=%2FzhongchouDetail' >> nginx_log/aliyun_nginx.log
cat nginx_log/t.log| grep 'u=%2Fproject%2F' >> nginx_log/aliyun_nginx.log

## calc
python calc_user_level.py

## pack
rm user_level_*.zip
zip -r user_level_$yesday.zip data/

## sendmail
#to="songwanli@36kr.com"
to="songwanli@36kr.com,cuiyan@36kr.com,lijiong@36kr.com,zouhao@36kr.com,caipeng@36kr.com"
subject="用户层级-数据推送-$yesday"
body="[用户层级分类数据-详见附件]:
第一层：注册用户。定义：注册36氪账户成功的用户
第二层：认证用户。定义：认证跟投人成功的用户
第三层：访问过项目详情页的用户。定义：访问过任意众筹项目详情页的用户
第四层：下单用户。定义：下过订单的用户
第五层：支付保证金用户。定义：支付保证金成功的用户
第六层：支付剩余款用户。定义：支付剩余款成功的用户"

attach_file="./user_level_$yesday.zip"

python /usr/bin/sendmail.py --to="${to}" --subject="${subject}" --body="${body}" --from-name="internal"  -a $attach_file

echo 'finish.'


