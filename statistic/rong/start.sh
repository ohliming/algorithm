#!/bin/bash
# ===============================================================
#   Copyright (C) 2015 Bigdata Inc. All rights reserved.
#
#   @file：start.sh
#   @author：Song Wanli <wanli.song@foxmail.com>
#   @date：2015-05-14
#   @desc：
#   @update：
# ================================================================

yesday=`date -d yesterday +"%Y%m%d"`
yesday2=`date -d yesterday +"%Y-%m-%d"`
path=`pwd`

data_dir="$path/result/$yesday"
mkdir -p $data_dir
stat_file=$data_dir/stat_info.$yesday
kr_stat_file=$data_dir/kr_stat_info.$yesday

## 1, calc stat data for rong
cd $path
python data_fetcher.py "$yesday" > $stat_file
python insert_rong_report.py $yesday2 $stat_file

## 2, calc stat data for rong
python kr_index_key_info_dependency.py > $kr_stat_file
python update_rong_krindex.py $yesday2 $kr_stat_file

echo "finish."


