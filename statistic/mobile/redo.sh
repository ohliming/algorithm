#!/bin/bash
# ===============================================================
#   Copyright (C) 2015 Bigdata Inc. All rights reserved.
#
#   @file：calc_zhong_h5.sh
#   @author：Song Wanli <wanli.song@foxmail.com>
#   @date：2015-06-09
#   @desc：
#   @update：
# ================================================================

path=`pwd`
today=`date +"%Y%m%d"`
yesday=`date -d yesterday +"%Y%m%d"`
yesday2=`date -d yesterday +"%Y-%m-%d"`
yesday=$1
yesday2=$2

stat_file=$path/data/app_stat_$yesday.txt
login_file=$path/data/app_login_$yesday.txt

## get data
python calc_app_behavior.py $yesday > $stat_file
python calc_mobile_user_login.py $yesday > $login_file

## insert sql
python insert_app_behavior.py $yesday2 $stat_file
python insert_mobile_user_login.py $yesday2 $login_file

echo "finish."
