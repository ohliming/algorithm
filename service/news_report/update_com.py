#!/usr/bin/env python
# -*- coding: utf8 -*-

import os,json,datetime,re,time
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
from company_recognize.report_to_company import ComLib
from common.db_fetcher import DataBaseFetcher

db_fetcher = DataBaseFetcher()
cur_abs_path = os.path.dirname(os.path.abspath(__file__))
path_segment = '../../company_recognize/segment/data'
file_com_name2id = '../../company_recognize/com_name2id.txt' 
file_filter_words = '../../company_recognize/com_filter.txt'

comlib = ComLib(path_segment, file_com_name2id, None, file_filter_words)

def get_event_type(title):
    etype = 0
    rongzi_list = ['融资','投资','美元','人民币','种子轮','天使轮','PreA','A轮','B轮','C轮','D轮','E轮','IPO','上市','私有化','收购','并购','合并','倒闭']
    new_list = ['发布','推出','研发','启动','新品','新产品','版本','业务','进军','入股','战略','上线']
    biandong_list = ['加入','任命','离职','组织架构','组织结构','事业部','事业群','CEO','COO','CMO','CFO','CIO']
    if title:
        title = unicode(title)
        if etype==0:
            for key in rongzi_list:
                if unicode(key) in title:
                    etype = 1
        if etype==0:
            for key in new_list:
                if unicode(key) in title:
                    etype = 2
        if etype==0:
            for key in biandong_list:
                if unicode(key) in title:
                    etype = 3
    return etype

if __name__=="__main__":
    # update news_report company
    now_time = datetime.datetime.now()
    yes_time = now_time + datetime.timedelta(days=-1)
    yes_date = yes_time.strftime('%Y-%m-%d')
    condition_sql = "publish_date >= \'%s 00:00:00\' and publish_date <= '%s 23:59:59' and type = 0" % (yes_date, yes_date)
    db_data = db_fetcher.get_sql_result('select id, title, content from news_report where %s' % condition_sql, 'mysql_insight')
    for pos in range(len(db_data)):
        kid, title, content = str(db_data[pos][0]), str(db_data[pos][1]), str(db_data[pos][2])
        try:
            topic_coms = comlib.extract_report(title, content.encode('utf8', 'ignore'), '-1')
            reported_coms = ",".join([x[0] for x in topic_coms])
            com_id, is_confident = comlib.extract_report(title, content.encode('utf8', 'ignore'))
            reported_com = 0
            if com_id and com_id!="0" and is_confident:
                reported_com = int(com_id)
            event_type = get_event_type(title)
            update_sql = "update news_report set reported_com= %s, reported_coms = \'%s\',event_type = %s  where id = %s" % (reported_com, reported_coms, event_type, kid)
            db_fetcher.commit_sql_cmd(update_sql, "mysql_insight")
        except:
            print 'happend error title:%s' % title
