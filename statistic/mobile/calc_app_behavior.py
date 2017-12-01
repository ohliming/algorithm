#!/usr/bin/env python
#coding=utf8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import json
import time as time_alia
import glob
import urllib
import gzip
from datetime import *
import re
import MySQLdb

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

        # nginx log
        self.ng_daily_log_file = '/data/work/daily_bak/nginx_mobile/nginx.krplus.access-%s_00000' %(self.report_date2)
        self.ng_monthly_log_file = '/data/work/daily_bak/nginx_mobile/monthly.log.%s' %(self.report_month)

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

    def get_app_info(self, ret):
        investor_dict = set()
        rows = self.get_sql_result("select id from user where (investor_type=10 or investor_type=20)")
        for row in rows:
            investor_dict.add(str(row[0]))

        company_dict = {}
        rows = self.get_sql_result("select manager_id,id from company where manager_id!=0")
        for row in rows:
            company_dict[str(row[0])] = str(row[1])

        investor_uids = set()
        ios_uids = set()
        android_uids = set()

        view_cids_pv = 0
        yuetan_coms_pv = 0
        bp_download_pv = 0
        sixin_coms_pv = 0
        follow_coms_pv = 0

        view_cids = set()
        view_bp = set()
        company_yuetan = set()
        sixin_coms = set()
        follow_coms = set()

        view_cids_cv = set()
        view_bp_cv = set()
        company_yuetan_cv = set()
        sixin_coms_cv = set()
        follow_coms_cv = set()

        view_cids_detail = set()
        company_yuetan_detail = set()
        view_bp_detail = set()
        sixin_coms_detail = set()
        follow_coms_detail = set()

        for line in open(self.ng_daily_log_file):
            line = line.strip('\n')
            uid_arr = line.split('"')[-1].strip().split(' ')
            uid = uid_arr[1] if len(uid_arr) >1 else '0'
            cookie_id = uid_arr[2] if len(uid_arr) >2 else '0'
            key = uid if uid != '0' else cookie_id

            ## 所有统计都是要为投资人身份
            if uid!='0' and uid in investor_dict:
                investor_uids.add(uid)
                #if not (('"36kr/' in line) or ('36kr com.android36kr.app/' in line)):
                if uid!='0' and 'iOS' in line:
                    ios_uids.add(uid)
                if uid!='0' and 'Android' in line:
                    android_uids.add(uid)

                ## 浏览公司
                m1 = re.search('/api/(v3|mobi)/company/(\d+)/info', line)
                if m1:
                    cid = m1.group(2)
                    view_cids_pv += 1
                    view_cids.add(uid)
                    view_cids_cv.add(cid)
                    if uid in investor_dict:
                        view_cids_detail.add(uid+"\t"+cid)

                ## 约谈公司管理员
                m1 = re.search('/api/(v3|mobi)/inmail/(\d+)/auto-send', line)
                if m1:
                    yuetan_coms_pv += 1
                    company_yuetan.add(uid)
                    manager_id = m1.group(2)
                    if manager_id in company_dict:
                        cid = company_dict[manager_id]
                        company_yuetan_cv.add(cid)
                        if uid in investor_dict:
                            company_yuetan_detail.add(uid+"\t"+cid)
                else:
                    ## 发私信公司管理员
                    m1 = re.search('/api/(v3|mobi)/inmail/(\d+)', line)
                    if m1:
                        sixin_coms_pv += 1
                        sixin_coms.add(uid)
                        manager_id = m1.group(2)
                        if manager_id in company_dict:
                            cid = company_dict[manager_id]
                            sixin_coms_cv.add(cid)
                            if uid in investor_dict:
                                sixin_coms_detail.add(uid+"\t"+cid)

                ## 下载BP公司
                m1 = re.search('/api/(v3|mobi)/company/(\d+)/bp', line)
                if m1:
                    cid = m1.group(2)
                    bp_download_pv += 1
                    view_bp.add(uid)
                    view_bp_cv.add(cid)
                    if uid in investor_dict:
                        view_bp_detail.add(uid+"\t"+cid)

                ## 关注公司
                m1 = re.search('/api/(v3|mobi)/follow/company/(\d+)', line)
                if m1:
                    cid = m1.group(2)
                    follow_coms_pv += 1
                    follow_coms.add(uid)
                    follow_coms_cv.add(cid)
                    if uid in investor_dict:
                        follow_coms_detail.add(uid+"\t"+cid)


        ret["app_daily_investor_num"] = len(investor_uids)
        ret["app_daily_user_ios_num"] = len(ios_uids)
        ret["app_daily_user_android_num"] = len(android_uids)

        ret["app_daily_view_com_uv"] = len(view_cids)
        ret["app_daily_follow_com_uv"] = len(follow_coms)
        ret["app_daily_yuetan_com_uv"] = len(company_yuetan)
        ret["app_daily_sixin_com_uv"] = len(sixin_coms)
        ret["app_daily_view_bp_uv"] = len(view_bp)

        ret["app_daily_view_com_pv"] = view_cids_pv
        ret["app_daily_follow_com_pv"] = follow_coms_pv
        ret["app_daily_yuetan_com_pv"] = yuetan_coms_pv
        ret["app_daily_sixin_com_pv"] = sixin_coms_pv
        ret["app_daily_view_bp_pv"] = bp_download_pv

        ret["app_daily_view_com_cv"] = len(view_cids_cv)
        ret["app_daily_follow_com_cv"] = len(follow_coms_cv)
        ret["app_daily_yuetan_com_cv"] = len(company_yuetan_cv)
        ret["app_daily_sixin_com_cv"] = len(sixin_coms_cv)
        ret["app_daily_view_bp_cv"] = len(view_bp_cv)

        ret["app_daily_view_com_detail"] = '\n'.join(view_cids_detail)
        ret["app_daily_follow_com_detail"] = '\n'.join(follow_coms_detail)
        ret["app_daily_yuetan_com_detail"] = '\n'.join(company_yuetan_detail)
        ret["app_daily_sixin_com_detail"] = '\n'.join(sixin_coms_detail)
        ret["app_daily_view_bp_detail"] = '\n'.join(view_bp_detail)

    def get_all_statistics_info(self):
        ret = {}
        self.get_app_info(ret)
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
