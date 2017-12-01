#!/usr/bin/env python
#coding=utf8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import MySQLdb
import json
import time as time_alia
import glob
import gzip
from datetime import *
import re, urllib
from db_crud import DbCrud
import traceback

class DataFetcher:
    def __init__(self, report_date):
        # time
        self.report_date = report_date
        self.report_date2 = report_date[0:4] +'-' +report_date[4:6] +'-' +report_date[6:8]
        self.report_yesday_date = (datetime.strptime(report_date, "%Y%m%d") - timedelta(days = 1)).strftime("%Y%m%d")
        self.report_yesday_date2 = self.report_yesday_date[0:4] +'-' +self.report_yesday_date[4:6] +'-' +self.report_yesday_date[6:8]
        self.report_month_date = report_date[0:6] +'01'
        self.report_last_month_end_date = (datetime.strptime(self.report_month_date, "%Y%m%d") - timedelta(days = 1)).strftime("%Y%m%d")
        self.report_month_date2 = report_date[0:4] +'-' +report_date[4:6] +'-01'
        self.report_month = report_date[0:4] +'-' +report_date[4:6]

        # db
        #self.db = DbCrud("db1.prod", "analyst", "3oVabBjQKdozxSid", "insight" )
        self.db_k = DbCrud("localhost", "root", "root", "krplus2_%s" % report_date )

        # nginx log
        self.ng_daily_log_file = '/data/work/daily_bak/nginx_stat/nginx.krplus.stat-%s_00000' %(self.report_date2)
        self.ng_monthly_log_file = '/data/work/daily_bak/nginx_stat/monthly.log.%s' %(self.report_month)


    def get_investors(self):
        investors = {}
        rows = self.db_k.select("select id from user where investor_type=10 or investor_type=20")
        for row in rows:
            investors[str(row[0])] = 1
        return investors

    def get_enterprisers(self):
        enterprisers = {}
        rows = self.db_k.select("select id from user where enterpriser=1")
        for row in rows:
            enterprisers[str(row[0])] = 1
        return enterprisers

    def get_daily_log_info(self, ret):

        all_uv_set = set()
        investor_uv_set = set()
        enterpriser_uv_set = set()

        d_investors = self.get_investors()
        d_enterprisers = self.get_enterprisers()

        for line in open(self.ng_daily_log_file):
            line = line.strip('\n')
            uid_arr = line.split('"')[-1].strip().split(' ')
            uid = uid_arr[1] if len(uid_arr) >1 else '0'
            cookie_id = uid_arr[2] if len(uid_arr) >2 else '0'

            if cookie_id!='0':
                all_uv_set.add(cookie_id)
            if uid and uid!='0':
                all_uv_set.add(uid)
                if uid in d_investors:
                    investor_uv_set.add(uid)
                if uid in d_enterprisers:
                    enterpriser_uv_set.add(uid)

        ret["daily_uv"] = len(all_uv_set)
        ret["daily_investor_uv"] = len(investor_uv_set)
        ret["daily_enterpriser_uv"] = len(enterpriser_uv_set)
        ret["investor_num"] = len(d_investors)
        ret["enterpriser_num"] = len(d_enterprisers)
        ret["daily_investor_ratio"] = 1.0*ret["daily_investor_uv"]/ret["investor_num"]
        ret["daily_enterpriser_ratio"] = 1.0*ret["daily_enterpriser_uv"]/ret["enterpriser_num"]


    def _get_dict_set_count_desc(self, mdict):
        dict_tmp = {}
        for k in mdict:
            dict_tmp[k] = len(mdict[k])
        list_tmp = dict_tmp.items()
        list_tmp.sort(key=lambda x:x[1], reverse=True)
        return list_tmp

    def _get_dict_count_desc(self, mdict):
        list_tmp = mdict.items()
        list_tmp.sort(key=lambda x:x[1], reverse=True)
        return list_tmp


    def get_all_statistics_info(self):
        try:
            ret = {}
            self.get_daily_log_info(ret)
            return ret
        except:
            traceback.print_exc()
        finally:
            #self.db.close()
            self.db_k.close()

def main():
    report_date = sys.argv[1].strip()
    data_fetcher = DataFetcher(report_date)
    r = data_fetcher.get_all_statistics_info()
    print json.dumps(r, ensure_ascii=False, indent=4, sort_keys=True).encode('utf8')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print '[Usage]: %s report_date[20150508]' % sys.argv[0]
        sys.exit(-1)
    sys.exit(main())
