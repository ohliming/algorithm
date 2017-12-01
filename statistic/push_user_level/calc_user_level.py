#!/usr/bin/env python
#coding=utf8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('../')
import math,datetime
import json
import datetime,time
import urllib,urllib2
from common.db_fetcher import DataBaseFetcher

def extract_qingyun_uids():
    uids_dict = set()
    for line in open("nginx_log/qinyun_nginx.log"):
        line = line.strip('\n')
        if not 'hm.gif?u=' in line:
            continue
        uid_arr = line.split(']')[1].strip().split(' ')
        uid = int(uid_arr[1]) if len(uid_arr) >1 else 0
        if uid==0: continue
        uids_dict.add(uid)
    return uids_dict

def extract_aliyun_uids():
    uids_dict = set()
    for line in open("nginx_log/aliyun_nginx.log"):
        line = line.strip('\n')
        if not 'hm.gif?u=' in line:
            continue
        uid_arr = line.split('"')[-1].strip().split(' ')
        uid = int(uid_arr[1]) if len(uid_arr) >1 else 0
        if uid==0: continue
        uids_dict.add(uid)
    return uids_dict


if __name__ == '__main__':
    fetcher = DataBaseFetcher()

    ## 看过众筹详情页
    detail_page_uids = extract_qingyun_uids() | extract_aliyun_uids()

    ## 下过订单
    trade_uids = {}
    db_data = fetcher.get_sql_result("select distinct user_id from krplus2.trade_crowd_funding where cf_id!=100","mysql_krplus")
    for row in db_data:
        uid = row[0]
        trade_uids[uid] = 4

    ## 已付保证金
    pre_money_uids = {}
    db_data = fetcher.get_sql_result("select distinct user_id from krplus2.trade_crowd_funding where status=11","mysql_krplus")
    for row in db_data:
        uid = row[0]
        pre_money_uids[uid] = 5

    ## 已付剩余款+交易成功
    finish_money_uids = {}
    db_data = fetcher.get_sql_result("select distinct user_id from krplus2.trade_crowd_funding where status=13 or status=2","mysql_krplus")
    for row in db_data:
        uid = row[0]
        finish_money_uids[uid] = 6

    ## 所有跟投人
    user_level = {}
    db_data = fetcher.get_sql_result("select id,coinvestor_type from krplus2.user","mysql_krplus")
    for row in db_data:
        uid = row[0]
        user_level[uid] = 1

        ## 跟投人
        if row[1]==2:
            user_level[uid] = 2
            ## 访问过众筹详情页
            if uid in detail_page_uids:
                user_level[uid] = 3
            if uid in trade_uids:
                user_level[uid] = 4
            if uid in pre_money_uids:
                user_level[uid] = 5
            if uid in finish_money_uids:
                user_level[uid] = 6

    ## output
    out_file_list = []
    for i in range(1,7):
        fp = open("data/user_level_%d.txt" %i, 'w')
        out_file_list.append(fp)

    for uid in user_level:
        level = user_level[uid]
        out_file_list[level-1].write(str(uid)+'\n')



