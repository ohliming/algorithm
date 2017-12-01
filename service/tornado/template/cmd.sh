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
port=12345
mode=0
num_process=1
num_thread=1

. ../../common/mysql_account.sh
mkdir log

## 2.run
case $run_cmd in
    start)
        ## start
        nohup ../tornado/babysitter -r data@36kr.com python ./server.py --port=$port --mode=$mode --processes=$num_process --threads=$num_thread --logdir=./log/ 1>/dev/null 2>&1 &
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
        nohup ../tornado/babysitter -r data@36kr.com python ./server.py --port=$port --mode=$mode --processes=$num_process --threads=$num_thread --logdir=./log/ 1>/dev/null 2>&1 &
        ;;
    *)
        ## test

        curl "127.0.0.1:9999?cmd=test"
        ;;
esac

echo "finish."
