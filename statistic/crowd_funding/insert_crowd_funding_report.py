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

def process(conn, report_date, data_file):
    cursor = conn.cursor()
    cursor.execute ("set names utf8")

    # process every line dbjson
    j = json.loads(open(data_file).read())
    title = ','.join(j.keys())
    val = ''
    for k in j.keys():
        if type(j[k]) is types.IntType or type(j[k]) is types.FloatType:
            val += str(j[k]) + ','
        else:
            val += "'" + j[k].encode('utf8').replace("'","\\'") + "',"
    val = val.strip(',')
    sql_cmd = "REPLACE INTO crowd_funding_report (%s,stat_date) VALUES (%s,'%s')" %(title, val, report_date)

    #print sql_cmd.encode('utf8')
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
    python ./prog [2015-06-23]
    '''
    sys.exit(main())

