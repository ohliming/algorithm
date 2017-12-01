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
#yesday=`date -d yesterday +"%Y%m%d"`
#yesday2=`date -d yesterday +"%Y-%m-%d"`
yesday=$1
yesday2=$2
stat_file=$path/data/crowd_funding_stat_$yesday.txt
mkdir data

## get data
python calc_crowd_funding.py $yesday > $stat_file

## insert
python insert_crowd_funding_report.py $yesday2 $stat_file

echo "finish."




