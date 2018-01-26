#!/bin/bash
# ===============================================================
#   Copyright (C) 2015 Bigdata Inc. All rights reserved.
#
#   @file：cmd.sh
#   @author：Song Wanli <wanli.song@foxmail.com>
#   @date：2015-04-20
#   @desc： sh cmd.sh (start|stop|restart)
#   @update：
# ================================================================

## 1.global conf
run_cmd=$1
port=10194
process_num=2
if [ $# -ge 2 ];then
    process_num=$2
fi
thread_num=2
mode=0
. ../../common/mysql_account.sh
if [ ! -d "./log" ];then
  mkdir log
fi

### 2,fetch krplus2 company dict
#mysql -u$DB_KRPLUS_USER -p$DB_KRPLUS_PASSWD $DB_KRPLUS_NAME -h$DB_HOST \
#      -e "set names utf8;select id,name,website,iphone_appstore_link from company \
#      where name !='' and status>1 and is_deleted != 1" \
#> id_name_url_app.txt

## 3,run
case $run_cmd in
    start)
        ## start

       # ## 2,fetch krplus2 company dict
       # mysql -u$DB_KRPLUS_USER -p$DB_KRPLUS_PASSWD $DB_KRPLUS_NAME -h$DB_HOST \
       # -e "set names utf8;select id,name,website,iphone_appstore_link from company \
       # where name !='' and status>1 and is_deleted != 1" \
       # > id_name_url_app.txt

        nohup ../tornado/babysitter -r  python ../hotspot/server.py --port=$port --mode=$mode --processes=$process_num --threads=$thread_num --logdir=./log/ >/dev/null 2>&1 &
        ;;
    stop)
        ## stop
        for pid in `ps aux|grep "server.py --port=$port " |grep -v grep| awk '{print $2}'`
        do
            echo $pid
            kill -9 $pid
        done
        ;;
    restart)
        ## restart
        for pid in `ps aux|grep "server.py --port=$port " |grep -v grep| awk '{print $2}'`
        do
            echo $pid
            kill -9 $pid
        done
        nohup ../tornado/babysitter -r data@36kr.com python ../hotspot/server.py --port=$port --mode=$mode --processes=$process_num --threads=$thread_num --logdir=./log/ >/dev/null 2>&1 &
        ;;
    *)
        ## test
        ;;
esac

echo "finish."

