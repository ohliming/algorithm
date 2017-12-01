#!/usr/bin/env python
#coding=utf8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import MySQLdb
import json
import time
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
        self.ng_monthly_log_lists = glob.glob('/data/work/daily_bak/nginx_stat/nginx.krplus.stat-%s*' %(self.report_month))

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

    '''
    ===========================
        nginx log processor
    ===========================
    '''
    def preprocess_nginx_log(self, gz_files, parse_file):
        fout = open(parse_file, 'w')
        for f in gz_files:
            f_date_str = f.split('access.log.')[1].split('.gz')[0]
            f_date = datetime.strptime(f_date_str, "%Y-%m-%d")
            if (f_date < datetime(2015, 5, 12, 23)
                or f_date > datetime.strptime(self.report_date, "%Y%m%d")):
                continue
            fp = gzip.open(f, 'rb')
            for line in fp.readlines():
                line = line.strip()
                if len(line) == 0: continue
                log_info = LogInfo()
                if log_info.parse_line(line):
                    r = []
                    for attr in LogInfo.attrs:
                        r.append(getattr(log_info, attr))
                    fout.write('\t'.join(r) + '\n')
                    fout.flush()
        fout.close()
        return 0

    def get_monthly_nginx_info(self, ret):
        # define var
        d_register_uids = set()
        d_unregister_cookies = set()
        d_get_bp_investor_ids = set()
        d_bp_download_com_ids = set()
        d_bp_download_detail = set()

        # extract stat info
        ret["n_monthly_website_pv"] = 0
        ret["n_monthly_unregister_pv"] = 0
        ret["n_monthly_bp_download_num"] = 0
        for f in self.ng_monthly_log_lists:
            for line in open(f):
                line = line.strip('\n')
                uid_arr = line.split('"')[-1].strip().split(' ')
                kr_plus_uid = uid_arr[1] if len(uid_arr) >1 else '0'
                cookie_uid = uid_arr[2] if len(uid_arr) >2 else '0'
                line = urllib.unquote(line)

                if "hm.gif?" not in line:
                    continue

                if "h=36kr.com" in line or "h=m.36kr.com " in line:
                    # 过滤掉主站资讯的统计
                    continue

                if kr_plus_uid == '0':
                    d_unregister_cookies.add(cookie_uid)
                else:
                    d_register_uids.add(kr_plus_uid)

                if line.find('u=') != -1:
                    ret["n_monthly_website_pv"] += 1
                    if kr_plus_uid == '0':
                        ret["n_monthly_unregister_pv"] += 1
                if line.find('et=下载BP') != -1:
                    arr = line.split('et=下载BP&')[1].split('&')[0].split('=')[1].split('|')
                    d_get_bp_investor_ids.add(arr[0])
                    d_bp_download_com_ids.add(arr[1])
                    ret["n_monthly_bp_download_num"] += 1

        ## output: stat info
        ret["n_monthly_website_uv"] = len(d_unregister_cookies) + len(d_register_uids)
        ret["n_monthly_unregister_uv"] = len(d_unregister_cookies)
        ret["n_monthly_login_user_num"] = len(d_register_uids)

        ret["n_monthly_get_bp_investor_num"] = len(d_get_bp_investor_ids)
        ret["n_monthly_bp_download_com_num"] = len(d_bp_download_com_ids)

        ret["n_monthly_investor_login_num"] = 0
        rows = self.get_sql_result("select id from user where (investor_type=10 or investor_type=20)")
        for row in rows:
            if str(row[0]) in d_register_uids:
                ret["n_monthly_investor_login_num"] += 1

        ret["n_monthly_enterpriser_login_num"] = 0
        rows = self.get_sql_result("select id from user where enterpriser=1")
        for row in rows:
            if str(row[0]) in d_register_uids:
                ret["n_monthly_enterpriser_login_num"] += 1

        return ret

    def get_daily_nginx_info(self, ret):
        # define var
        d_register_uids = set()
        d_unregister_cookies = set()
        d_get_bp_investor_ids = set()
        d_bp_download_com_ids = set()
        d_bp_download_detail = set()

        # extract stat info
        ret["n_daily_website_pv"] = 0
        ret["n_daily_unregister_pv"] = 0
        ret["n_daily_bp_download_num"] = 0

        n_daily_activity_uv = {"details":{}, "apply":{}}

        for line in open(self.ng_daily_log_file):
            line = line.strip('\n')
            uid_arr = line.split('"')[-1].strip().split(' ')
            kr_plus_uid = uid_arr[1] if len(uid_arr) >1 else '0'
            cookie_uid = uid_arr[2] if len(uid_arr) >2 else '0'
            line = urllib.unquote(line)

            if "hm.gif?" not in line:
                continue

            if "h=36kr.com" in line or "h=m.36kr.com " in line:
                # 过滤掉主站资讯的统计
                continue

            if kr_plus_uid == '0':
                d_unregister_cookies.add(cookie_uid)
            else:
                d_register_uids.add(kr_plus_uid)

            if line.find('u=') != -1:
                ret["n_daily_website_pv"] += 1
                if kr_plus_uid == '0':
                    ret["n_daily_unregister_pv"] += 1
            if line.find('et=下载BP') != -1:
                arr = line.split('et=下载BP&')[1].split('&')[0].split('=')[1].split('|')
                d_get_bp_investor_ids.add(arr[0])
                d_bp_download_com_ids.add(arr[1])
                rows = self.get_sql_result("select name from user where id=%s" %(arr[0]))
                if rows:
                    d_bp_download_detail.add((arr[2]+'\t'+ arr[0] +'\t' +str(rows[0][0])))
                    ret["n_daily_bp_download_num"] += 1

            #key = kr_plus_uid if kr_plus_uid!='0' else cookie_uid
            key = cookie_uid
            resch = re.search(r'u=/activityApply/(details|apply)/(\d+)', line)
            if resch:
                atype = resch.group(1)
                aid = str(resch.group(2))
                if atype not in n_daily_activity_uv:
                    n_daily_activity_uv[atype] = {}
                if aid in n_daily_activity_uv[atype]:
                    n_daily_activity_uv[atype][aid].add(key)
                else:
                    n_daily_activity_uv[atype][aid] = set([key])

        ## output: stat info
        ret["n_daily_website_uv"] = len(d_unregister_cookies) + len(d_register_uids)
        ret["n_daily_unregister_uv"] = len(d_unregister_cookies)
        ret["n_daily_login_user_num"] = len(d_register_uids)

        txt=""
        for act_type in n_daily_activity_uv:
            info = []
            for aid in n_daily_activity_uv[act_type]:
                size = len(n_daily_activity_uv[act_type][aid])
                info.append([int(aid), size])
            info.sort(key=lambda x:x[0])
            txt += "\n".join([act_type+"-"+str(a[0])+"\t"+str(a[1]) for a in info])+"\n"
        ret["n_daily_activity_uv_list"] = txt

        ret["n_daily_get_bp_investor_num"] = len(d_get_bp_investor_ids)
        ret["n_daily_bp_download_com_num"] = len(d_bp_download_com_ids)
        ret["n_daily_bp_download_detail_list"] = '\n'.join(d_bp_download_detail)

        ret["n_daily_investor_login_num"] = 0
        rows = self.get_sql_result("select id from user where (investor_type=10 or investor_type=20)")
        for row in rows:
            if str(row[0]) in d_register_uids:
                ret["n_daily_investor_login_num"] += 1
        ret["n_daily_investor_login_ratio"] = float('%0.5f' % (ret["n_daily_investor_login_num"] * 1.0 / len(rows)))

        ret["n_daily_enterpriser_login_num"] = 0
        rows = self.get_sql_result("select id from user where enterpriser=1")
        for row in rows:
            if str(row[0]) in d_register_uids:
                ret["n_daily_enterpriser_login_num"] += 1
        ret["n_daily_enterpriser_login_ratio"] = float('%0.5f' % (ret["n_daily_enterpriser_login_num"] * 1.0 / len(rows)))

        return ret

    def get_collected_monthly_active_users(self, ret):
        ret['n_collected_monthly_active_user_num'] = 0
        collected_user_login_times = {}
        for f in self.ng_monthly_log_lists:
            d_register_uids = set()
            for line in open(f):
                try:
                    line = line.strip('\n')
                    uid_arr = line.split('"')[-1].strip().split(' ')
                    kr_plus_uid = uid_arr[1] if len(uid_arr) >1 else '0'
                    cookie_uid = uid_arr[2] if len(uid_arr) >2 else '0'
                    if kr_plus_uid != '0':
                        d_register_uids.add(kr_plus_uid)
                except:
                    continue
            for uid in d_register_uids:
                if uid in collected_user_login_times:
                    collected_user_login_times[uid] += 1
                else:
                    collected_user_login_times[uid] = 1

        for uid in collected_user_login_times:
            if collected_user_login_times[uid] >=3:
                rows = self.get_sql_result("select from_uid from inmail where direction=1 and from_uid=%s and \
                                            create_date>='%s 00:00:00' and create_date<='%s 23:59:59'"
                                            %(uid, self.report_month_date2, self.report_date2))
                if rows:
                    ret['n_collected_monthly_active_user_num'] += 1
                    #print uid +'\t' + str(collected_user_login_times[uid]) + '\t' + str(rows[0][0])
        return ret

    '''
    ===========================
        audit statistics
    ===========================
    '''
    def get_statistics_audit_info(self, ret):
        rows = self.get_sql_result("select count(distinct company_id) from \
                                  (select audit_id,company_id,company_name from audit_system_%s.audit_company) as a \
                                  left join audit_system_%s.audit as b on a.audit_id=b.id \
                                  where updated_at>='%s 00:00:00' and updated_at<='%s 23:59:59' and status='approved'"
                                  %(self.report_date, self.report_date, self.report_date2, self.report_date2))
        ret['a_daily_user_created_coms_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("select count(*) from audit_system_%s.audit \
                                   where (type='startup_exp' or type='invest_exp') and (status='approved') \
                                   and creator in (select id from krplus2_%s.user where phone!='')"
                                   %(self.report_date, self.report_date))
        ret['a_collected_audit_success_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("select count(*) from audit_system_%s.audit \
                                   where (type='startup_exp' or type='invest_exp') \
                                   and (status='rejected' or status='deleted' or status='cancelled') \
                                   and creator in (select id from krplus2_%s.user where phone!='')"
                                   %(self.report_date, self.report_date))
        ret['a_collected_audit_failed_num'] = int(rows[0][0]) if rows else 0

        return ret

    '''
    ================================
        yuetan or sixin statistics
    ================================
    '''
    def get_statistics_interview_info(self, ret):
        ### 私信发送的数量
        rows = self.get_sql_result("select count(*) from inmail where direction=1")
        ret['m_sixin_total_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("select count(*) from inmail \
                                    where direction=1 and create_date <='%s 23:59:59' and create_date >='%s 00:00:00'"
                                   %(self.report_date2, self.report_date2))
        ret['m_daily_sixin_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("select count(a.id) from inmail as a inner join user as b on a.from_uid=b.id \
                                    where a.direction=1 and a.create_date>='%s 00:00:00' and a.create_date<='%s 23:59:59' \
                                     and b.enterpriser=1"
                                   %(self.report_date2, self.report_date2))
        ret['m_daily_enterpriser_start_sixin_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("select count(a.id) from inmail as a inner join user as b on a.from_uid=b.id \
                                    where a.direction=1 and a.create_date>='%s 00:00:00' and a.create_date<='%s 23:59:59' \
                                    and (b.investor_type=10 or b.investor_type=20)"
                                   %(self.report_date2, self.report_date2))
        ret['m_daily_investor_start_sixin_num'] = int(rows[0][0]) if rows else 0

        ### 发送私信的人数
        #rows = self.get_sql_result("select count(distinct id) from user \
        #                            where id in (select from_uid from inmail where direction=1 and \
        #                                         create_date>='%s 00:00:00' and create_date<='%s 23:59:59')"
        #                           %(self.report_date2, self.report_date2))
        rows = self.get_sql_result("select count(distinct from_uid) from inmail where direction=1 and \
                                                 create_date>='%s 00:00:00' and create_date<='%s 23:59:59'"
                                   %(self.report_date2, self.report_date2))
        ret['m_daily_use_sixin_person_num'] = int(rows[0][0]) if rows else 0

        #rows = self.get_sql_result("select count(distinct id) from user \
        #                            where id in (select from_uid from inmail where direction=1 and \
        #                                         create_date>='%s 00:00:00' and create_date<='%s 23:59:59')"
        #                           %(self.report_month_date2, self.report_date2))
        rows = self.get_sql_result("select count(distinct from_uid) from inmail where direction=1 and \
                                                 create_date>='%s 00:00:00' and create_date<='%s 23:59:59' "
                                   %(self.report_month_date2, self.report_date2))
        ret['m_monthly_use_sixin_person_num'] = int(rows[0][0]) if rows else 0

        #rows = self.get_sql_result("select count(distinct id) from user \
        #                            where id in (select from_uid from inmail where direction=1 and \
        #                                         create_date>='%s 00:00:00' and create_date<='%s 23:59:59') \
        #                            and user.enterpriser=1"
        #                           %(self.report_date2, self.report_date2))
        rows = self.get_sql_result("select count(distinct a.from_uid) from inmail as a inner join user as b on a.from_uid=b.id \
                                                 where a.direction=1 and \
                                                 a.create_date>='%s 00:00:00' and a.create_date<='%s 23:59:59' \
                                                 and b.enterpriser=1"
                                   %(self.report_date2, self.report_date2))
        ret['m_daily_use_sixin_enterpriser_num'] = int(rows[0][0]) if rows else 0
        #rows = self.get_sql_result("select count(distinct id) from user \
        #                            where id in (select from_uid from inmail where direction=1 and \
        #                                         create_date>='%s 00:00:00' and create_date<='%s 23:59:59') \
        #                            and (user.investor_type=10 or user.investor_type=20)"
        #                           %(self.report_date2, self.report_date2))
        rows = self.get_sql_result("select count(distinct a.from_uid) from inmail as a inner join user as b on a.from_uid=b.id \
                                    where a.direction=1 and \
                                    a.create_date>='%s 00:00:00' and a.create_date<='%s 23:59:59' \
                                    and (b.investor_type=10 or b.investor_type=20)"
                                   %(self.report_date2, self.report_date2))
        ret['m_daily_use_sixin_investor_num'] = int(rows[0][0]) if rows else 0
        ret['m_daily_use_sixin_notinvestor_num'] = ret['m_daily_use_sixin_person_num'] - ret['m_daily_use_sixin_investor_num']

        #rows = self.get_sql_result("select count(distinct id) from user \
        #                            where id in (select from_uid from inmail where direction=1 and \
        #                                         create_date>='%s 00:00:00' and create_date<='%s 23:59:59') \
        #                            and (user.investor_type=10 or user.investor_type=20)"
        #                           %(self.report_month_date2, self.report_date2))
        rows = self.get_sql_result("select count(distinct a.from_uid) from inmail as a inner join user as b on a.from_uid=b.id \
                                    where a.direction=1 and \
                                    a.create_date>='%s 00:00:00' and a.create_date<='%s 23:59:59' \
                                    and (b.investor_type=10 or b.investor_type=20)"
                                   %(self.report_month_date2, self.report_date2))
        ret['m_monthly_use_sixin_investor_num'] = int(rows[0][0]) if rows else 0
        ret['m_monthly_use_sixin_notinvestor_num'] = ret['m_monthly_use_sixin_person_num'] - ret['m_monthly_use_sixin_investor_num']

        ### 约谈统计
       # #rows = self.get_sql_result("select count(*) from (select uid from company_follow group by uid) as a")
       # rows = self.get_sql_result("select count(distinct uid) from company_follow ")
       # ret['m_start_yuetan_investor_total_num'] = int(rows[0][0]) if rows else 0
       # #rows = self.get_sql_result("select count(*) from (select uid from krplus2_%s.company_follow group by uid) as a"
       # rows = self.get_sql_result("select count(distinct uid) from krplus2_%s.company_follow"
       #                            %(self.report_last_month_end_date))
       # month_start_yuetan_investor_num = int(rows[0][0]) if rows else 0
       # ret['m_monthly_start_yuetan_investor_num'] = ret['m_start_yuetan_investor_total_num'] - month_start_yuetan_investor_num

       # #rows = self.get_sql_result("select count(*) from (select cid from company_follow group by cid) as a")
       # rows = self.get_sql_result("select count(distinct cid) from company_follow ")
       # ret['m_yuetan_coms_total_num'] = int(rows[0][0]) if rows else 0
       # #rows = self.get_sql_result("select count(*) from (select cid from krplus2_%s.company_follow group by cid) as a"
       # rows = self.get_sql_result("select count(distinct cid) from krplus2_%s.company_follow "
       #                            %(self.report_last_month_end_date))
       # month_yuetan_coms_num= int(rows[0][0]) if rows else 0
       # ret['m_monthly_yuetan_coms_num'] = ret['m_yuetan_coms_total_num'] - month_yuetan_coms_num

       # rows = self.get_sql_result("select count(*) from company_follow ")
       # total_yuetan_num= int(rows[0][0]) if rows else 0
       # rows = self.get_sql_result("select count(*) from krplus2_%s.company_follow "
       #                            %(self.report_last_month_end_date))
       # total_yuetan_num_last= int(rows[0][0]) if rows else 0
       # ret['m_monthly_yuetan_num'] = total_yuetan_num - total_yuetan_num_last


        rows = self.get_sql_result("select count(distinct from_uid) from inmail where direction=1 and content like '%在36氪融资平台上看到了%'")
        ret['m_start_yuetan_investor_total_num'] = int(rows[0][0]) if rows else 0
        #rows = self.get_sql_result("select count(distinct from_uid) from krplus2_%s.inmail where direction=1 and content like '%%在36氪融资平台上看到了%%'" %(self.report_last_month_end_date))
        #month_start_yuetan_investor_num = int(rows[0][0]) if rows else 0
        #ret['m_monthly_start_yuetan_investor_num'] = ret['m_start_yuetan_investor_total_num'] - month_start_yuetan_investor_num
        rows = self.get_sql_result("select count(distinct from_uid) from inmail where direction=1 and content like '%%在36氪融资平台上看到了%%' and create_date<='%s 23:59:59' and create_date >= '%s 00:00:00'" %(self.report_date2, self.report_month_date2))
        ret['m_monthly_start_yuetan_investor_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("select count(distinct to_uid) from inmail where direction=1 and content like '%在36氪融资平台上看到了%'")
        ret['m_yuetan_coms_total_num'] = int(rows[0][0]) if rows else 0
        #rows = self.get_sql_result("select count(distinct to_uid) from krplus2_%s.inmail where direction=1 and content like '%%在36氪融资平台上看到了%%'" %(self.report_last_month_end_date))
        #month_yuetan_coms_num= int(rows[0][0]) if rows else 0
        #ret['m_monthly_yuetan_coms_num'] = ret['m_yuetan_coms_total_num'] - month_yuetan_coms_num
        rows = self.get_sql_result("select count(distinct to_uid) from inmail where direction=1 and content like '%%在36氪融资平台上看到了%%' and create_date<='%s 23:59:59' and create_date >= '%s 00:00:00'" % (self.report_date2, self.report_month_date2))
        ret['m_monthly_yuetan_coms_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("select count(*) from inmail where direction=1 and content like '%在36氪融资平台上看到了%'")
        total_yuetan_num= int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("select count(*) from krplus2_%s.inmail where direction=1 and content like '%%在36氪融资平台上看到了%%'" %(self.report_last_month_end_date))
        total_yuetan_num_last= int(rows[0][0]) if rows else 0
        ret['m_monthly_yuetan_num'] = total_yuetan_num - total_yuetan_num_last

        ## 约谈的模板可以修改，文本匹配会有误差，更改为user，company的join查询
        ## 每日约谈明细
        #com_pat = re.compile(r'希望可以聊一聊(.*?)的融资事宜')
        #flag_pat = '在36氪融资平台上看到了贵司的详细介绍以及此轮的融资需求'
        #yuetan_info_list = set()
        #yuetan_com_cnt_dict = {}
        #yuetan_starter_uids = set()
        #sql_cmd = ("SELECT a.from_uid,b.name,a.content from inmail as a left join user as b on a.from_uid=b.id \
        #                            where a.direction = 1 and \
        #                            a.create_date <='%s 23:59:59' and a.create_date >= '%s 00:00:00'"
        #                           %(self.report_date2, self.report_date2))
        #rows = self.get_sql_result(sql_cmd)
        #for row in rows:
        #    if not flag_pat in row[2]:
        #        continue
        #    match_coms = com_pat.findall(row[2].replace('"','').replace('“','').replace('”',''))
        #    #print row[2]
        #    #有些用户可能会改模板，匹配不上，去掉
        #    if not match_coms:
        #        continue
        #    com_name = match_coms[0]
        #    if com_name in yuetan_com_cnt_dict:
        #        yuetan_com_cnt_dict[com_name] += 1
        #    else:
        #        yuetan_com_cnt_dict[com_name] = 1
        #    # 自己拼的sql，参数需要转义；如果写mysql参数列表的方式就不用，它自己会去做
        #    t = self.get_sql_result('select a.id,(b.status=3 or b.status=4 or b.status=5) as is_listed from company as a \
        #                         left join company_funds as b on a.id=b.cid where a.name="%s"'
        #                         %(MySQLdb.escape_string(com_name)))
        #    #print row[0],row[1],com_name,MySQLdb.escape_string(com_name)
        #    record = (row[0],row[1],t[0][0],com_name,t[0][1])
        #    yuetan_info_list.add(record)
        #    yuetan_starter_uids.add(row[0])

        #ret['m_daily_yuetan_coms_detail_list'] = ''
        #for (uid,uname,cid,cname,is_list) in yuetan_info_list:
        #    com_cnt = yuetan_com_cnt_dict[cname]
        #    ret['m_daily_yuetan_coms_detail_list'] += '%s\t%s\t%s\t%s\t%s\t%s\n' %(
        #                                         str(uid),uname,str(cid),cname,str(com_cnt),str(is_list))
        #ret['m_daily_yuetan_coms_detail_list'] = ret['m_daily_yuetan_coms_detail_list'].strip('\n')
        #ret['m_daily_start_yuetan_investor_num'] = len(yuetan_starter_uids)
        #ret['m_daily_yuetan_coms_num'] = len(yuetan_com_cnt_dict)
        #ret['m_daily_yuetan_num'] = sum(yuetan_com_cnt_dict.values())

        ## 每日约谈明细
        yuetan_info_dict = {}
        yuetan_com_cnt_dict = {}
        yuetan_starter_uids = set()
        yuetan_detail = ''
        sql_cmd = ("select * from \
                       (SELECT a.from_uid,b.name as from_uname,a.to_uid,c.name as to_uname, d.id as cid,d.name as cname, \
                                    (e.status=3 or e.status=4 or e.status=5) as is_listed, a.id from inmail as a \
                                    left join user as b on a.from_uid=b.id \
                                    left join user as c on a.to_uid=c.id \
                                    left join company as d on c.id=d.manager_id \
                                    left join company_funds as e on d.id=e.cid \
                                    where a.direction = 1 and \
                                    a.create_date <='%s 23:59:59' and a.create_date >= '%s 00:00:00'\
                                    and a.content like '%%在36氪融资平台上看到了%%' \
                                    order by e.update_date desc,e.id desc) \
                       as tt group by tt.id"
                       %(self.report_date2, self.report_date2))
        rows = self.get_sql_result(sql_cmd)
        for row in rows:
            from_uid = row[0]
            from_uname = row[1]
            to_uid = row[2]
            to_uname = row[3]
            cid = row[4]
            cname = row[5]
            #content = row[6]
            islisted = row[6]
            if cid in yuetan_com_cnt_dict:
                yuetan_com_cnt_dict[cid] += 1
            else:
                yuetan_com_cnt_dict[cid] = 1
            yuetan_starter_uids.add(from_uid)
            record = (from_uid,from_uname,cid,cname,islisted)
            if record in yuetan_info_dict:
                yuetan_info_dict[record] += 1
            else:
                yuetan_info_dict[record] = 1

        for rec in yuetan_info_dict:
            yuetan_detail += '%s\t%s\t%s\t%s\t%s\t%s\n'  % (
                             str(rec[0]), str(rec[1]), str(rec[2]), str(rec[3]), str(yuetan_info_dict[rec]), str(rec[4]))

        ret['m_daily_yuetan_coms_detail_list'] = yuetan_detail.strip('\n')
        ret['m_daily_start_yuetan_investor_num'] = len(yuetan_starter_uids)
        ret['m_daily_yuetan_coms_num'] = len(yuetan_com_cnt_dict)
        ret['m_daily_yuetan_num'] = sum(yuetan_com_cnt_dict.values())

        return ret

    '''
    ===========================
        company statistics
    ===========================
    '''
    def do_diff_com_list(self, base_list, cmp_list):
        ret = set()
        tmp = {}
        for t in cmp_list:
            tmp[t[0]] = 1
        for t in base_list:
            cid = t[0]
            name = t[1]
            if not cid in tmp:
                ret.add((str(cid)+'\t'+name))
        return '\n'.join(ret)

    def get_statistics_com_info(self, ret):
        ### 有主公司
        rows = self.get_sql_result("SELECT COUNT(1) FROM company WHERE manager_id != 0")
        ret['c_manager_com_total_num'] = int(rows[0][0]) if rows else '0'
        rows = self.get_sql_result("SELECT COUNT(1) FROM krplus2_%s.company where manager_id != 0" %(self.report_yesday_date))
        yes_manager_com_num = int(rows[0][0]) if rows else 0
        ret['c_daily_manager_com_num'] = ret['c_manager_com_total_num'] - yes_manager_com_num
        rows = self.get_sql_result("SELECT COUNT(1) FROM krplus2_%s.company where manager_id != 0" %(self.report_last_month_end_date))
        month_manager_com_num = int(rows[0][0]) if rows else 0
        ret['c_monthly_manager_com_num'] = ret['c_manager_com_total_num'] - month_manager_com_num

        #rows = self.get_sql_result("select count(distinct cid) from (select cid from company_funds where (status=6) group by cid) as a")
        rows = self.get_sql_result("select count(distinct cid) from company_funds where status=6")
        ret['c_fail_listed_com_num'] = int(rows[0][0]) if rows else 0

        ### 申请融资公司
        rows = self.get_sql_result("select count(distinct cid) from company_funds where (status=2 or status=3 or status=4 or status=5 or status=6) and type=0")
        ret['c_apply_financing_com_total_num'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("select count(distinct company_id) from \
                                   (select audit_id,company_id,company_name from audit_system_%s.audit_com_finance_apply t1 \
                                   left join audit_system_%s.audit t2 on t1.audit_id=t2.id \
                                   where t2.created_at>='%s 00:00:00' and t2.created_at<='%s 23:59:59' and t1.financing_type=0) as a"
                                   % (self.report_date, self.report_date, self.report_date2, self.report_date2))
        ret['c_daily_apply_financing_com_num'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("select count(distinct cid) from krplus2_%s.company_funds \
                    where (status=2 or status=3 or status=4 or status=5 or status=6) and type=0" %(self.report_last_month_end_date))
        month_apply_financing_com_num = int(rows[0][0]) if rows else 0
        ret['c_monthly_apply_financing_com_num'] = ret['c_apply_financing_com_total_num'] - month_apply_financing_com_num

        ### 审核通过公司
        rows = self.get_sql_result("select count(distinct cid) from company_funds where (status=3 or status=4) and type=0")
        ret['c_financing_audit_success_total_num'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("select count(distinct cid) from krplus2_%s.company_funds \
                    where (status=3 or status=4) and type=0" %(self.report_last_month_end_date))
        month_financing_audit_success_num = int(rows[0][0]) if rows else 0
        ret['c_monthly_financing_audit_success_num'] = ret['c_financing_audit_success_total_num'] - month_financing_audit_success_num

        rows = self.get_sql_result("select count(distinct cid) from company_funds where (status=3 or status=4 or status=5) and type=0")
        ret['c_financing_audit_success_total_num2'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("select count(distinct cid) from krplus2_%s.company_funds \
                    where (status=3 or status=4 or status=5) and type=0" %(self.report_last_month_end_date))
        month_financing_audit_success_num2 = int(rows[0][0]) if rows else 0
        ret['c_monthly_financing_audit_success_num2'] = ret['c_financing_audit_success_total_num2'] - month_financing_audit_success_num2

        rows = self.get_sql_result("select count(distinct company_id) from \
                                   (select audit_id,company_id,company_name from audit_system_%s.audit_com_finance_apply t1 \
                                   left join audit_system_%s.audit t2 on t1.audit_id=t2.id \
                                   where t2.updated_at>='%s 00:00:00' and t2.updated_at<='%s 23:59:59' \
                                   and t1.financing_type=0 and t2.status='approved') as a"
                                   %(self.report_date, self.report_date, self.report_date2, self.report_date2))
        ret['c_daily_financing_audit_success_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("select distinct a.company_id as t_cid,a.company_name as t_cname,(b.status=4) as is_recommended from \
                                   (select audit_id,company_id,company_name from audit_system_%s.audit_com_finance_apply t1 \
                                   left join audit_system_%s.audit t2 on t1.audit_id=t2.id \
                                   where t2.updated_at>='%s 00:00:00' and t2.updated_at<='%s 23:59:59' \
                                   and t1.financing_type=0 and t2.status='approved') as a\
                                   left join company_funds as b on a.company_id=b.cid"
                                   %(self.report_date, self.report_date, self.report_date2, self.report_date2))
        ret['c_daily_financing_audit_success_com_list'] = '\n'.join(map(lambda x: ('\t'.join([str(k) for k in x])), rows))

        ### 完成融资公司
        rows = self.get_sql_result("select distinct a.cid,b.name from company_funds as a inner join company as b on a.cid=b.id where a.status=5 and b.is_deleted=0")
        ret['c_finish_financing_com_total_num'] = len(rows) if rows else 0
        c_finish_financing_com_total_list = rows

        rows = self.get_sql_result("select distinct a.cid,b.name from krplus2_%s.company_funds as a inner join krplus2_%s.company as b on a.cid=b.id where a.status=5  and b.is_deleted=0 " %(self.report_last_month_end_date, self.report_last_month_end_date))
        month_finish_financing_com_num = len(rows) if rows else 0
        ret['c_monthly_finish_financing_com_num'] = ret['c_finish_financing_com_total_num'] - month_finish_financing_com_num

        rows = self.get_sql_result("select distinct a.cid,b.name from krplus2_%s.company_funds as a inner join krplus2_%s.company as b on a.cid=b.id where a.status=5  and b.is_deleted=0 " %(self.report_yesday_date, self.report_yesday_date))
        yes_finish_financing_com_num = len(rows) if rows else 0
        yes_finish_financing_com_list = rows
        ret['c_daily_finish_financing_com_num'] = ret['c_finish_financing_com_total_num'] - yes_finish_financing_com_num
        ret['c_daily_finish_financing_com_list'] = self.do_diff_com_list(c_finish_financing_com_total_list,yes_finish_financing_com_list)

        ### 公司完整度
        rows = self.get_sql_result("select count(*) from company \
                                    where name!='' and brief !='' and logo !='' and address1!=0 \
                                    and industry!=0 and intro!=''")
        ret['c_integrity_com_total_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("select id,name from company \
                                    where name!='' and brief !='' and logo !='' and address1!=0 and industry!=0 and intro!='' \
                                    and (create_date >= '%s 00:00:00' and create_date <= '%s 23:59:59')"
                                   %(self.report_month_date2, self.report_date2))
        ret['c_monthly_integrity_com_num'] = len(rows)
        monthly_integrity_com_list = rows

        rows = self.get_sql_result("select id,name from company \
                                    where name!='' and brief !='' and logo !='' and address1!=0 \
                                    and industry!=0 and intro!='' and (create_date >= '%s 00:00:00' and create_date <= '%s 23:59:59')"
                                    %(self.report_month_date2, self.report_yesday_date2))
        monthly_integrity_yesday_com_list = rows

        rows = self.get_sql_result("select id,name from krplus2_%s.company \
                                    where name!='' and brief !='' and logo !='' and address1!=0 \
                                    and industry!=0 and intro!='' and (create_date >= '%s 00:00:00' and create_date <= '%s 23:59:59')"
                                    %(self.report_yesday_date, self.report_month_date2, self.report_yesday_date2))
        ret['c_daily_integrity_com_num'] = int(ret['c_monthly_integrity_com_num']) - len(rows)
        monthly_integrity_yesday2_com_list = rows

        ## diff new integrity coms
        ret['c_daily_integrity_com_list'] = self.do_diff_com_list(monthly_integrity_com_list, monthly_integrity_yesday2_com_list)

        return ret

    '''
    ===========================
        user statistics
    ===========================
    '''
    def get_statistics_user_info(self, ret):
        if not 'n_daily_unregister_uv' in ret:
            raise Exception('error: not found')
        ### 注册用户
        rows = self.get_sql_result("SELECT COUNT(*) FROM user where phone!=''")
        ret['u_register_total_num'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("SELECT COUNT(*) FROM krplus2_%s.user where phone!=''" %(self.report_yesday_date))
        yes_register_total_num = int(rows[0][0]) if rows else 0
        ret['u_daily_register_num'] = int(ret['u_register_total_num']) - yes_register_total_num
        rows = self.get_sql_result("SELECT COUNT(*) FROM krplus2_%s.user where phone!=''" %(self.report_last_month_end_date))
        month_register_total_num = int(rows[0][0]) if rows else 0
        ret['u_monthly_register_num'] = int(ret['u_register_total_num']) - month_register_total_num
        ret['u_daily_register_conversion_ratio'] = float('%0.5f' %(ret['u_daily_register_num'] * 1.0 / ret["n_daily_unregister_uv"]))

        ### 资料完善的用户
        rows = self.get_sql_result("SELECT COUNT(*) FROM user where phone!='' and avatar!='' and name!='' and email!=''")
        ret['u_integrity_user_total_num'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("SELECT COUNT(*) FROM krplus2_%s.user where phone!='' and avatar!='' and name!='' and email!=''"
                                    %(self.report_yesday_date))
        yes_integrity_user_total_num = int(rows[0][0]) if rows else 0
        ret['u_daily_integrity_user_num'] = ret['u_integrity_user_total_num'] - yes_integrity_user_total_num
        ret['u_daily_integrity_user_ratio'] = float('%0.5f' %(ret['u_daily_integrity_user_num'] * 1.0 / ret["u_daily_register_num"]))

        ### 创业者用户
        rows = self.get_sql_result("SELECT COUNT(*) FROM user WHERE enterpriser=1")
        ret['u_enterpriser_total_num'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("SELECT COUNT(*) FROM krplus2_%s.user where enterpriser=1" %(self.report_yesday_date))
        yes_enterpriser_total_num = int(rows[0][0]) if rows else 0
        ret['u_daily_enterpriser_num'] = ret['u_enterpriser_total_num'] - yes_enterpriser_total_num
        rows = self.get_sql_result("SELECT COUNT(*) FROM krplus2_%s.user where enterpriser=1" %(self.report_last_month_end_date))
        month_enterpriser_total_num = int(rows[0][0]) if rows else 0
        ret['u_monthly_enterpriser_num'] = ret['u_enterpriser_total_num'] - month_enterpriser_total_num

        ### 投资者用户
        rows = self.get_sql_result("SELECT COUNT(*) FROM user WHERE investor_type in (10,20)")
        ret['u_investor_total_num'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("SELECT COUNT(*) FROM krplus2_%s.user where investor_type in (10,20)" %(self.report_yesday_date))
        yes_investor_total_num = int(rows[0][0]) if rows else 0
        ret['u_daily_investor_num'] = ret['u_investor_total_num'] - yes_investor_total_num
        rows = self.get_sql_result("SELECT COUNT(*) FROM krplus2_%s.user where investor_type in (10,20)" %(self.report_last_month_end_date))
        month_investor_total_num = int(rows[0][0]) if rows else 0
        ret['u_monthly_investor_num'] = ret['u_investor_total_num'] - month_investor_total_num

        ### 创业者+投资用户
        rows = self.get_sql_result("SELECT COUNT(*) FROM user WHERE enterpriser=1 or investor_type in (10,20)")
        ret['u_core_user_total_num'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("SELECT COUNT(*) FROM krplus2_%s.user WHERE enterpriser=1 or investor_type in (10,20)"
                                   %(self.report_yesday_date))
        yes_core_user_total_num = int(rows[0][0]) if rows else 0
        ret['u_daily_core_user_num'] = ret['u_core_user_total_num'] - yes_core_user_total_num
        ret['u_daily_core_user_ratio'] = float('%0.5f' %(ret['u_daily_core_user_num'] * 1.0 / ret["u_daily_register_num"]))

        ##优质投资人
        rows = self.get_sql_result("SELECT COUNT(*) FROM user WHERE investor_type=10")
        ret['u_good_investor_total_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("SELECT COUNT(*) FROM user_invitation_code where apply_type=1 and status=1 and create_date<='%s 23:59:59' and create_date >= '%s 00:00:00'" %(self.report_date2, self.report_date2))
        ret['u_daily_apply_good_investor_num'] = int(rows[0][0]) if rows else 0

        return ret

    def get_all_statistics_info(self):
        ret = {}
        self.get_monthly_nginx_info(ret)
        self.get_daily_nginx_info(ret)
        self.get_statistics_user_info(ret)
        self.get_statistics_com_info(ret)
        self.get_statistics_interview_info(ret)
        self.get_statistics_audit_info(ret)
        self.get_collected_monthly_active_users(ret)
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
