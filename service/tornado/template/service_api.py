#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class ServiceAPI:
    '''
    ## 用户自定义的接口
    ## 1.新增接口名称需要增加至cmds列表
    ## 2.新增接口逻辑需要增加handle()函数
    ## 3.handle函数返回Str或Json格式: {"code':0,"msg":"ok","data":{}}
    '''
    cmds = ['alive','test']
    def __init__(self, log):
        self.log = log
        self.log.info("RequestHandler initialized")

    ## 业务处理函数模块
    def mytest(self,params):
        import time
        time.sleep(3)
        r = {}
        r['msg'] = 'test'
        if 'msg' in params:
            r['msg'] = params['msg']
        return r

    ## 请求处理函数模块
    def handle(self, params):
        if not params['cmd'] in ServiceAPI.cmds:
            return {'msg':'no such method %s!'} % params['cmd']
        if params['cmd'] == 'alive':
            return {'msg':'ok'}
        elif params['cmd'] == 'test':
            return self.mytest(params)
