#!/usr/bin/env python
#coding=utf8
import os,sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os.path
import MySQLdb
from ConfigParser import SafeConfigParser

class DataBaseFetcher:
    def __init__(self, config_file=None):
        self.config = SafeConfigParser()
        self.config_file = ''
        self._set_default_config_file(config_file)
        self.config.read(self.config_file)
        if not self.config.sections():
            raise Exception("[Empty account]: %s!" %(self.config_file))
        self.db_dict = {}
        for db_type in self.config.sections():
            self.db_dict[db_type] = None

    def _set_default_config_file(self, config_file):
        if config_file:
            self.config_file = config_file
            return
        ## find default conf
        cur_path = os.getcwd()
        path_arr = cur_path.split('/')
        is_found = False
        for i in range(len(path_arr)-1,0,-1):
            common_path = '/'.join(path_arr[:i+1])
            file_path = common_path + "/common/mysql_account.ini"
            if os.path.exists(file_path):
                self.config_file = file_path
                return
        raise Exception("[Not Found]: Project/common/mysql_account.ini!")

    def _reset_db_connection(self, db_type):
        if not db_type in self.db_dict:
            raise Exception("Unknown db_type: %s" % db_type)

        if self.db_dict[db_type]: self.db_dict[db_type].close()
        self.db_dict[db_type] = MySQLdb.connect(
                                      host= self.config.get(db_type, 'host'),
                                      user= self.config.get(db_type, 'user'),
                                      passwd= self.config.get(db_type, 'passwd'),
                                      db= self.config.get(db_type, 'db'))
        self.db_dict[db_type].autocommit(True)
        self.db_dict[db_type].set_character_set('utf8')

    def get_sql_result(self, sql_cmd, db_type, ret_dict=False):
        if not db_type in self.db_dict:
            raise Exception("Unknown db_type: %s" % db_type)
        if self.db_dict[db_type] is None:
            self._reset_db_connection(db_type)
        db_cur = self.db_dict[db_type].cursor() if not ret_dict else self.db_dict[db_type].cursor(cursorclass=MySQLdb.cursors.DictCursor)
        db_data = ''
        retry_count = 0
        while retry_count < 3:
            try:
                #print sql_cmd
                db_cur.execute(sql_cmd)
                db_data = db_cur.fetchall()
                break
            except:
                self._reset_db_connection(db_type)
                db_cur = self.db_dict[db_type].cursor() if not ret_dict else self.db_dict[db_type].cursor(cursorclass=MySQLdb.cursors.DictCursor)
            retry_count += 1
        return db_data

    def gen_insert_sql_clause(self, table, dict_d):
        col_list = []
        params = []
        for k in dict_d:
            if dict_d[k] is not None:
                col_list.append("`"+k+"`")
                params.append(dict_d[k])
        cols = ",".join(col_list)
        vals = ",".join(["%s"]*len(col_list))
        sql = "insert into %s (%s) values (%s)" % (table, cols, vals)
        return (sql,params)

    def gen_update_sql_clause(self, table, dict_d, where_case):
        col_list = []
        params = []
        for k in dict_d:
            if dict_d[k] is not None:
                col_list.append("`"+k+"`=%s")
                params.append(dict_d[k])
        cols = ",".join(col_list)
        sql = "update %s set %s where %s" % (table, cols, where_case)
        return (sql,params)

    def commit_sql_cmd(self, sql_cmd, db_type, params=None):
        if not db_type in self.db_dict:
            raise Exception("Unknown db_type: %s" % db_type)
        if self.db_dict[db_type] is None:
            self._reset_db_connection(db_type)
        db = self.db_dict[db_type]
        db_cur = db.cursor()
        retry_count = 0
        while retry_count < 3:
            try:
                db_cur.execute(sql_cmd,params)
                insert_id = db.insert_id()
                db.commit()
                return insert_id
            except:
                self._reset_db_connection(db_type)
                db = self.db_dict[db_type]
                db_cur = db.cursor()
            retry_count += 1
        return -1

if __name__ == '__main__':
    fetcher = DataBaseFetcher('mysql_account.ini')
    ## test
    db_data = fetcher.get_sql_result("select id,name from krplus2.company where id=1515","mysql_readall")
    print "mysql_readall: " + db_data[0][1]
    db_data = fetcher.get_sql_result("select id,name from company_trend where id=1515","mysql_insight")
    print "mysql_insight: " + db_data[0][1]
