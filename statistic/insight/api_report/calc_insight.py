#!/usr/bin/env python
#coding=utf8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import json
import time as time_alia
import glob
import gzip
from datetime import *
import re, urllib
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
        #self.db_k = DbCrud("dev09", "root", "oalLToPzrypgpZjTh3yW", "krplus2_%s" % report_date )

        # nginx log
        self.ng_daily_log_file = '/data/work/daily_bak/nginx_insight/nginx.krplus.insight-%s_00000' %(self.report_date2)

    def get_daily_log_info(self):
        api_detail = {}
        for line in open(self.ng_daily_log_file):
            line = line.strip('\n')
            uid_arr = line.split('"')[-1].strip().split(' ')
            uid = uid_arr[1] if len(uid_arr) >1 else '0'
            cookie_id = uid_arr[2] if len(uid_arr) >2 else '0'
            ip = line.split(" ")[0].split(",")[0]
            key = uid if uid!="0" else ip

            if "insight.36kr.com" in line:
                resch = re.search(r'/api/([^ \s\?\d]+)(\d*)([^ \s\?\d]+)(\?\S+)?', line)
                if resch:
                    nid = "***" if resch.group(2) else ""
                    url = "/api/"+resch.group(1)+nid+resch.group(3)
                    if url in api_detail:
                        if key in api_detail[url]:
                            api_detail[url][key] += 1
                        else:
                            api_detail[url][key] = 1
                    else:
                        api_detail[url] = {key:1}
        api_t = {}
        for k in api_detail:
            user_pv = api_detail[k].items()
            user_pv.sort(key=lambda x:x[1], reverse=True)
            user_pv = user_pv[:10]
            info = "\n".join(["%8s%-20s%s" % ("",str(a[0]),str(a[1])) for a in user_pv])
            api_t[k] = (user_pv[0][1], info)
        all_list = api_t.items()
        all_list.sort(key=lambda x:x[1][0], reverse=True)
        info = "\n".join(["%s\n%s" % (a[0], a[1][1]) for a in all_list])
        #print info
        return info


    def get_all_statistics_info(self):
        try:
            return self.get_daily_log_info()
        except:
            traceback.print_exc()
        finally:
            pass

def main():
    report_date = sys.argv[1].strip()
    data_fetcher = DataFetcher(report_date)
    r = data_fetcher.get_all_statistics_info()
    print r

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print '[Usage]: %s report_date[20150508]' % sys.argv[0]
        sys.exit(-1)
    sys.exit(main())
