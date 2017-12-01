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
yesday=`date -d yesterday +"%Y%m%d"`
yesday2=`date -d yesterday +"%Y-%m-%d"`

stat_file=$path/data/insight_stat_api_$yesday.txt
mkdir data

## get data
python calc_insight.py $yesday > $stat_file
