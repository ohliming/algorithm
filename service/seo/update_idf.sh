#!/bin/bash
# ===============================================================
#   Copyright (C) 2015 Bigdata Inc. All rights reserved.
#
#   @file：update_idf.sh
#   @author：Song Wanli <wanli.song@foxmail.com>
#   @date：2015-09-09
#   @desc：
#   @update：
# ================================================================

python seo_db_stats.py >com_df_idf.tmp
cnt=`cat com_df_idf.tmp |wc -l`
if [ $cnt -lt 20000 ];then
    echo "Subject: [SEO文本idf字典报警:idf num $cnt lt 2w]"
    exit 1
fi

mv com_df_idf com_df_idf.bak
mv com_df_idf.tmp com_df_idf

sh cmd.sh restart
