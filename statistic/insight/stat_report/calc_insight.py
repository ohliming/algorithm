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
        self.db = DbCrud("rds60i0820sk46jfsiv0.mysql.rds.aliyuncs.com", "analyst", "JxM2sdUgVgKXMGOg", "insight" )
        self.db_k = DbCrud("localhost", "root", "root", "krplus2_%s" % report_date )

        # nginx log
        self.ng_daily_log_file = '/data/work/daily_bak/nginx_stat/nginx.krplus.stat-%s_00000' %(self.report_date2)
        self.ng_monthly_log_lists = glob.glob('/data/work/daily_bak/nginx_stat/nginx.krplus.stat-%s*' %(self.report_month))

    def get_investors(self):
        investors = {}
        rows = self.db_k.select("select id from user where investor_type=10 or investor_type=20")
        for row in rows:
            investors[str(row[0])] = 1
        return investors

    def get_daily_log_info(self, ret):
        home_page_uv = set()
        home_page_pv = 0
        home_page_u_dict = {}
        investor_uv = set()
        investor_pv = 0
        d_investors = self.get_investors()

        search_kw_uv = set()
        search_kw_pv = 0
        search_kw_uv_dict = {}
        search_kw_pv_dict = {}
        search_ind_uv = set()
        search_ind_pv = 0
        search_ind_uv_dict = {}
        search_ind_pv_dict = {}
        search_phase_uv = set()
        search_phase_pv = 0
        search_phase_uv_dict = {}
        search_phase_pv_dict = {}

        detail_uv_dict = {}
        detail_uv = set()
        detail_pv = 0

        click_investor_validate_uv =set()
        click_investor_validate_pv =0
        click_detail_uv = set()
        click_detail_pv = 0

        add_compare_uv = set()
        add_compare_pv = 0
        add_compare_uv_dict = {}

        for line in open(self.ng_daily_log_file):
            line = line.strip('\n')
            uid_arr = line.split('"')[-1].strip().split(' ')
            uid = uid_arr[1] if len(uid_arr) >1 else '0'
            cookie_id = uid_arr[2] if len(uid_arr) >2 else '0'
            key = cookie_id	

            if "h=insight.36kr.com" in line:
                home_page_pv += 1
                home_page_uv.add(key)
                if uid in d_investors:
                    investor_pv += 1
                    investor_uv.add(uid)

                if uid and uid!="0":
                    if "u=&h=insight.36kr.com" in line \
                        or "hm.gif?u=%2Fhome" in line \
                        or "hm.gif?u=%2Fwelcome" in line \
                        or "hm.gif?u=%2Fuser%2Flogout" in line:
                        pass
                    else:
                        if uid in home_page_u_dict:
                            home_page_u_dict[uid] += 1
                        else:
                            home_page_u_dict[uid] = 1

            # 详情只有认证用户能进，抛掉自己的测试用户，非认证有权限进
            if uid and uid in d_investors:
                # 同时有行业与kw的，后台是按kw搜索返回结果，统计只算在kw下
                rsch = re.search(r'u=%2Fresult%3Fkeyword%3D(.*?)(%26.*?)?&h=insight.36kr.com', line)
                if rsch:
                    kw = urllib.unquote(urllib.unquote(rsch.group(1)))
                    search_kw_uv.add(uid)
                    search_kw_pv += 1
                    if kw in search_kw_uv_dict:
                        search_kw_uv_dict[kw].add(uid)
                        search_kw_pv_dict[kw] += 1
                    else:
                        search_kw_uv_dict[kw] = set([uid])
                        search_kw_pv_dict[kw] = 1

                rsch = re.search(r'u=%2Fresult%3Findustry%3D(.*?)(%26.*?)?&h=insight.36kr.com', line)
                if rsch:
                    ind = rsch.group(1)
                    search_ind_uv.add(uid)
                    search_ind_pv += 1
                    if ind in search_ind_uv_dict:
                        search_ind_uv_dict[ind].add(uid)
                        search_ind_pv_dict[ind] += 1
                    else:
                        search_ind_uv_dict[ind] = set([uid])
                        search_ind_pv_dict[ind] = 1

                rsch = re.search(r'u=%2Fresult%3F(.*?)phase%3D(.*?)(%26.*?)?&h=insight.36kr.com', line)
                if rsch:
                    phase = rsch.group(2)
                    search_phase_uv.add(uid)
                    search_phase_pv += 1
                    if phase in search_phase_uv_dict:
                        search_phase_uv_dict[phase].add(uid)
                        search_phase_pv_dict[phase] += 1
                    else:
                        search_phase_uv_dict[phase] = set([uid])
                        search_phase_pv_dict[phase] = 1

                rsch = re.search(r'u=%2Fcompany%2F(\d+)&h=insight.36kr.com', line)
                if rsch:
                    detail_uv.add(uid)
                    detail_pv += 1
                   # cid = rsch.group(1)
                   # if cid in detail_uv_dict:
                   #     detail_uv_dict[cid].add(uid)
                   # else:
                   #     detail_uv_dict[cid] = set([uid])

                rsch = re.search(r'hm.gif\?et=%E6%8C%89%E9%92%AE&ev=%E6%8A%95%E8%B5%84%E4%BA%BA%E6%8F%90%E4%BA%A4%E8%AE%A4%E8%AF%81%E6%8C%89%E9%92%AE&h=rong.36kr.com', line)
                if rsch:
                    click_investor_validate_uv.add(uid)
                    click_investor_validate_pv += 1

                rsch = re.search(r'hm.gif\?et=%E6%8C%89%E9%92%AE&ev=company_finance_detail%7C(\d+)&h=insight.36kr.com', line)
                if rsch:
                    click_detail_uv.add(uid)
                    click_detail_pv += 1

                rsch = re.search(r'hm.gif\?et=compare_company&ev=(\d+)%7C(\d+)&h=insight.36kr.com', line)
                if rsch:
                    add_compare_uv.add(uid)
                    add_compare_pv += 1
                    cid_add = rsch.group(1)
                    cid_current = rsch.group(2)
                    cids = cid_current + "-" +cid_add
                    if cids in add_compare_uv_dict:
                        add_compare_uv_dict[cids].add(uid)
                    else:
                        add_compare_uv_dict[cids] = set([uid])

        ret["kr_daily_homepage_uv"] = len(home_page_uv)
        ret["kr_daily_homepage_pv"] = home_page_pv
        ret["kr_daily_investor_uv"] = len(investor_uv)
        ret["kr_daily_investor_pv"] = investor_pv
        ret["kr_daily_investor_avg_page"] = 1.0*ret["kr_daily_investor_pv"]/ret["kr_daily_investor_uv"] if ret["kr_daily_investor_uv"]>0 else 0
        ret["kr_daily_investor_uv_ratio"] = 1.0*ret["kr_daily_investor_uv"]/ret["kr_daily_homepage_uv"] if ret["kr_daily_homepage_uv"]>0 else 0
        ret["kr_daily_noninvestor_uv"] = ret["kr_daily_homepage_uv"] - ret["kr_daily_investor_uv"]

        ret["kr_daily_keyword_uv"] = len(search_kw_uv)
        ret["kr_daily_keyword_pv"] = search_kw_pv
        ret["kr_daily_industry_uv"] = len(search_ind_uv)
        ret["kr_daily_industry_pv"] = search_ind_pv
        ret["kr_daily_phase_uv"] = len(search_phase_uv)
        ret["kr_daily_phase_pv"] = search_phase_pv
        ret["kr_daily_detail_uv"] = len(detail_uv)
        ret["kr_daily_detail_pv"] = detail_pv

        info_list = self._get_dict_set_count_desc(search_kw_uv_dict)
        ret["kr_daily_keyword_uv_list"] = "\n".join([str(a[0])+"\t"+str(a[1]) for a in info_list])
        info_list = self._get_dict_count_desc(search_kw_pv_dict)
        ret["kr_daily_keyword_pv_list"] = "\n".join([str(a[0])+"\t"+str(a[1]) for a in info_list])

        info_list = self._get_dict_set_count_desc(search_ind_uv_dict)
        ret["kr_daily_industry_uv_list"] = "\n".join([str(a[0])+"\t"+str(a[1]) for a in info_list])
        info_list = self._get_dict_count_desc(search_ind_pv_dict)
        ret["kr_daily_industry_pv_list"] = "\n".join([str(a[0])+"\t"+str(a[1]) for a in info_list])

        info_list = self._get_dict_set_count_desc(search_phase_uv_dict)
        ret["kr_daily_phase_uv_list"] = "\n".join([str(a[0])+"\t"+str(a[1]) for a in info_list])
        info_list = self._get_dict_count_desc(search_phase_pv_dict)
        ret["kr_daily_phase_pv_list"] = "\n".join([str(a[0])+"\t"+str(a[1]) for a in info_list])

        ret["kr_daily_click_investor_validate_uv"] = len(click_investor_validate_uv)
        ret["kr_daily_click_investor_validate_pv"] = click_investor_validate_pv
        ret["kr_daily_click_detail_uv"] = len(click_detail_uv)
        ret["kr_daily_click_detail_pv"] = click_detail_pv
        ret["kr_daily_add_compare_uv"] = len(add_compare_uv)
        ret["kr_daily_add_compare_pv"] = add_compare_pv

        info_list = self._get_dict_set_count_desc(add_compare_uv_dict)
        ret["kr_daily_add_compare_uv_list"] = "\n".join([str(a[0])+"\t"+str(a[1]) for a in info_list])

        info_list = self._get_dict_count_desc(home_page_u_dict)
        ret["kr_daily_user_pv_list"] = "\n".join([str(a[0])+"\t"+str(a[1]) for a in info_list])
        #ret["kr_daily_user_pv_list"] = "\n".join([ "%-10d      %s" %(int(a[0]),str(a[1])) for a in info_list])

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

    def get_monthly_log_info(self, ret):
        home_page_uv = set()
        home_page_pv = 0
	for f in self.ng_monthly_log_lists:
            for line in open(f):
                line = line.strip('\n')
                uid_arr = line.split('"')[-1].strip().split(' ')
                uid = uid_arr[1] if len(uid_arr) >1 else '0'
                cookie_id = uid_arr[2] if len(uid_arr) >2 else '0'
                key = cookie_id

                if "h=insight.36kr.com" in line:
                    home_page_pv += 1
                    home_page_uv.add(key)

        ret["kr_monthly_homepage_uv"] = len(home_page_uv)
        ret["kr_monthly_homepage_pv"] = home_page_pv

    def get_sql_info(self, ret):
        sql = "select count(*) from interview_log where type=0 and create_date >= %s and create_date <= %s"
        params = (self.report_date2+" 00:00:00", self.report_date2+" 23:59:59")
        rows = self.db.select(sql, params)
        ret["kr_daily_interview_pv"] = rows[0][0]

        sql = "select count(*) from interview_log where type=1 and create_date >= %s and create_date <= %s"
        params = (self.report_date2+" 00:00:00", self.report_date2+" 23:59:59")
        rows = self.db.select(sql, params)
        ret["kr_daily_report_pv"] = rows[0][0]

        interview_detail = {}
        report_detail = {}
        d_cid_name = {}
        sql = "select a.uid, a.cid, a.type, b.name from interview_log as a left join company_trend as b \
                on a.cid=b.id where create_date >= %s and create_date <= %s order by a.cid"
        params = (self.report_date2+" 00:00:00", self.report_date2+" 23:59:59")
        rows = self.db.select(sql, params)
        for row in rows:
            uid = str(row[0])
            cid = str(row[1])
            otype = row[2]
            cname = row[3]
            if not cname:
                #重跑数据，很久之前的，company_trend重刷了，找不到公司
                sql2 = "select name from company where id=%s"
                params2 = (int(cid),)
                cname = self.db_k.select(sql2, params2)[0][0]
            d_cid_name[cid] = cname
            if otype==0:
                if cid in interview_detail:
                    interview_detail[cid].add(uid)
                else:
                    interview_detail[cid]=set([uid])
            elif otype==1:
                if cid in report_detail:
                    report_detail[cid].add(uid)
                else:
                    report_detail[cid]=set([uid])

        tmp_list = interview_detail.items()
        tmp_list.sort(key=lambda x:len(x[1]), reverse=True)
        i_info = "\n".join([str(a[0])+"\t"+d_cid_name[a[0]]+"\t"+",".join(a[1]) for a in tmp_list])
        tmp_list = report_detail.items()
        tmp_list.sort(key=lambda x:len(x[1]), reverse=True)
        r_info = "\n".join([str(a[0])+"\t"+d_cid_name[a[0]]+"\t"+",".join(a[1]) for a in tmp_list])
        ret["kr_daily_interview_list"] = i_info
        ret["kr_daily_report_list"] = r_info

    def get_all_statistics_info(self):
        try:
            ret = {}
            self.get_sql_info(ret)
            self.get_daily_log_info(ret)
            self.get_monthly_log_info(ret)
            return ret
        except:
            traceback.print_exc()
        finally:
            self.db.close()
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
