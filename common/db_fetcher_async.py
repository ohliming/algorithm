#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys 
reload(sys)
sys.setdefaultencoding('utf-8')
import os, traceback
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../')))
from ConfigParser import SafeConfigParser
import tornado.gen
import tormysql

class DataBaseFetcherAsync():
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
        #针对每个db_type,创建一个连接池，连接池最大数目由max_connections指定，连接按需建立，长时间闲置则会自动断开（由idle_seconds指定）
        self.db_dict[db_type] = tormysql.ConnectionPool(
            max_connections = 100, #max open connections
            idle_seconds = 720, #conntion idle timeout time, 0 is not timeout
            wait_connection_timeout = 10, #wait connection timeout
            host = self.config.get(db_type, 'host'),
            user = self.config.get(db_type, 'user'),
            passwd = self.config.get(db_type, 'passwd'),
            db = self.config.get(db_type, 'db'),
            charset = "utf8"
            )
        
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

    @tornado.gen.coroutine
    def get_sql_result(self, sql_cmd, db_type, ret_dict=False):
        if not db_type in self.db_dict:
            raise Exception("Unknown db_type: %s" % db_type)
        if self.db_dict[db_type] is None:
            self._reset_db_connection(db_type)
        with (yield self.db_dict[db_type].Connection()) as conn:
            cursor = conn.cursor() if not ret_dict else conn.cursor(tormysql.DictCursor)
            yield cursor.execute(sql_cmd)
            datas = cursor.fetchall()
            yield conn.commit()
        raise tornado.gen.Return(datas)

    @tornado.gen.coroutine
    def commit_sql_cmd(self, sql_cmd, db_type, params=None):
        if not db_type in self.db_dict:
            raise Exception("Unknown db_type: %s" % db_type)
        if self.db_dict[db_type] is None:
            self._reset_db_connection(db_type)
        insert_id = -1 
        retry_count = 0
        while retry_count < 3:
            with (yield self.db_dict[db_type].Connection()) as conn:
                try:
                    with conn.cursor() as cursor:
                        yield cursor.execute(sql_cmd, params)
                        insert_id = conn.insert_id()
                except:
                    yield conn.rollback()
                else:
                    yield conn.commit()
                    break
            retry_count += 1
        raise tornado.gen.Return(insert_id)
            
    @tornado.gen.coroutine
    def test(self):
        with (yield self.pool2.Connection()) as conn:
            with conn.cursor() as cursor:
                yield cursor.execute('select * from company limit 100,1')
                datas = cursor.fetchall()
        raise tornado.gen.Return(datas)
