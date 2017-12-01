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
yesday=$1
yesday2=$2

stat_file=$path/data/user_login_stat_$yesday.txt
mkdir data

## get data
python calc_user_login.py $yesday > $stat_file

## insert sql
python insert_user_login.py $yesday2 $stat_file
python insert_search_keyword.py $yesday2 $stat_file

## output investor behavior
python get_investor_behavior.py |sort -t"	" -k3gr >user_login_behavior.txt

echo "finish."
