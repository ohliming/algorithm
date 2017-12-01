#!/bin/bash
# ===============================================================
#   Copyright (C) 2015 Bigdata Inc. All rights reserved.
#
#   @file：insight report
#   @author：Song Wanli <wanli.song@foxmail.com>
#   @date：2015-06-09
#   @desc：
#   @update：
# ================================================================

cd `dirname $0`
path=`pwd`
today=`date +"%Y%m%d"`
yesday=$1
yesday2=`date -d  "$yesday" +"%Y-%m-%d"`

stat_file=$path/data/insight_stat_$yesday.txt
mkdir data

## get data
python calc_insight.py $yesday > $stat_file

## insert sql
python insert_insight_report.py $yesday2 $stat_file




