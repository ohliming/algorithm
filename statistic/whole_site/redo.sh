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
#yesday=`date -d yesterday +"%Y%m%d"`
#yesday2=`date -d yesterday +"%Y-%m-%d"`

yesday=$1
yesday2=`date -d  "$yesday" +"%Y-%m-%d"`

stat_file=$path/data/allsite_stat_$yesday.txt

## get data
python calc_allsite.py $yesday > $stat_file

## insert sql
python insert_allsite_report.py $yesday2 $stat_file



