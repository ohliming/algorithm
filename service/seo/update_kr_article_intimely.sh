#!/bin/bash
# ===============================================================
#   Copyright (C) 2015 Bigdata Inc. All rights reserved.
#
#   @file：update_kr_article_intimely.sh
#   @author：Song Wanli <wanli.song@foxmail.com>
#   @date：2015-11-09
#   @desc：
#   @update：
# ================================================================

article_id=$1
day=`date +"%Y%m%d"`
update_path=/data/work/timetask/timed-algorithm-datasource_opration/datasource_opration
if [ ! -x "$update_path" ]; then
  curl "http://data-internal.corp.36kr.com/seo?cmd=extractArticle&id=$article_id"
else
  cd $update_path
  python ./kr_article_pipeline.py "$article_id" >> data/feeds_result_$day.txt 2>/dev/null
  python ./kr_media_report_pipeline.py "$article_id" > media_report.log 2>&1
fi
