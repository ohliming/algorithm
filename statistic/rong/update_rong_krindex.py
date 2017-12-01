#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Date    :  2015-02-04 15:09:31

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import MySQLdb
import json
import types

# connect to the MySQL server
def connect_mysql():
    conn = None
    try:
        conn = MySQLdb.connect(host = "rds60i0820sk46jfsiv0.mysql.rds.aliyuncs.com",
                user = "stat",
                passwd = "JTRQ6pNlnqdBV3ox",
                port= 3306,
                db = "stat")
        return conn
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
    return None

def extract(data_file):
    ret = {}
    for line in open(data_file):
        arr = line.strip('\n').split('\t')
        if arr[0] == '总公司数:':
            ret['kr_index_com_total_num'] = int(arr[1])
        elif arr[0] == '总Website数:':
            ret['kr_index_com_website_num'] = int(arr[1].split(' ')[0])
            ratio = arr[1].split('(')[1].split('%')[0]
            ret['kr_index_com_website_ratio'] = float(ratio) / 100
        elif arr[0] == 'Top列表可见Website数:':
            ret['kr_index_com_website_top_num'] = int(arr[1].split(' ')[0])
            ratio = arr[1].split('(')[1].split('%')[0]
            ret['kr_index_com_website_top_ratio'] = float(ratio) / 100
        elif arr[0] == '总App数:':
            ret['kr_index_com_app_num'] = int(arr[1].split(' ')[0])
            ratio = arr[1].split('(')[1].split('%')[0]
            ret['kr_index_com_app_ratio'] = float(ratio) / 100
        elif arr[0] == 'Top列表可见App数:':
            ret['kr_index_com_app_top_num'] = int(arr[1].split(' ')[0])
            ratio = arr[1].split('(')[1].split('%')[0]
            ret['kr_index_com_app_top_ratio'] = float(ratio) / 100
        elif arr[0] == '氪指数可见打分数:':
            ret['kr_index_com_presentable_num'] = int(arr[1].split(' ')[0])
            ratio = arr[1].split('(')[1].split('%')[0]
            ret['kr_index_com_presentable_ratio'] = float(ratio) / 100
        elif arr[0] == '公司标签覆盖率:':
            ret['kr_index_com_tag_num'] = int(arr[1].split(' ')[0])
            ratio = arr[1].split('(')[1].split('%')[0]
            ret['kr_index_com_tag_ratio'] = float(ratio) / 100
        elif arr[0] == '公司平均标签数:':
            ret['kr_index_com_tag_avg_num'] = float(arr[1].split(' ')[0])
        elif arr[0] == '公司行业覆盖率:':
            ret['kr_index_com_industry_num'] = int(arr[1].split(' ')[0])
            ratio = arr[1].split('(')[1].split('%')[0]
            ret['kr_index_com_industry_ratio'] = float(ratio) / 100
        elif arr[0] == '公司融资轮次覆盖率:':
            ret['kr_index_com_fund_num'] = int(arr[1].split(' ')[0])
            ratio = arr[1].split('(')[1].split('%')[0]
            ret['kr_index_com_fund_ratio'] = float(ratio) / 100
    return ret

def process(conn, report_date, data_file):
    cursor = conn.cursor()
    cursor.execute ("set names utf8")

    # process every line dbjson
    j = extract(data_file)
    title = ','.join(j.keys())
    val = ''
    for k in j.keys():
        if type(j[k]) is types.IntType or type(j[k]) is types.FloatType:
            val += k + '=' + str(j[k]) + ','
        else:
            val += k + '=' +"'" + j[k].encode('utf8').replace("'","\\'") + "',"
    val = val.strip(',')
    sql_cmd = "UPDATE rong_report SET %s where stat_date='%s'" %(val, report_date)

    print sql_cmd.encode('utf8')
    #return 0

    try:
        cursor.execute ("set names utf8")
        cursor.execute(sql_cmd.encode('utf8'))
        conn.commit ()
        print "Number of rows inserted: %d" % cursor.rowcount
    except Exception,e:
        print "Error info: %s" % e
    conn.close ()
    #sys.exit (0)

def main():
    conn = connect_mysql()
    report_date = sys.argv[1]
    stat_file = sys.argv[2]
    process(conn, report_date, stat_file)

if __name__ == "__main__":
    '''
    python ./prog [2015-6-23]
    '''
    sys.exit(main())

