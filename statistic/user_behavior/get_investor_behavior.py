#!/usr/bin/env python
#coding=utf8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import MySQLdb
from ConfigParser import SafeConfigParser

class DataFetcher:
    def __init__(self, config_file):
        self.config = SafeConfigParser()
        self.config.read(config_file)

        self.db = None
        self.db_cursor = None
        self.reset_db_connection('mysql_readall')

        self.db_insight = None
        self.db_cursor_insight = None
        self.reset_db_connection('mysql_stat')

    def reset_db_connection(self, db_type):
        if db_type == "mysql_readall":
            if self.db: self.db.close()
            self.db = MySQLdb.connect(host= self.config.get(db_type, 'host'),
                                      user= self.config.get(db_type, 'user'),
                                      passwd= self.config.get(db_type, 'passwd'),
                                      db= self.config.get(db_type, 'db'))
            self.db.set_character_set('utf8')
            self.db_cursor = self.db.cursor()
        elif db_type == "mysql_stat":
            if self.db_insight: self.db_insight.close()
            self.db_insight = MySQLdb.connect(host= self.config.get(db_type, 'host'),
                                              user= self.config.get(db_type, 'user'),
                                              passwd= self.config.get(db_type, 'passwd'),
                                              db= self.config.get(db_type, 'db'))
            self.db_insight.set_character_set('utf8')
            self.db_cursor_insight = self.db_insight.cursor()
        else:
            raise Exception("Unknown db_type: %s" % db_type)

    def get_sql_result(self, sql_cmd, db_type):
        db_cur = self.db_cursor if db_type == "mysql_readall" else self.db_cursor_insight
        db_data = ''
        retry_count = 0
        while retry_count < 3:
            try:
                db_cur.execute(sql_cmd)
                db_data = db_cur.fetchall()
                break
            except:
                self.reset_db_connection(db_type)
                db_cur = self.db_cursor if db_type == "mysql_readall" else self.db_cursor_insight
            retry_count += 1
        return db_data

    def commit_sql_cmd(self, sql_cmd, db_type="mysql_stat"):
        db_cur = self.db_cursor_insight
        db = self.db_insight
        retry_count = 0
        while retry_count < 3:
            try:
                db_cur.execute(sql_cmd)
                db.commit()
                return 0
            except:
                self.reset_db_connection(db_type)
                db_cur = self.db_cursor_insight
                db = self.db_insight
            retry_count += 1
        return -1

if __name__ == '__main__':
    fetcher = DataFetcher('mysql_account.conf')
    db_data = fetcher.get_sql_result("select id,name,cteate_time,update_time from user WHERE investor_type in (10,20)","mysql_readall")
    for row in db_data:
        investor_id = row[0]
        investor_name = row[1]
        cteate_time = row[2]
        update_time = row[3]
        tmp_data = fetcher.get_sql_result("select count(uid) from user_login where uid=%d" %investor_id, "mysql_stat")
        login_times = tmp_data[0][0]
        tmp_data = fetcher.get_sql_result("select stat_date from user_login where uid=%d order by stat_date desc limit 1" %investor_id, "mysql_stat")
        login_date = tmp_data[0][0] if tmp_data else '-'
        print "%d\t%s\t%d\t%s\t%s" %(investor_id, investor_name, login_times,cteate_time,login_date)

