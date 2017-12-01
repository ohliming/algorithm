#!/usr/bin/env python
# -*- coding: utf8 -*-

import MySQLdb

class DbCrud():
    def __init__(self, host, user, pwd, db):
        self.host = host
        self.user = user
        self.passwd = pwd
        self.db = db
        self.conn = None

    def __get_conn(self):
        if not self.conn:
            self.conn = self.__getconnection()
            return self.conn
        try:
            self.conn.ping(True)
        except:
            self.conn = self.__getconnection()
        return self.conn

    def __getconnection(self, db=None):
        conn = MySQLdb.Connection(host=self.host, user=self.user, passwd=self.passwd, db=self.db, charset="utf8")
        if db:
            conn.select_db(db)
        return conn

    # 查
    def select(self, sql, params=None, db=None):
        # conn = self.__getconnection(db)
        conn = self.__get_conn()
        cur = conn.cursor()
        cur.execute(sql, params)
        results = cur.fetchall()
        conn.commit()
        # conn.close() 
        return results

    def select_dict(self, sql, params=None, db=None):
        conn = self.__get_conn()
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(sql, params)
        results = cur.fetchallDict()
        return results

    # 增删改
    def execute(self, sql, params=None, db=None):
        # conn = self.__getconnection(db)
        conn = self.__get_conn()
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        # conn.close()

    # 自增，返回id
    def insert(self, sql, params=None, db=None):
        # conn = self.__getconnection(db)
        conn = self.__get_conn()
        cur = conn.cursor()
        cur.execute(sql, params)
        id = conn.insert_id()
        conn.commit()
        # conn.close()
        return id

    def insert_many(self, sql, params=None, db=None):
        # conn = self.__getconnection(db)
        conn = self.__get_conn()
        cur = conn.cursor()
        cur.executemany(sql, params)
        #id = conn.insert_id()
        #id2 = cur.lastrowid
        #print "lastrowid:", type(id2), id2
        conn.commit()
        # conn.close()
        #return id
    
    def close(self):
        if self.conn:
            self.conn.close()

    # 取数据字段及数据集，方便插入或更新操作；输入dict的key值需与数据库字段对应，date类型数据转成str
    def get_column_and_param(self, dict_d):
        col_list = []
        params = []
        for k in dict_d:
            if dict_d[k] is not None:
                col_list.append("`"+k+"`")
                params.append(dict_d[k])    
        cols = ",".join(col_list)
        vals = ",".join(["%s"]*len(col_list))
        return (cols,vals, params)
    
    def insert_data(self, table, dict_d):
        (cols, vals, params) = self.get_column_and_param(dict_d)
        sql = "insert into %s (%s) values (%s)" % (table, cols, vals)
        return self.insert(sql, params)

    def update_data(self, table, dict_d, where_case):
        col_list = []
        params = []
        for k in dict_d:
            if dict_d[k] is not None:
                col_list.append("`"+k+"`=%s")
                params.append(dict_d[k])
        cols = ",".join(col_list)
        sql = "update %s set %s where %s" % (table, cols, where_case)
        self.execute(sql, params)

    # datas里的多个数据，字段要一致，没有的补None
    def bulk_insert(self, table, datas):
        if datas:
            key_list = datas[0].keys()
            params = []
            for data in datas:
                param = []
                for key in key_list:
                    param.append(data[key])
                params.append(param)
            cols = "`"+"`,`".join(key_list)+"`"
            vals1 = "("+",".join(["%s"]*len(key_list))+")"
            #vals = ",".join([vals1]*len(datas))
            sql = "insert into %s (%s) values %s" % (table, cols, vals1)
            self.insert_many(sql, params)

if __name__ == '__main__':
    db = DbCrud("dev04", "operator", "cdlLT4PzryUgpZjTh3yx", "crm")            
    sql2 = "create table mytest2 (aid int AUTO_INCREMENT, id int, name varchar(20), PRIMARY KEY (`aid`)) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8"
    #db.execute(sql2)

    datas = [{"id":1,"name":"qq"},{"id":2,"name":"ww"}]
    res =  db.bulk_insert("mytest2", datas)
    #print type(res), res    

    sql3 = "drop table mytest2"
   # db.execute(sql3)    
    db.close()
    


    
