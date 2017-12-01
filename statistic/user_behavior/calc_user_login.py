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
import re
import urllib

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
        self.db_name = 'krplus2_' + report_date
        self.db = None
        self.db_cursor = None
        self.reset_db_connection()

        # nginx log
        self.ng_daily_log_file = '/data/work/daily_bak/nginx_stat/nginx.krplus.stat-%s_00000' %(self.report_date2)
        self.ng_monthly_log_file = '/data/work/daily_bak/nginx_stat/monthly.log.%s' %(self.report_month)

    def reset_db_connection(self):
        if self.db: self.db.close()
        self.db = MySQLdb.connect(host='localhost',user='root',passwd='root',db=self.db_name)
        self.db.set_character_set('utf8')
        self.db_cursor = self.db.cursor()

    def get_sql_result(self, sql_cmd):
        db_data = ''
        retry_count = 0
        while retry_count < 3:
            try:
                self.db_cursor.execute(sql_cmd)
                db_data = self.db_cursor.fetchall()
                break
            except:
                self.reset_db_connection()
            retry_count += 1
        return db_data

    def get_daily_validated_users(self, ret):
        validated_user = set()
        search_keyword = set()
        investor_uids = set()

        ## load investor uids
        rows = self.get_sql_result("select id from user where (investor_type=10 or investor_type=20)")
        for row in rows:
            investor_uids.add(str(row[0]))

        for line in open(self.ng_daily_log_file):
            line = line.strip('\n')
            uid_arr = line.split('"')[-1].strip().split(' ')
            uid = uid_arr[1] if len(uid_arr) >1 else '0'
            cookie_id = uid_arr[2] if len(uid_arr) >2 else '0'
            key = uid if uid != '0' else cookie_id

            if uid != '0' and uid !='':
                is_investor = '0'
                if uid in investor_uids:
                    is_investor = '1'
                from_mobile = '0'
                if ('iPhone' in line) or ('Android' in line):
                    from_mobile = '1'

                is_coinvestor = '0'
                if 'u=%2Fzhongchou' in line:
                    is_coinvestor = '1'
                validated_user.add(uid+"\t"+is_investor+"\t"+from_mobile+"\t"+is_coinvestor)

                #check uid is investor
                if not uid in investor_uids: continue
                if 'u=%2Fsearch%3Fquery%3D' in line:
                    keyword = line.split('u=%2Fsearch%3Fquery%3D')[1].split('&')[0]
                    record = uid +"\t"+ urllib.unquote((urllib.unquote(keyword))).strip('#to-complete-profile').split('&')[0]
                    search_keyword.add(record)
        ret['daily_login_uids'] = list(validated_user)
        ret['daily_search_keyword'] = "\n".join(list(search_keyword))
        #print ret['daily_search_keyword']
        return ret

    def get_all_statistics_info(self):
        ret = {}
        self.get_daily_validated_users(ret)
        return ret

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
