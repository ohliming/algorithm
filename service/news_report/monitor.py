#!/usr/bin/env python
# -*- coding: utf8 -*-

import os,json,datetime,re,time
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
from common.db_fetcher import DataBaseFetcher

db_fetcher = DataBaseFetcher()

def get_domain_list(url_file = 'urls.txt'):
    domain_list = []
    with open(url_file) as url_f:
        for line in url_f:
            url = line.strip()
            if 'https' in url:
                start_pos = 8
            else:
                start_pos = 7

            str_url = url[start_pos:]
            end_pos = str_url.find('/')
            if end_pos  == -1: end_pos = len(str_url)
            domain = str_url[:end_pos]
            domain_list.append(domain)

    return domain_list

def create_html_table(datas, title=None):
    info = '<table class="table"  border="1" cellpadding="6" style="text-align:left;margin:15px 0; border-collapse: collapse;border-color: #ddd;border: 1px solid #ddd;width: 100%;">'
    info += "<tr style='background-color:#BBB;'>"
    info += "<th>%s</th>" % title
    info += "</tr>"
    for data in datas:
        if type(data)==list:
            info += "<tr>"
            for k in data:
                info += "<td>%s</td>" % str(k)
            info += "</tr>"
        else:
            info += "<tr style='background-color:#EEE;'><td colspan='%d'><b>%s</b></td></tr>" % (len(title), str(data))
    info += "</table>"
    return info

if __name__=="__main__":
    domain_list = get_domain_list()
    now_time = datetime.datetime.now()
    pre_time = now_time + datetime.timedelta(days=-3)
    pre_date = pre_time.strftime('%Y-%m-%d')

    title = '异常抓取站点'
    data_list = []
    for domain in domain_list:
        sel_sql = "select count(*) from news_report where publish_date >= \'%s 00:00:00\' and domain = \'%s\' and type = 0 limit 1" % (pre_date, domain)
        db_data = db_fetcher.get_sql_result(sel_sql, 'mysql_insight')
        domain_count = int(db_data[0][0])

        if domain_count == 0:
            data_list.append(domain)
    data_list = list(set(data_list))
    info = create_html_table(data_list, title)
    print info
