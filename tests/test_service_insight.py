#!/usr/bin/env python
# encoding: utf-8
import sys,os
import unittest
from curses.has_key import has_key
reload(sys)
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../service/insight')))
from tornado.testing import gen_test
from tornado.testing import AsyncTestCase
from insight_fetcher import InsightFetcher


class TestDBFetcherAsync(AsyncTestCase):
    def setUp(self):
        super(TestDBFetcherAsync, self).setUp()
        self.data_fetcher = InsightFetcher()

    def tearDown(self):
        super(TestDBFetcherAsync, self).tearDown()

    @gen_test
    def test_get_dau_data(self):
        cid = '1515'
        r = yield self.data_fetcher.get_dau_data(cid)
        self.assertTrue(r.has_key('y_list') and r['y_list'][0].has_key('name') and r['y_list'][0]['name'] == '36氪', 'get dau data error')
