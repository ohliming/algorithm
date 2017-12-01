#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os

sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))

from hotsfind import HotsFind
import json
import time

class ServiceAPI:
    '''
    ## 用户自定义的接口
    ## 1.新增接口名称需要增加至cmds列表
    ## 2.新增接口逻辑需要增加handle()函数
    ## 3.handle函数返回Str或Json格式: {"code':0,"msg":"ok","data":{}}
    '''
    cmds = ['test','update','init','hotsfind']
    m_hotfind = HotsFind('./keywords.txt')
    def __init__(self, log):
        self.log = log
        self.log.info('Service Initialized.')
        str_today =  time.strftime('%Y-%m-%d',time.localtime(time.time()))
        data_titile = './articles_snatch/data/title_list.%s' % str_today
        self.url_title,self.url_date,self.url_en = self.m_hotfind.read_articles_title(data_titile)

    def handle(self, params):
        if not params['cmd'] in ServiceAPI.cmds:
            return {'msg':'no such method %s!'} % params['cmd']
        ret = {}
        if params['cmd'] == 'test':
            ret = {"msg":"ok"}
        elif params['cmd'] == 'init':
            self.m_hotfind.clear_history_init('./keywords.txt')
            ret = {"msg":"clear success cache"}
        elif params['cmd'] == 'update':
            str_today =  time.strftime('%Y-%m-%d',time.localtime(time.time()))
            data_titile = './articles_snatch/data/title_list.%s' % str_today
            self.url_title,self.url_date,self.url_en = self.m_hotfind.read_articles_title(data_titile)
            ret = {"msg":"url len :%s" % len(self.url_title)}
        elif params['cmd'] =='hotsfind':
            ret = self.m_hotfind.find_hotspot(self.url_title,self.url_date,self.url_en)
        return ret

if __name__ == '__main__':
    pass
