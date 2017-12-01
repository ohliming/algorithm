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

    def get_cf_project_stat_info(self, ret):
        ## sum聚合函数，就是没结果，也会有一行null值，判断不要用rows
        rows = self.get_sql_result("SELECT COUNT(1) FROM crowd_funding WHERE status in (25,30,35,50) and id!=100")
        ret['cf_com_total_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("SELECT sum(cf_raising) FROM crowd_funding WHERE status in (25,30,35,50) and id!=100")
        ret['cf_target_raising_total_num'] = int(rows[0][0]) if rows[0][0] else 0

        #rows = self.get_sql_result("SELECT sum(cf_success_raising) FROM crowd_funding WHERE status in (25,30,35,50) and id!=100")
        #ret['cf_success_raising_total_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("SELECT sum(lead_investment) FROM crowd_funding WHERE status in (25,30,35,50) and id!=100")
        ret['cf_lead_investment_total_num'] = int(rows[0][0]) if rows[0][0] else 0

        rows = self.get_sql_result("select sum(investment) from trade_crowd_funding as a \
                                    inner join trade as b on a.trade_id=b.id where b.type=1 and a.cf_id!=100")
        ret['cf_co_investor_amount_money_total_num'] = int(rows[0][0]) if rows[0][0] else 0
        ret['cf_amount_money_total_num'] = ret['cf_co_investor_amount_money_total_num'] + ret['cf_lead_investment_total_num']
        rows = self.get_sql_result("select sum(investment) from trade_crowd_funding as a \
                                    inner join trade as b on a.trade_id=b.id where b.type=1 and b.status=3 and a.cf_id!=100 \
                                     ")
        ret['cf_co_investor_proceeds_money_total_num'] = int(rows[0][0]) if rows[0][0] else 0
        rows = self.get_sql_result("select sum(amount) from trade where type=2 and status=3  ")
        ret['cf_co_investor_proceeds_money_total_num_2'] = int(rows[0][0]) if rows[0][0] else 0
        rows = self.get_sql_result("select sum(amount) from trade where type=2 and status in (5,6) ")
        ret['cf_co_investor_proceeds_money_total_num_2_56'] = int(rows[0][0]) if rows[0][0] else 0
        rows = self.get_sql_result("select sum(amount) from trade where type=3 and status=3  ")
        ret['cf_co_investor_proceeds_money_total_num_3'] = int(rows[0][0]) if rows[0][0] else 0
        ret['cf_success_raising_total_num'] = ret['cf_co_investor_proceeds_money_total_num'] + ret['cf_lead_investment_total_num']

        rows = self.get_sql_result("SELECT count(1) FROM  trade where type=1 and goods_id!=100 ")
        ret['cf_co_investor_trade_total_num'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("SELECT count(1) FROM  trade where  type=2 and status=3 and goods_id!=100  ")
        ret['cf_co_investor_trade_success_total_num_2'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("SELECT count(1) FROM  trade where  type=2 and status in (5,6) and goods_id!=100  ")
        ret['cf_co_investor_trade_success_total_num_2_56'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("SELECT count(1) FROM  trade where  type=3 and status=3 and goods_id!=100  ")
        ret['cf_co_investor_trade_success_total_num_3'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where type=2 and status=3 and goods_id!=100  ")
        ret['cf_trade_success_co_investor_total_num_2'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where type=2 and status in (5,6) and goods_id!=100  ")
        ret['cf_trade_success_co_investor_total_num_2_56'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where type=3 and  status=3 and goods_id!=100  ")
        ret['cf_trade_success_co_investor_total_num_3'] = int(rows[0][0]) if rows else 0
        #rows = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where status in (1,2,3,8) and goods_id!=100")
        rows = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where goods_id!=100")
        ret['cf_trade_created_co_investor_total_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("select count(distinct(b.creator)) \
                                    from audit_system_%s.audit_co_investor as a \
                                    inner join audit_system_%s.audit as b on a.audit_id=b.id" %(self.report_date, self.report_date))
        ret['cf_apply_co_investor_total_num'] = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("select count(distinct(b.creator)) \
                                    from audit_system_%s.audit_co_investor as a \
                                    inner join audit_system_%s.audit as b on a.audit_id=b.id \
                                    where b.status='approved'" %(self.report_date, self.report_date))
        ret['cf_approved_co_investor_total_num'] = int(rows[0][0]) if rows else 0

        rows = self.get_sql_result("select count(distinct b.creator) \
                                   from audit_system_%s.audit_co_investor as a \
                                   inner join audit_system_%s.audit as b on a.audit_id=b.id \
                                   where a.created_at >= '%s 00:00:00' and a.created_at <= '%s 23:59:59'"
                                   % (self.report_date, self.report_date, self.report_date2, self.report_date2))
        total_daily_audit_investor = int(rows[0][0]) if rows else 0
        rows = self.get_sql_result("select count(distinct b.creator) \
                                    from audit_system_%s.audit_co_investor as a \
                                    inner join audit_system_%s.audit as b on a.audit_id=b.id \
                                    inner join krplus2_%s.user as c on c.id=b.creator \
                                    where (c.cteate_time >= '%s 00:00:00' and c.cteate_time <= '%s 23:59:59') \
                                    and (a.created_at >= '%s 00:00:00' and a.created_at <= '%s 23:59:59')"
                                    % (self.report_date, self.report_date, self.report_date, self.report_date2, self.report_date2, self.report_date2, self.report_date2))
        total_daily_audit_investor_and_register = int(rows[0][0]) if rows else 0
        ret["cf_daily_apply_investor_todayreg"] = total_daily_audit_investor_and_register
        ret["cf_daily_apply_investor_nontodayreg"] = total_daily_audit_investor - total_daily_audit_investor_and_register
        return ret

    def get_cf_pre_project_detail_info(self, ret_dict):
        rows = self.get_sql_result("SELECT a.id,b.name,a.financing_type,a.publish_time,a.start_time \
                    ,a.days,TO_DAYS(close_time)-TO_DAYS(start_time),a.operate_comment, \
                    a.cf_raising,a.cf_max_raising,a.cf_min_raising,a.lead_investment,a.lead_user_id,a.lead_org_id  \
                    ,a.cf_success_raising,b.manager_id,a.status \
                    FROM crowd_funding as a inner join company as b on a.company_id=b.id WHERE a.status in (25,30) and a.id!=100 \
                    and (('%s 23:59:59' < a.start_time and '%s 23:59:59' > a.publish_time) or a.status=25)"
                    %(self.report_date2, self.report_date2))
        cf_pre_heat_com_info_list = []
        for row in rows:
            record = []
            cf_id = row[0]
            cf_name = row[1]
            cf_type = '新股' if row[2] ==1 else '旧股'
            cf_publish_time = str(row[3])
            cf_start_time = str(row[4])
            cf_expect_days = str(row[5])
            cf_real_days = str(row[6])
            cf_comment = str(row[7])
            cf_raising = str(row[8])
            cf_max_raising = str(row[9])
            cf_min_raising = str(row[10])
            lead_investment = str(row[11]) if row[11] else '0'
            lead_name = ''
            if row[12] !=0:
                ret = self.get_sql_result("SELECT name from user where id=%d" %row[12])
                lead_name = ret[0][0] if ret else ''
            elif row[13]!=0:
                ret = self.get_sql_result("select name_abbr from organization where id=%d" %row[13])
                lead_name = ret[0][0] if ret else ''
            lead_name = '' if not lead_name else lead_name

            #cf_success_raising = str(row[14])
            manager_id = row[15]
            status_id = row[16]

            ret = self.get_sql_result("select sum(investment) from trade_crowd_funding as a \
                                       inner join trade as b on a.trade_id=b.id where b.type=1 and  a.cf_id=%d \
                                        " %cf_id)
            cf_co_investor_amount_money_num = str(ret[0][0]) if ret[0][0] else '0'
            cf_amount_money_total_num = str(float(cf_co_investor_amount_money_num) + float(lead_investment))

            ret = self.get_sql_result("select sum(investment) from trade_crowd_funding as a \
                                       inner join trade as b on a.trade_id=b.id where a.cf_id=%d and b.type=1 and  b.status=3 \
                                        " %cf_id)
            cf_co_investor_proceeds_money_num = str(ret[0][0]) if ret[0][0] else '0'
            cf_success_raising = str(float(cf_co_investor_proceeds_money_num) + float(lead_investment))

            ret = self.get_sql_result("select sum(b.amount) from trade_crowd_funding as a \
                                       inner join trade as b on a.trade_id=b.parent_id where a.cf_id=%d and b.type=2 and  b.status=3 \
                                        " %cf_id)
            cf_co_investor_proceeds_money_num_2 = str(ret[0][0]) if ret[0][0] else '0'
            ret = self.get_sql_result("select sum(b.amount) from trade_crowd_funding as a \
                                       inner join trade as b on a.trade_id=b.parent_id where a.cf_id=%d and b.type=2 and  b.status in (5,6) \
                                        " %cf_id)
            cf_co_investor_proceeds_money_num_2_56 = str(ret[0][0]) if ret[0][0] else '0'
            ret = self.get_sql_result("select sum(b.amount) from trade_crowd_funding as a \
                                       inner join trade as b on a.trade_id=b.parent_id where a.cf_id=%d and b.type=3 and  b.status=3 \
                                        " %cf_id)
            cf_co_investor_proceeds_money_num_3 = str(ret[0][0]) if ret[0][0] else '0'

            ret = self.get_sql_result("SELECT count(1) FROM  trade where type=1 and  goods_id=%d   " %cf_id)
            cf_co_investor_trade_num = str(ret[0][0]) if ret else '0'
            ret = self.get_sql_result("SELECT count(1) FROM  trade where type=2 and  status=3 and goods_id=%d  " %cf_id)
            cf_co_investor_trade_success_num_2 = str(ret[0][0]) if ret else '0'
            ret = self.get_sql_result("SELECT count(1) FROM  trade where type=2 and  status in (5,6) and goods_id=%d  " %cf_id)
            cf_co_investor_trade_success_num_2_56 = str(ret[0][0]) if ret else '0'
            ret = self.get_sql_result("SELECT count(1) FROM  trade where type=3 and  status=3 and goods_id=%d  " %cf_id)
            cf_co_investor_trade_success_num_3 = str(ret[0][0]) if ret else '0'

            ret = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where type=2 and status=3 and goods_id=%d  " %cf_id)
            cf_trade_success_co_investor_num_2 = str(ret[0][0]) if ret else '0'
            ret = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where type=2 and status in (5,6) and goods_id=%d  " %cf_id)
            cf_trade_success_co_investor_num_2_56 = str(ret[0][0]) if ret else '0'
            ret = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where type=3 and  status=3 and goods_id=%d  " %cf_id)
            cf_trade_success_co_investor_num_3 = str(ret[0][0]) if ret else '0'
            ret = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where goods_id=%d  " %cf_id)
            cf_trade_created_co_investor_num = str(ret[0][0]) if ret else '0'

            ret = self.get_sql_result("select count(id) from inmail where direction=1 and to_uid=%d and \
                  from_uid in (SELECT distinct(user_id) as tuid FROM  trade where goods_id=%d)"
                  %(manager_id,cf_id))
            cf_com_yuetan_num = str(ret[0][0]) if ret else '0'

            ## get result
            record.append(cf_name)
            record.append(cf_type)
            record.append(cf_publish_time)
            record.append(cf_start_time)
            record.append(cf_expect_days)
            record.append(cf_real_days)
            record.append(cf_comment)
            record.append(cf_raising)
            record.append(cf_max_raising)
            record.append(cf_min_raising)
            record.append(lead_name)
            record.append(cf_amount_money_total_num)
            record.append(cf_success_raising)
            record.append(lead_investment)
            record.append(cf_co_investor_amount_money_num)
            record.append(cf_co_investor_proceeds_money_num)
            record.append(cf_co_investor_proceeds_money_num_2)
            record.append(cf_co_investor_proceeds_money_num_2_56)
            record.append(cf_co_investor_proceeds_money_num_3)
            record.append(cf_co_investor_trade_num)
            record.append(cf_co_investor_trade_success_num_2)
            record.append(cf_co_investor_trade_success_num_2_56)
            record.append(cf_co_investor_trade_success_num_3)
            record.append(cf_trade_created_co_investor_num)
            record.append(cf_trade_success_co_investor_num_2)
            record.append(cf_trade_success_co_investor_num_2_56)
            record.append(cf_trade_success_co_investor_num_3)
            record.append(cf_com_yuetan_num)
            cf_pre_heat_com_info_list.append('\t'.join(record))

        ret_dict['cf_pre_heat_com_info_list'] = '\n'.join(cf_pre_heat_com_info_list)

    def get_cf_project_detail_info(self, ret_dict):
        rows = self.get_sql_result("SELECT a.id,b.name,a.financing_type,a.publish_time,a.start_time \
                    ,a.days,TO_DAYS(close_time)-TO_DAYS(start_time),a.operate_comment, \
                    a.cf_raising,a.cf_max_raising,a.cf_min_raising,a.lead_investment,a.lead_user_id,a.lead_org_id  \
                    ,a.cf_success_raising,b.manager_id,a.status \
                    FROM crowd_funding as a inner join company as b on a.company_id=b.id WHERE a.status in (30,35,50) and a.id!=100 \
                    and '%s 23:59:59' > a.start_time "
                    %(self.report_date2))
                    #and '%s 23:59:59' > a.start_time and '%s 23:59:59' < a.end_time"
        cf_investing_com_info_list = []
        cf_finished_com_info_list = []
        for row in rows:
            record = []
            cf_id = row[0]
            cf_name = row[1]
            cf_type = '新股' if row[2] ==1 else '旧股'
            cf_publish_time = str(row[3])
            cf_start_time = str(row[4])
            cf_expect_days = str(row[5])
            cf_real_days = str(row[6])
            cf_comment = str(row[7])
            cf_raising = str(row[8])
            cf_max_raising = str(row[9])
            cf_min_raising = str(row[10])
            lead_investment = str(row[11]) if row[11] else '0'
            lead_name = ''
            if row[12] !=0:
                ret = self.get_sql_result("SELECT name from user where id=%d" %row[12])
                lead_name = ret[0][0] if ret else ''
            elif row[13]!=0:
                ret = self.get_sql_result("select name from organization where id=%d" %row[13])
                lead_name = ret[0][0] if ret else ''
            lead_name = '' if not lead_name else lead_name

            #cf_success_raising = str(row[14])
            manager_id = row[15]
            status_id = row[16]

            ret = self.get_sql_result("select sum(investment) from trade_crowd_funding as a \
                                       inner join trade as b on a.trade_id=b.id where b.type=1 and a.cf_id=%d  " %cf_id)
            cf_co_investor_amount_money_num = str(ret[0][0]) if ret[0][0] else '0'
            cf_amount_money_total_num = str(float(cf_co_investor_amount_money_num) + float(lead_investment))

            ret = self.get_sql_result("select sum(investment) from trade_crowd_funding as a \
                                       inner join trade as b on a.trade_id=b.id where a.cf_id=%d and b.type=1 and b.status=3  " %cf_id)
            cf_co_investor_proceeds_money_num = str(ret[0][0]) if ret[0][0] else '0'
            cf_success_raising = str(float(cf_co_investor_proceeds_money_num) + float(lead_investment))

            ret = self.get_sql_result("select sum(b.amount) from trade_crowd_funding as a \
                                       inner join trade as b on a.trade_id=b.parent_id where a.cf_id=%d and b.type=2 and b.status=3  " %cf_id)
            cf_co_investor_proceeds_money_num_2 = str(ret[0][0]) if ret[0][0] else '0'
            ret = self.get_sql_result("select sum(b.amount) from trade_crowd_funding as a \
                                       inner join trade as b on a.trade_id=b.parent_id where a.cf_id=%d and b.type=2 and b.status in (5,6)  " %cf_id)
            cf_co_investor_proceeds_money_num_2_56 = str(ret[0][0]) if ret[0][0] else '0'
            ret = self.get_sql_result("select sum(b.amount) from trade_crowd_funding as a \
                                       inner join trade as b on a.trade_id=b.parent_id where a.cf_id=%d and b.type=3 and b.status=3  " %cf_id)
            cf_co_investor_proceeds_money_num_3 = str(ret[0][0]) if ret[0][0] else '0'

            ret = self.get_sql_result("SELECT count(1) FROM  trade where type=1 and  goods_id=%d  " %cf_id)
            cf_co_investor_trade_num = str(ret[0][0]) if ret else '0'
            ret = self.get_sql_result("SELECT count(1) FROM  trade where status=3 and type=2 and goods_id=%d  " %cf_id)
            cf_co_investor_trade_success_num_2 = str(ret[0][0]) if ret else '0'
            ret = self.get_sql_result("SELECT count(1) FROM  trade where status in (5,6) and type=2 and goods_id=%d  " %cf_id)
            cf_co_investor_trade_success_num_2_56 = str(ret[0][0]) if ret else '0'
            ret = self.get_sql_result("SELECT count(1) FROM  trade where status=3 and type=3 and goods_id=%d  " %cf_id)
            cf_co_investor_trade_success_num_3 = str(ret[0][0]) if ret else '0'

            ret = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where type=2 and status=3 and goods_id=%d  " %cf_id)
            cf_trade_success_co_investor_num_2 = str(ret[0][0]) if ret else '0'
            ret = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where type=2 and status in (5,6) and goods_id=%d  " %cf_id)
            cf_trade_success_co_investor_num_2_56 = str(ret[0][0]) if ret else '0'
            ret = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where type=3 and status=3 and goods_id=%d  " %cf_id)
            cf_trade_success_co_investor_num_3 = str(ret[0][0]) if ret else '0'
            ret = self.get_sql_result("SELECT count(distinct(user_id)) FROM  trade where goods_id=%d  " %cf_id)
            cf_trade_created_co_investor_num = str(ret[0][0]) if ret else '0'

            ret = self.get_sql_result("select count(id) from inmail where direction=1 and to_uid=%d and \
                  from_uid in (SELECT distinct(user_id) as tuid FROM  trade where goods_id=%d)"
                  %(manager_id,cf_id))
            cf_com_yuetan_num = str(ret[0][0]) if ret else '0'

            ## get result
            record.append(cf_name)
            record.append(cf_type)
            record.append(cf_publish_time)
            record.append(cf_start_time)
            record.append(cf_expect_days)
            record.append(cf_real_days)
            record.append(cf_comment)
            record.append(cf_raising)
            record.append(cf_max_raising)
            record.append(cf_min_raising)
            record.append(lead_name)
            record.append(cf_amount_money_total_num)
            record.append(cf_success_raising)
            record.append(lead_investment)
            record.append(cf_co_investor_amount_money_num)
            record.append(cf_co_investor_proceeds_money_num)
            record.append(cf_co_investor_proceeds_money_num_2)
            record.append(cf_co_investor_proceeds_money_num_2_56)
            record.append(cf_co_investor_proceeds_money_num_3)
            record.append(cf_co_investor_trade_num)
            record.append(cf_co_investor_trade_success_num_2)
            record.append(cf_co_investor_trade_success_num_2_56)
            record.append(cf_co_investor_trade_success_num_3)
            record.append(cf_trade_created_co_investor_num)
            record.append(cf_trade_success_co_investor_num_2)
            record.append(cf_trade_success_co_investor_num_2_56)
            record.append(cf_trade_success_co_investor_num_3)
            record.append(cf_com_yuetan_num)
            if status_id == 50:
                cf_finished_com_info_list.append('\t'.join(record))
            else:
                cf_investing_com_info_list.append('\t'.join(record))

        ret_dict['cf_finished_com_info_list'] = '\n'.join(cf_finished_com_info_list)
        ret_dict['cf_investing_com_info_list'] = '\n'.join(cf_investing_com_info_list)

    def get_monthly_crowd_funding_info(self, ret):
        #data = self._get_uv_and_pv(self.ng_monthly_log_file, "month")
        ret['cf_monthly_home_page_pv'] = 0
        ret['cf_monthly_detail_page_pv'] = 0
        ret['cf_monthly_pay_page_pv'] = 0
        ret['cf_monthly_confirm_page_pv'] = 0
        ret['cf_monthly_investor_validate_page_pv'] = 0
        ret['cf_monthly_investor_validate_page_mobile_pv'] = 0
        ret['cf_monthly_investor_validate_page_pc_pv'] = 0
        ret['cf_monthly_home_page_uv'] = 0
        ret['cf_monthly_detail_page_uv'] = 0
        ret['cf_monthly_pay_page_uv'] = 0
        ret['cf_monthly_confirm_page_uv'] = 0
        ret['cf_monthly_investor_validate_page_uv'] = 0

    def get_daily_crowd_funding_info(self, ret):
        #data = self._get_uv_and_pv(self.ng_daily_log_file, "day")
        ret['cf_daily_home_page_pv'] = 0
        ret['cf_daily_detail_page_pv'] = 0
        ret['cf_daily_pay_page_pv'] = 0
        ret['cf_daily_confirm_page_pv'] = 0
        ret['cf_daily_investor_validate_page_pv'] = 0
        ret['cf_daily_investor_validate_page_mobile_pv'] = 0
        ret['cf_daily_investor_validate_page_pc_pv'] = 0
        ret['cf_daily_home_page_uv'] = 0
        ret['cf_daily_detail_page_uv'] = 0
        ret['cf_daily_pay_page_uv'] = 0
        ret['cf_daily_confirm_page_uv'] = 0
        ret['cf_daily_investor_validate_page_uv'] = 0
        ret['cf_daily_validated_user_uv'] = 0
        ret['cf_daily_validated_user_detail_uv'] = 0
        ret['cf_daily_all_validated_user_detail_uv'] = 0
        ret['cf_daily_validated_user_uv_ratio'] = 0
        ret['cf_daily_slider_rongzi_uv_list'] = ''
        ret['cf_daily_slider_rongzi_pv_list'] = ''

    def _get_uv_and_pv(self, filename, period="month"):
        ret = {}
        ret['home_page_pv'] = 0
        ret['detail_page_pv'] = 0
        home_page_uids = set()
        detail_page_uids = set()

        slider_page_pv={"2":0,"3":0,"4":0,"5":0}
        slider_page_uv_set={"2":set(),"3":set(),"4":set(),"5":set()}

        ret['pay_page_pv'] = 0
        ret['confirm_page_pv'] = 0
        ret['investor_validate_page_pv'] = 0
        ret['investor_validate_page_mobile_pv'] = 0
        ret['investor_validate_page_pc_pv'] = 0
        pay_page_uids = set()
        confirm_page_uids = set()
        investor_validate_page_uids = set()

        uids_yestoday_validated = {}
        ret['validated_user_uv'] = 0
        ret['validated_user_uv_ratio'] = 0.0
        ret['validated_user_detail_uv'] = 0
        home_page_validated_uids = set()
        detail_page_validated_uids = set()
        detail_page_all_validated_uids = set()
        if period=="day":
            uids_yestoday_validated = self._get_yestoday_validated_uids()
            uids_validated = self._get_validated_uids()

        for line in open(filename):
            line = line.strip('\n')
            uid_arr = line.split('"')[-1].strip().split(' ')
            uid = uid_arr[1] if len(uid_arr) >1 else '0'
            cookie_id = uid_arr[2] if len(uid_arr) >2 else '0'
            key = uid if uid != '0' else cookie_id

            #line = urllib.unquote(line)
            if 'u=%2Fzhongchou&h=rong.36kr.com' in line:
                ret['home_page_pv'] += 1
                home_page_uids.add(key)
                if period=="day":
                    if uid in uids_yestoday_validated:
                        home_page_validated_uids.add(uid)
            #elif 'u=%2Fcompany%2F145336%2Ffinance%3FfundingId%3D102&h=rong.36kr.com' in line:
            elif re.search(r'u=%2Fcompany%2F\d+%2Ffinance%3FfundingId%3D\d+&h=rong.36kr.com', line):
                ret['detail_page_pv'] += 1
                detail_page_uids.add(key)
                if period=="day":
                    if uid in uids_yestoday_validated:
                        detail_page_validated_uids.add(uid)
                    if uid in uids_validated:
                        detail_page_all_validated_uids.add(uid)
            #elif 'u=%2Fzhongchou%2Fpay%3Ftid%3D1520&h=rong.36kr.com' in line:
            elif re.search(r'u=%2Fzhongchou%2Fpay%3Ftid%3D\d+&h=rong.36kr.com', line):
                ret['pay_page_pv'] += 1
                pay_page_uids.add(key)
            #elif 'u=%2Fzhongchou%2Fconfirm%3Fcid%3D145336%26fundingId%3D102&h=rong.36kr.com' in line:
            elif re.search(r'u=%2Fzhongchou%2Fconfirm%3Fcid%3D\d+%26fundingId%3D\d+&h=rong.36kr.com', line):
                ret['confirm_page_pv'] += 1
                confirm_page_uids.add(key)
            elif 'u=%2FinvestorValidate&h=rong.36kr.com' in line:
                ret['investor_validate_page_pv'] += 1
                investor_validate_page_uids.add(key)
                if 'iPhone' in line or 'Android' in line:
                    ret['investor_validate_page_mobile_pv'] += 1
                else:
                    ret['investor_validate_page_pc_pv'] += 1
            else:
                if period=="day":
                    if re.search(r'u=%2Fcompany%2F(\d+)%2Foverview%3FfromIndexSlider%3D(\d+)', line):
                        rid = re.search(r'u=%2Fcompany%2F(\d+)%2Foverview%3FfromIndexSlider%3D(\d+)', line).group(2)
                        if rid in slider_page_pv:
                            slider_page_pv[rid] += 1
                        else:
                            slider_page_pv[rid] = 1
                        if rid in slider_page_uv_set:
                            slider_page_uv_set[rid].add(key)
                        else:
                            slider_page_uv_set[rid] = set([key])

        slider_page_uv={}
        for k in slider_page_uv_set:
            slider_page_uv[k] = len(slider_page_uv_set[k])
        tmp_spp = slider_page_pv.items()
        tmp_spp.sort(key=lambda x:int(x[0]))
        tmp_spu = slider_page_uv.items()
        tmp_spu.sort(key=lambda x:int(x[0]))
        ret['slider_rongzi_uv_list'] = "\n".join(["slider-"+a[0]+"\t"+str(a[1]) for a in tmp_spu])
        ret['slider_rongzi_pv_list'] = "\n".join(["slider-"+a[0]+"\t"+str(a[1]) for a in tmp_spp])

        ret['home_page_uv'] = len(home_page_uids)
        ret['detail_page_uv'] = len(detail_page_uids)
        ret['pay_page_uv'] = len(pay_page_uids)
        ret['confirm_page_uv'] = len(confirm_page_uids)
        ret['investor_validate_page_uv'] = len(investor_validate_page_uids)
        ret['validated_user_uv'] = len(home_page_validated_uids)
        ret['validated_user_detail_uv'] = len(detail_page_validated_uids)
        ret['all_validated_user_detail_uv'] = len(detail_page_all_validated_uids)
        ret['validated_user_uv_ratio'] = ret['validated_user_uv']*1.0/len(uids_yestoday_validated) if uids_yestoday_validated else 0.0
        return ret

    def get_daily_crowd_funding_info_v2(self,ret):
	## pv
        ret['cf_v2_daily_home_page_pv'] = 0
        ret['cf_v2_daily_home_page_pc_pv'] = 0
        ret['cf_v2_daily_home_page_h5_pv'] = 0

        ret['cf_v2_daily_detail_page_pv'] = 0
        ret['cf_v2_daily_detail_page_pc_pv'] = 0
        ret['cf_v2_daily_detail_page_h5_pv'] = 0

        ret['cf_v2_daily_validate_page_pv'] = 0
        ret['cf_v2_daily_validate_page_pc_pv'] = 0
        ret['cf_v2_daily_validate_page_h5_pv'] = 0

        ret['cf_v2_daily_confirm_page_pv'] = 0
        ret['cf_v2_daily_confirm_page_pc_pv'] = 0
        ret['cf_v2_daily_confirm_page_h5_pv'] = 0

        ret['cf_v2_daily_order_page_pv'] = 0
        ret['cf_v2_daily_order_page_pc_pv'] = 0
        ret['cf_v2_daily_order_page_h5_pv'] = 0

        ret['cf_v2_daily_confirm_order_page_pv'] = 0
        ret['cf_v2_daily_confirm_order_page_pc_pv'] = 0
        ret['cf_v2_daily_confirm_order_page_h5_pv'] = 0

        ret['cf_v2_daily_pay_page_pv'] = 0
        ret['cf_v2_daily_pay_page_pc_pv'] = 0
        ret['cf_v2_daily_pay_page_h5_pv'] = 0

        ret['cf_v2_daily_payway_page_pv'] = 0
        ret['cf_v2_daily_payway_page_pc_pv'] = 0
        ret['cf_v2_daily_payway_page_h5_pv'] = 0

        ret['cf_v2_daily_confirmway_page_pv'] = 0
        ret['cf_v2_daily_confirmway_page_pc_pv'] = 0
        ret['cf_v2_daily_confirmway_page_h5_pv'] = 0

        ret['cf_v2_daily_news_page_pv'] = 0
        ret['cf_v2_daily_news_page_pc_pv'] = 0
        ret['cf_v2_daily_news_page_h5_pv'] = 0

        ret['cf_v2_daily_news_detail_page_pv'] = 0
        ret['cf_v2_daily_news_detail_page_pc_pv'] = 0
        ret['cf_v2_daily_news_detail_page_h5_pv'] = 0

        ret['cf_v2_daily_procedure_page_pv'] = 0
        ret['cf_v2_daily_procedure_page_pc_pv'] = 0
        ret['cf_v2_daily_procedure_page_h5_pv'] = 0

        ret['cf_v2_daily_payoutline_page_pv'] = 0
        ret['cf_v2_daily_payoutline_page_pc_pv'] = 0
        ret['cf_v2_daily_payoutline_page_h5_pv'] = 0

	## uv
        cf_v2_daily_home_page_uv = set()
        cf_v2_daily_home_page_pc_uv = set()
        cf_v2_daily_home_page_h5_uv = set()

        cf_v2_daily_detail_page_uv = set()
        cf_v2_daily_detail_page_pc_uv = set()
        cf_v2_daily_detail_page_h5_uv = set()

        cf_v2_daily_validate_page_uv = set()
        cf_v2_daily_validate_page_pc_uv = set()
        cf_v2_daily_validate_page_h5_uv = set()

        cf_v2_daily_confirm_page_uv = set()
        cf_v2_daily_confirm_page_pc_uv = set()
        cf_v2_daily_confirm_page_h5_uv = set()

        cf_v2_daily_order_page_uv = set()
        cf_v2_daily_order_page_pc_uv = set()
        cf_v2_daily_order_page_h5_uv = set()

        cf_v2_daily_confirm_order_page_uv = set()
        cf_v2_daily_confirm_order_page_pc_uv = set()
        cf_v2_daily_confirm_order_page_h5_uv = set()

        cf_v2_daily_pay_page_uv = set()
        cf_v2_daily_pay_page_pc_uv = set()
        cf_v2_daily_pay_page_h5_uv = set()

        cf_v2_daily_payway_page_uv = set()
        cf_v2_daily_payway_page_pc_uv = set()
        cf_v2_daily_payway_page_h5_uv = set()

        cf_v2_daily_confirmway_page_uv = set()
        cf_v2_daily_confirmway_page_pc_uv = set()
        cf_v2_daily_confirmway_page_h5_uv = set()

        cf_v2_daily_news_page_uv = set()
        cf_v2_daily_news_page_pc_uv = set()
        cf_v2_daily_news_page_h5_uv = set()

        cf_v2_daily_news_detail_page_uv = set()
        cf_v2_daily_news_detail_page_pc_uv = set()
        cf_v2_daily_news_detail_page_h5_uv = set()

        cf_v2_daily_procedure_page_uv = set()
        cf_v2_daily_procedure_page_pc_uv = set()
        cf_v2_daily_procedure_page_h5_uv = set()

        cf_v2_daily_payoutline_page_uv = set()
        cf_v2_daily_payoutline_page_pc_uv = set()
        cf_v2_daily_payoutline_page_h5_uv = set()

        uids_validated = self._get_validated_uids()

        for line in open(self.ng_daily_log_file):
            line = line.strip('\n')
            uid_arr = line.split('"')[-1].strip().split(' ')
            uid = uid_arr[1] if len(uid_arr) >1 else '0'
            cookie_id = uid_arr[2] if len(uid_arr) >2 else '0'
            key = uid if uid != '0' else cookie_id

            line = urllib.unquote(line)
            if not 'hm.gif?u=' in line:
                continue
            line = line.split('hm.gif?')[1]

	    ## h5
            if 'https://rong.36kr.com/m/' in line:
                m1 = re.match('u=/zhongchou&', line)
                if m1:
                    ret['cf_v2_daily_home_page_pv'] += 1
                    ret['cf_v2_daily_home_page_h5_pv'] += 1
		    cf_v2_daily_home_page_uv.add(key)
		    cf_v2_daily_home_page_h5_uv.add(key)

                m1 = re.match('u=/zhongchouDetail\?companyId=(\d+)&fundingId=(\d+)&', line)
                if m1:
                    ret['cf_v2_daily_detail_page_pv'] += 1
                    ret['cf_v2_daily_detail_page_h5_pv'] += 1
		    cf_v2_daily_detail_page_uv.add(key)
		    cf_v2_daily_detail_page_h5_uv.add(key)

                m1 = re.match('u=/investorValidate&', line)
                if m1:
                    ret['cf_v2_daily_validate_page_pv'] += 1
                    ret['cf_v2_daily_validate_page_h5_pv'] += 1
		    cf_v2_daily_validate_page_uv.add(key)
		    cf_v2_daily_validate_page_h5_uv.add(key)

                m1 = re.match('u=/zhongchouConfirm/(\d+)/(\d+)&', line)
                if m1:
                    ret['cf_v2_daily_confirm_page_pv'] += 1
                    ret['cf_v2_daily_confirm_page_h5_pv'] += 1
		    cf_v2_daily_confirm_page_uv.add(key)
		    cf_v2_daily_confirm_page_h5_uv.add(key)

                m1 = re.match('u=/zhongchouAllOrder&h=rong.36kr.com', line)
                if m1:
                    ret['cf_v2_daily_order_page_pv'] += 1
                    ret['cf_v2_daily_order_page_h5_pv'] += 1
		    cf_v2_daily_order_page_uv.add(key)
		    cf_v2_daily_order_page_h5_uv.add(key)

                m1 = re.match('u=/zhongchouConfirm/(\d+)/(\d+)&', line)
                m2 = re.match('u=/zhongchouAllOrder&h=rong.36kr.com', line)
                if m1 or m2:
                    ret['cf_v2_daily_confirm_order_page_pv'] += 1
                    ret['cf_v2_daily_confirm_order_page_h5_pv'] += 1
		    cf_v2_daily_confirm_order_page_uv.add(key)
		    cf_v2_daily_confirm_order_page_h5_uv.add(key)

                m1 = re.match('u=/zhongchouConfirm/(\d+)/(\d+)&', line)
                m2 = re.match('u=/zhongchouPayWay/(\d+)/', line)
                if m1 or m2:
                    ret['cf_v2_daily_pay_page_pv'] += 1
                    ret['cf_v2_daily_pay_page_h5_pv'] += 1
		    cf_v2_daily_pay_page_uv.add(key)
		    cf_v2_daily_pay_page_h5_uv.add(key)

                m1 = re.match('u=/zhongchouPayWay/(\d+)/', line)
                if m1:
                    ret['cf_v2_daily_payway_page_pv'] += 1
                    ret['cf_v2_daily_payway_page_h5_pv'] += 1
		    cf_v2_daily_payway_page_uv.add(key)
		    cf_v2_daily_payway_page_h5_uv.add(key)

                m1 = re.match('u=/zhongchouConfirm/(\d+)/(\d+)&', line)
                if m1:
                    ret['cf_v2_daily_confirmway_page_pv'] += 1
                    ret['cf_v2_daily_confirmway_page_h5_pv'] += 1
		    cf_v2_daily_confirmway_page_uv.add(key)
		    cf_v2_daily_confirmway_page_h5_uv.add(key)

                m1 = re.match('u=/zhongchouNews&', line)
                if m1:
                    ret['cf_v2_daily_news_page_pv'] += 1
                    ret['cf_v2_daily_news_page_h5_pv'] += 1
		    cf_v2_daily_news_page_uv.add(key)
		    cf_v2_daily_news_page_h5_uv.add(key)

                m1 = re.match('u=/zhongchouNews/detail\?id=(\d+)&', line)
                if m1:
                    ret['cf_v2_daily_news_detail_page_pv'] += 1
                    ret['cf_v2_daily_news_detail_page_h5_pv'] += 1
		    cf_v2_daily_news_detail_page_uv.add(key)
		    cf_v2_daily_news_detail_page_h5_uv.add(key)

                m1 = re.match('u=/procedure\?cfid=(\d+)', line)
                if m1:
                    ret['cf_v2_daily_procedure_page_pv'] += 1
                    ret['cf_v2_daily_procedure_page_h5_pv'] += 1
		    cf_v2_daily_procedure_page_uv.add(key)
		    cf_v2_daily_procedure_page_h5_uv.add(key)

                m1 = re.match('u=/zhongchou/payOutline\?tid=(\d+)', line)
                if m1:
                    ret['cf_v2_daily_payoutline_page_pv'] += 1
                    ret['cf_v2_daily_payoutline_page_h5_pv'] += 1
		    cf_v2_daily_payoutline_page_uv.add(key)
		    cf_v2_daily_payoutline_page_h5_uv.add(key)
	    ## pc
            else:
                m1 = re.match('u=/zhongchou&', line)
                if m1:
                    ret['cf_v2_daily_home_page_pv'] += 1
                    ret['cf_v2_daily_home_page_pc_pv'] += 1
		    cf_v2_daily_home_page_uv.add(key)
		    cf_v2_daily_home_page_pc_uv.add(key)

                m1 = re.match('u=/company/(\d+)/crowFunding\?fundingId=(\d+)&', line)
                if m1:
                    ret['cf_v2_daily_detail_page_pv'] += 1
                    ret['cf_v2_daily_detail_page_pc_pv'] += 1
		    cf_v2_daily_detail_page_uv.add(key)
		    cf_v2_daily_detail_page_pc_uv.add(key)

                m1 = re.match('u=/investorValidate&', line)
                if m1:
                    ret['cf_v2_daily_validate_page_pv'] += 1
                    ret['cf_v2_daily_validate_page_pc_pv'] += 1
		    cf_v2_daily_validate_page_uv.add(key)
		    cf_v2_daily_validate_page_pc_uv.add(key)

                m1 = re.match('u=/zhongchou/confirm\?cid=(\d+)&fundingId=(\d+)&', line)
                if m1:
                    ret['cf_v2_daily_confirm_page_pv'] += 1
                    ret['cf_v2_daily_confirm_page_pc_pv'] += 1
		    cf_v2_daily_confirm_page_uv.add(key)
		    cf_v2_daily_confirm_page_pc_uv.add(key)

                m1 = re.match('u=/uc/coinvest&', line)
                if m1:
                    ret['cf_v2_daily_order_page_pv'] += 1
                    ret['cf_v2_daily_order_page_pc_pv'] += 1
		    cf_v2_daily_order_page_uv.add(key)
		    cf_v2_daily_order_page_pc_uv.add(key)

                m1 = re.match('u=/zhongchou/confirm\?cid=(\d+)&fundingId=(\d+)&', line)
                m2 = re.match('u=/uc/coinvest&', line)
                if m1 or m2:
                    ret['cf_v2_daily_confirm_order_page_pv'] += 1
                    ret['cf_v2_daily_confirm_order_page_pc_pv'] += 1
		    cf_v2_daily_confirm_order_page_uv.add(key)
		    cf_v2_daily_confirm_order_page_pc_uv.add(key)

                m1 = re.match('u=/zhongchou/pay\?tid=(\d+)&', line)
                if m1:
                    ret['cf_v2_daily_pay_page_pv'] += 1
                    ret['cf_v2_daily_pay_page_pc_pv'] += 1
		    cf_v2_daily_pay_page_uv.add(key)
		    cf_v2_daily_pay_page_pc_uv.add(key)

                m1 = re.match('u=/zhongchou/pay\?tid=(\d+).+&r=https://uc.36kr.com/', line)
                if m1:
                    ret['cf_v2_daily_payway_page_pv'] += 1
                    ret['cf_v2_daily_payway_page_pc_pv'] += 1
		    cf_v2_daily_payway_page_uv.add(key)
		    cf_v2_daily_payway_page_pc_uv.add(key)

                m1 = re.match('u=/zhongchou/pay\?tid=(\d+)&type=\w+&h=rong.36kr.com', line)
                if m1:
                    ret['cf_v2_daily_confirmway_page_pv'] += 1
                    ret['cf_v2_daily_confirmway_page_pc_pv'] += 1
		    cf_v2_daily_confirmway_page_uv.add(key)
		    cf_v2_daily_confirmway_page_pc_uv.add(key)

                m1 = re.match('u=/zhongchouNews&', line)
                if m1:
                    ret['cf_v2_daily_news_page_pv'] += 1
                    ret['cf_v2_daily_news_page_pc_pv'] += 1
		    cf_v2_daily_news_page_uv.add(key)
		    cf_v2_daily_news_page_pc_uv.add(key)

                m1 = re.match('u=/zhongchouNews/detail\?id=(\d+)&', line)
                if m1:
                    ret['cf_v2_daily_news_detail_page_pv'] += 1
                    ret['cf_v2_daily_news_detail_page_pc_pv'] += 1
		    cf_v2_daily_news_detail_page_uv.add(key)
		    cf_v2_daily_news_detail_page_pc_uv.add(key)

                m1 = re.match('u=/procedure\?cfid=(\d+)', line)
                if m1:
                    ret['cf_v2_daily_procedure_page_pv'] += 1
                    ret['cf_v2_daily_procedure_page_pc_pv'] += 1
		    cf_v2_daily_procedure_page_uv.add(key)
		    cf_v2_daily_procedure_page_pc_uv.add(key)

                m1 = re.match('u=/zhongchou/payOutline\?tid=(\d+)', line)
                if m1:
                    ret['cf_v2_daily_payoutline_page_pv'] += 1
                    ret['cf_v2_daily_payoutline_page_pc_pv'] += 1
		    cf_v2_daily_payoutline_page_uv.add(key)
		    cf_v2_daily_payoutline_page_pc_uv.add(key)

        ret['cf_v2_daily_validated_home_page_uv'] = 0
        ret['cf_v2_daily_unvalidated_home_page_uv'] = 0
        ret['cf_v2_daily_validated_detail_page_uv'] = 0
        ret['cf_v2_daily_unvalidated_detail_page_uv'] = 0
        for i in cf_v2_daily_home_page_uv:
            if i in uids_validated:
        	ret['cf_v2_daily_validated_home_page_uv'] += 1
            else:
        	ret['cf_v2_daily_unvalidated_home_page_uv'] += 1
        for i in cf_v2_daily_detail_page_uv:
            if i in uids_validated:
        	ret['cf_v2_daily_validated_detail_page_uv'] += 1
            else:
        	ret['cf_v2_daily_unvalidated_detail_page_uv'] += 1

        ret["cf_v2_daily_home_page_uv"] = len(cf_v2_daily_home_page_uv)
        ret["cf_v2_daily_home_page_pc_uv"] = len(cf_v2_daily_home_page_pc_uv)
        ret["cf_v2_daily_home_page_h5_uv"] = len(cf_v2_daily_home_page_h5_uv)

        ret["cf_v2_daily_detail_page_uv"] = len(cf_v2_daily_detail_page_uv)
        ret["cf_v2_daily_detail_page_pc_uv"] = len(cf_v2_daily_detail_page_pc_uv)
        ret["cf_v2_daily_detail_page_h5_uv"] = len(cf_v2_daily_detail_page_h5_uv)

        ret["cf_v2_daily_validate_page_uv"] = len(cf_v2_daily_validate_page_uv)
        ret["cf_v2_daily_validate_page_pc_uv"] = len(cf_v2_daily_validate_page_pc_uv)
        ret["cf_v2_daily_validate_page_h5_uv"] = len(cf_v2_daily_validate_page_h5_uv)

        ret["cf_v2_daily_confirm_page_uv"] = len(cf_v2_daily_confirm_page_uv)
        ret["cf_v2_daily_confirm_page_pc_uv"] = len(cf_v2_daily_confirm_page_pc_uv)
        ret["cf_v2_daily_confirm_page_h5_uv"] = len(cf_v2_daily_confirm_page_h5_uv)

        ret["cf_v2_daily_order_page_uv"] = len(cf_v2_daily_order_page_uv)
        ret["cf_v2_daily_order_page_pc_uv"] = len(cf_v2_daily_order_page_pc_uv)
        ret["cf_v2_daily_order_page_h5_uv"] = len(cf_v2_daily_order_page_h5_uv)

        ret["cf_v2_daily_confirm_order_page_uv"] = len(cf_v2_daily_confirm_order_page_uv)
        ret["cf_v2_daily_confirm_order_page_pc_uv"] = len(cf_v2_daily_confirm_order_page_pc_uv)
        ret["cf_v2_daily_confirm_order_page_h5_uv"] = len(cf_v2_daily_confirm_order_page_h5_uv)

        ret["cf_v2_daily_pay_page_uv"] = len(cf_v2_daily_pay_page_uv)
        ret["cf_v2_daily_pay_page_pc_uv"] = len(cf_v2_daily_pay_page_pc_uv)
        ret["cf_v2_daily_pay_page_h5_uv"] = len(cf_v2_daily_pay_page_h5_uv)

        ret["cf_v2_daily_payway_page_uv"] = len(cf_v2_daily_payway_page_uv)
        ret["cf_v2_daily_payway_page_pc_uv"] = len(cf_v2_daily_payway_page_pc_uv)
        ret["cf_v2_daily_payway_page_h5_uv"] = len(cf_v2_daily_payway_page_h5_uv)

        ret["cf_v2_daily_confirmway_page_uv"] = len(cf_v2_daily_confirmway_page_uv)
        ret["cf_v2_daily_confirmway_page_pc_uv"] = len(cf_v2_daily_confirmway_page_pc_uv)
        ret["cf_v2_daily_confirmway_page_h5_uv"] = len(cf_v2_daily_confirmway_page_h5_uv)

        ret["cf_v2_daily_news_page_uv"] = len(cf_v2_daily_news_page_uv)
        ret["cf_v2_daily_news_page_pc_uv"] = len(cf_v2_daily_news_page_pc_uv)
        ret["cf_v2_daily_news_page_h5_uv"] = len(cf_v2_daily_news_page_h5_uv)

        ret["cf_v2_daily_news_detail_page_uv"] = len(cf_v2_daily_news_detail_page_uv)
        ret["cf_v2_daily_news_detail_page_pc_uv"] = len(cf_v2_daily_news_detail_page_pc_uv)
        ret["cf_v2_daily_news_detail_page_h5_uv"] = len(cf_v2_daily_news_detail_page_h5_uv)

        ret["cf_v2_daily_procedure_page_uv"] = len(cf_v2_daily_procedure_page_uv)
        ret["cf_v2_daily_procedure_page_pc_uv"] = len(cf_v2_daily_procedure_page_pc_uv)
        ret["cf_v2_daily_procedure_page_h5_uv"] = len(cf_v2_daily_procedure_page_h5_uv)

        ret["cf_v2_daily_payoutline_page_uv"] = len(cf_v2_daily_payoutline_page_uv)
        ret["cf_v2_daily_payoutline_page_pc_uv"] = len(cf_v2_daily_payoutline_page_pc_uv)
        ret["cf_v2_daily_payoutline_page_h5_uv"] = len(cf_v2_daily_payoutline_page_h5_uv)

        return ret

    def _get_yestoday_validated_uids(self):
        rows = self.get_sql_result("SELECT id from krplus2_%s.user where coinvestor_type='2' " %(self.report_yesday_date))
        uids = {}
        for row in rows:
            uids[str(row[0])]=1
        return uids

    def _get_validated_uids(self):
        rows = self.get_sql_result("SELECT id from user where coinvestor_type='2' ")
        uids = {}
        for row in rows:
            uids[str(row[0])]=1
        return uids

    def get_homepage_followpage_uv(self, ret):
        d_uid = {}
        for line in open(self.ng_daily_log_file):
            if 'hm.gif?u=' in line:
                line = line.strip('\n')
                uid_arr = line.split('"')[-1].strip().split(' ')
                uid = uid_arr[1] if len(uid_arr) >1 else '0'
                cookie_id = uid_arr[2] if len(uid_arr) >2 else '0'
                #key = uid if uid != '0' else cookie_id
                key =cookie_id

                url = line.split('u=')[1].split(' ')[0]
                dt = line.split('[')[1].split(' ')[0]
                try:
                    b=time_alia.strptime(dt, "%d/%b/%Y:%H:%M:%S")
                except:
                    continue
                ts = int(time_alia.mktime(b))

                if key in d_uid:
                    d_uid[key].append((ts, url))
                else:
                    d_uid[key] = [(ts, url)]

        for key in d_uid:
            d_uid[key].sort(key=lambda x:x[0])

        home_page = "%2Fzhongchou&h=rong.36kr.com"
        res = {}
        for key in d_uid:
            for i in range(len(d_uid[key])-1):
                url = d_uid[key][i][1]
                if url == home_page:
                    url_follow = d_uid[key][i+1][1]
                    if url_follow != home_page:
                        if url_follow in res:
                            res[url_follow] = res[url_follow] +1
                        else:
                            res[url_follow] = 1

        datas = res.items()
        datas.sort(key=lambda x:x[1], reverse=True)

        result = "\n".join([a[0]+"\t"+str(a[1]) for a in datas])
        ret["cf_daily_follow_page_info_list"] = result


    def get_coinvestor_validate_pv(self, ret):
        '''
        1 跟投人认证ua统计&ev=一句话简介&h=rongtest.36kr.com
        2 跟投人认证ua统计&ev=上传名片&h=rongtest.36kr.com
        3 跟投人认证ua统计&ev=个人单笔投资额�%B    A�&h=rongtest.36kr.com
        4 跟投人认证ua统计&ev=公司名&h=rongtest.36kr.com
        5 跟投人认证ua统计&ev=关注领域&h=rongtest.36kr.com
        6 跟投人认证ua统计&ev=所在地&h=rongtest.36kr.com
        7 跟投人认证ua统计&ev=投资者条件&h=rongtest.36kr.com
        8 跟投人认证ua统计&ev=投资阶段&h=rongtest.36kr.com
        9 跟投人认证ua统计&ev=真实姓名&h=rongtest.36kr.com
        14 跟投人认证ua统计&ev=身份证号码&h=rongtest.36kr.com
        10 跟投人认证ua统计&ev=确认身份证号码&h=rongtest.36kr.com
        11 跟投人认证ua统计&ev=职位&h=rongtest.36kr.com
        12 跟投人认证ua统计&ev=证件号码&h=rongtest.36kr.com
        13 跟投人认证ua统计&ev=证件类型&h=rongtest.36kr.com
        '''
        ret['cf_daily_coinvestor_validate_brief_pv'] = 0
        ret['cf_daily_coinvestor_validate_logo_pv'] = 0
        ret['cf_daily_coinvestor_validate_single_money_pv'] = 0
        ret['cf_daily_coinvestor_validate_company_pv'] = 0
        ret['cf_daily_coinvestor_validate_industry_pv'] = 0
        ret['cf_daily_coinvestor_validate_city_pv'] = 0
        ret['cf_daily_coinvestor_validate_invest_condition_pv'] = 0
        ret['cf_daily_coinvestor_validate_fund_phrase_pv'] = 0
        ret['cf_daily_coinvestor_validate_real_name_pv'] = 0
        ret['cf_daily_coinvestor_validate_id_number_pv'] = 0
        ret['cf_daily_coinvestor_validate_re_id_number_pv'] = 0
        ret['cf_daily_coinvestor_validate_postion_pv'] = 0
        ret['cf_daily_coinvestor_validate_certify_num_pv'] = 0
        ret['cf_daily_coinvestor_validate_certify_type_pv'] = 0
        for line in open(self.ng_daily_log_file):
            if '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E4%B8%80%E5%8F%A5%E8%AF%9D%E7%AE%80%E4%BB%8B' in line:
                ret['cf_daily_coinvestor_validate_brief_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E4%B8%8A%E4%BC%A0%E5%90%8D%E7%89%87' in line:
                ret['cf_daily_coinvestor_validate_logo_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E4%B8%AA%E4%BA%BA%E5%8D%95%E7%AC%94%E6%8A%95%E8%B5%84%E9%A2%9D%E5%BA%A6' in line:
                ret['cf_daily_coinvestor_validate_single_money_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E5%85%AC%E5%8F%B8%E5%90%8D' in line:
                ret['cf_daily_coinvestor_validate_company_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E5%85%B3%E6%B3%A8%E9%A2%86%E5%9F%9F' in line:
                ret['cf_daily_coinvestor_validate_industry_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E6%89%80%E5%9C%A8%E5%9C%B0' in line:
                ret['cf_daily_coinvestor_validate_city_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E6%8A%95%E8%B5%84%E8%80%85%E6%9D%A1%E4%BB%B6' in line:
                ret['cf_daily_coinvestor_validate_invest_condition_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E6%8A%95%E8%B5%84%E9%98%B6%E6%AE%B5' in line:
                ret['cf_daily_coinvestor_validate_fund_phrase_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E7%9C%9F%E5%AE%9E%E5%A7%93%E5%90%8D' in line:
                ret['cf_daily_coinvestor_validate_real_name_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E8%BA%AB%E4%BB%BD%E8%AF%81%E5%8F%B7%E7%A0%81' in line:
                ret['cf_daily_coinvestor_validate_id_number_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E7%A1%AE%E8%AE%A4%E8%BA%AB%E4%BB%BD%E8%AF%81%E5%8F%B7%E7%A0%81' in line:
                ret['cf_daily_coinvestor_validate_re_id_number_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E8%81%8C%E4%BD%8D' in line:
                ret['cf_daily_coinvestor_validate_postion_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E8%AF%81%E4%BB%B6%E5%8F%B7%E7%A0%81' in line:
                ret['cf_daily_coinvestor_validate_certify_num_pv'] += 1
            elif '%E8%B7%9F%E6%8A%95%E4%BA%BA%E8%AE%A4%E8%AF%81ua%E7%BB%9F%E8%AE%A1&ev=%E8%AF%81%E4%BB%B6%E7%B1%BB%E5%9E%8B' in line:
                ret['cf_daily_coinvestor_validate_certify_type_pv'] += 1

    def get_weixin_public_uv(self, ret):
        cf_daily_wxpub_wx36kr_zhongchou = set()
        cf_daily_wxpub_wx36kr_company_create = set()
        cf_daily_wxpub_wx36kr_investor_apply = set()
        cf_daily_wxpub_wx36kr_krspace = set()
        cf_daily_wxpub_wx36kr_report = set()

        cf_daily_wxpub_wx36kr_rongzi_zhongchou = set()
        cf_daily_wxpub_wx36kr_rongzi_company_create = set()
        cf_daily_wxpub_wx36kr_rongzi_investor_apply = set()

        cf_daily_wxpub_wx36kr_service_zhongchou = set()
        cf_daily_wxpub_wx36kr_service_company_create = set()
        cf_daily_wxpub_wx36kr_service_investor_apply = set()
        cf_daily_wxpub_wx36kr_service_krspace = set()
        cf_daily_wxpub_wx36kr_service_report = set()

        cf_daily_wxpub_wxgzhcd_view = set()
        cf_daily_wxpub_wxgzhcd_apply = set()
        cf_daily_wxpub_wxgzhcd_help = set()

        ## add
        rows = self.get_sql_result("SELECT id from krplus2_%s.user where coinvestor_type='2' " %(self.report_date))
        coinvestor_uids = {}
        for row in rows:
            coinvestor_uids[str(row[0])]=1
        cf_daily_com_detail_coinvestor_list = {}

        for line in open(self.ng_daily_log_file):
            line = line.strip('\n')
            uid_arr = line.split('"')[-1].strip().split(' ')
            uid = uid_arr[1] if len(uid_arr) >1 else '0'
            cookie_id = uid_arr[2] if len(uid_arr) >2 else '0'
            key = uid if uid != '0' else cookie_id

            line = urllib.unquote(line)

            ## add https://rong.36kr.com/#/company/29878/crowFunding?fundingId=110&h=rong.36kr.com stat
            if uid in coinvestor_uids and 'rong.36kr.com' in line:
                cid = ''
                m1 = re.search('u=/company/(\d+)/crowFunding', line)
                if m1:
                    cid = m1.group(1)
                else:
                    m2 = re.search('zhongchouDetail?companyId=(\d+)&fundingId', line)
                    if m2:
                        cid = m2.group(1)
                if cid:
                    if cid in cf_daily_com_detail_coinvestor_list:
                        cf_daily_com_detail_coinvestor_list[cid].add(uid)
                    else:
                        cf_daily_com_detail_coinvestor_list[cid] = set()
                        cf_daily_com_detail_coinvestor_list[cid].add(uid)

            ## weixin project
            if 'https://rong.36kr.com/m/?ref=wx36kr' in line:
                if 'u=/zhongchou' in line:
                    cf_daily_wxpub_wx36kr_zhongchou.add(key)
                elif 'u=/company_create' in line:
                    cf_daily_wxpub_wx36kr_company_create.add(key)
                elif 'u=/investor/apply' in line:
                    cf_daily_wxpub_wx36kr_investor_apply.add(key)

            if 'http://space.36kr.com/krspace-h5.html?ref=wx36kr' in line:
                cf_daily_wxpub_wx36kr_krspace.add(key)

            if 'http://chuang.36kr.com/report?ref=wx36kr' in line:
                if 'u=/report/index' in line:
                    cf_daily_wxpub_wx36kr_report.add(key)

            if 'https://rong.36kr.com/m/?ref=wx36kr_rongzi' in line:
                if 'u=/zhongchou' in line:
                    cf_daily_wxpub_wx36kr_rongzi_zhongchou.add(key)
                elif 'u=/company_create' in line:
                    cf_daily_wxpub_wx36kr_rongzi_company_create.add(key)
                elif 'u=/investor/apply' in line:
                    cf_daily_wxpub_wx36kr_rongzi_investor_apply.add(key)

            if 'https://rong.36kr.com/m/?ref=wx36kr_service' in line:
                if 'u=/zhongchou' in line:
                    cf_daily_wxpub_wx36kr_service_zhongchou.add(key)
                elif 'u=/company_create' in line:
                    cf_daily_wxpub_wx36kr_service_company_create.add(key)
                elif 'u=/investor/apply' in line:
                    cf_daily_wxpub_wx36kr_service_investor_apply.add(key)

            if 'http://space.36kr.com/krspace-h5.html?ref=wx36kr_service' in line:
                cf_daily_wxpub_wx36kr_service_krspace.add(key)
            if 'http://chuang.36kr.com/report?ref=wx36kr_service' in line:
                if 'u=/report/index' in line:
                    cf_daily_wxpub_wx36kr_service_report.add(key)

            if 'http://z.36kr.com/#/?op=wxgzhcd' in line:
                cf_daily_wxpub_wxgzhcd_view.add(key)
            if 'http://rong.36kr.com/#/investorValidate?op=wxgzhcd' in line:
                cf_daily_wxpub_wxgzhcd_apply.add(key)
            if 'http://help.36kr.com/q-m-zc.html?op=wxgzhcd' in line:
                cf_daily_wxpub_wxgzhcd_help.add(key)

        ret['cf_daily_wxpub_wx36kr_zhongchou_uv'] = len(cf_daily_wxpub_wx36kr_zhongchou)
        ret['cf_daily_wxpub_wx36kr_company_create_uv'] = len(cf_daily_wxpub_wx36kr_company_create)
        ret['cf_daily_wxpub_wx36kr_investor_apply_uv'] = len(cf_daily_wxpub_wx36kr_investor_apply)
        ret['cf_daily_wxpub_wx36kr_krspace_uv'] = len(cf_daily_wxpub_wx36kr_krspace)
        ret['cf_daily_wxpub_wx36kr_report_uv'] = len(cf_daily_wxpub_wx36kr_report)

        ret['cf_daily_wxpub_wx36kr_rongzi_zhongchou_uv'] = len(cf_daily_wxpub_wx36kr_rongzi_zhongchou)
        ret['cf_daily_wxpub_wx36kr_rongzi_company_create_uv'] = len(cf_daily_wxpub_wx36kr_rongzi_company_create)
        ret['cf_daily_wxpub_wx36kr_rongzi_investor_apply_uv'] = len(cf_daily_wxpub_wx36kr_rongzi_investor_apply)

        ret['cf_daily_wxpub_wx36kr_service_zhongchou_uv'] = len(cf_daily_wxpub_wx36kr_service_zhongchou)
        ret['cf_daily_wxpub_wx36kr_service_company_create_uv'] = len(cf_daily_wxpub_wx36kr_service_company_create)
        ret['cf_daily_wxpub_wx36kr_service_investor_apply_uv'] = len(cf_daily_wxpub_wx36kr_service_investor_apply)
        ret['cf_daily_wxpub_wx36kr_service_krspace_uv'] = len(cf_daily_wxpub_wx36kr_service_krspace)
        ret['cf_daily_wxpub_wx36kr_service_report_uv'] = len(cf_daily_wxpub_wx36kr_service_report)

        ret['cf_daily_wxpub_wxgzhcd_view_uv'] = len(cf_daily_wxpub_wxgzhcd_view)
        ret['cf_daily_wxpub_wxgzhcd_apply_uv'] = len(cf_daily_wxpub_wxgzhcd_apply)
        ret['cf_daily_wxpub_wxgzhcd_help_uv'] = len(cf_daily_wxpub_wxgzhcd_help)

        cf_daily_com_detail_coinvestor_uv = []
        for fcid in cf_daily_com_detail_coinvestor_list:
            rows = self.get_sql_result("SELECT name from krplus2_%s.company where id=%s" %(self.report_date,fcid))
            if rows:
                name = rows[0][0]
                coinvestor_uv = len(cf_daily_com_detail_coinvestor_list[fcid])
                cf_daily_com_detail_coinvestor_uv.append(name+"\t"+str(coinvestor_uv))
        ret['cf_daily_com_detail_coinvestor_uv_list'] = '\n'.join(cf_daily_com_detail_coinvestor_uv)


    def get_all_statistics_info(self):
        ret = {}
        self.get_cf_project_stat_info(ret)
        self.get_cf_pre_project_detail_info(ret)
        self.get_cf_project_detail_info(ret)
        self.get_daily_crowd_funding_info(ret)
        self.get_monthly_crowd_funding_info(ret)
        self.get_homepage_followpage_uv(ret)
        self.get_coinvestor_validate_pv(ret)
        self.get_weixin_public_uv(ret)
        self.get_daily_crowd_funding_info_v2(ret)
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
