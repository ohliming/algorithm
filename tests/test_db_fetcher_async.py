#!/usr/bin/env python
# encoding: utf-8
import sys,os
reload(sys)
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../')))
from tornado.testing import gen_test
from common.db_fetcher_async import DataBaseFetcherAsync
from tornado.testing import AsyncTestCase


class TestDBFetcherAsync(AsyncTestCase):
    def setUp(self):
        super(TestDBFetcherAsync, self).setUp()
        self.fetcher_async = DataBaseFetcherAsync()

    def tearDown(self):
        super(TestDBFetcherAsync, self).tearDown()

    @gen_test
    def test_get_sql_result(self):
        sql_cmd = 'select * from crm.company limit 10'
        rows = yield self.fetcher_async.get_sql_result(sql_cmd, "mysql_readall")
        self.assertTrue(isinstance(rows, (tuple)), 'select result type error')
        self.assertEqual(len(rows), 10, 'select data error')

        rows = yield self.fetcher_async.get_sql_result(sql_cmd, "mysql_readall", True)
        self.assertTrue(isinstance(rows, (list)), 'select result type error')
        self.assertEqual(len(rows), 10, 'select data error')

    @gen_test
    def test_commit_sql_cmd(self):
        sql_cmd = 'drop table if exists test_regression'
        ret = yield self.fetcher_async.commit_sql_cmd(sql_cmd, "mysql_insight")
        self.assertEqual(ret, 0, 'drop table error')

        sql_cmd = '''
            create table test_regression(
                `id` int(11) NOT NULL PRIMARY KEY AUTO_INCREMENT, 
                `content` varchar(255)
                )ENGINE=InnoDB AUTO_INCREMENT=100 DEFAULT CHARSET=utf8;
            '''
        ret = yield self.fetcher_async.commit_sql_cmd(sql_cmd, "mysql_insight")
        self.assertEqual(ret, 0, 'create table error')

        sql_cmd = 'insert into test_regression (id, content) values (10000, \"this is a test\")'
        ret = yield self.fetcher_async.commit_sql_cmd(sql_cmd, "mysql_insight")
        self.assertEqual(ret, 10000, 'insert error')

        sql_cmd = 'update test_regression set content = \"update test\" where id = 10000'
        ret = yield self.fetcher_async.commit_sql_cmd(sql_cmd, "mysql_insight")
        self.assertEqual(ret, 0, 'update error')

        sql_cmd = 'delete from test_regression where id = 10000'
        ret = yield self.fetcher_async.commit_sql_cmd(sql_cmd, "mysql_insight")
        self.assertEqual(ret, 0, 'delete error')

        sql_cmd = 'drop table test_regression'
        ret = yield self.fetcher_async.commit_sql_cmd(sql_cmd, "mysql_insight")
        self.assertEqual(ret, 0, 'drop table error')

