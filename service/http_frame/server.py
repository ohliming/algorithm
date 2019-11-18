#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), './')))
import time,json
from optparse import OptionParser
import logging,logging.handlers

import tornado.web
import tornado.gen
import tornado.ioloop as ioloop
import tornado.httpserver as httpserver
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

from service_api import ServiceAPI

class ServerHandler(tornado.web.RequestHandler):
    # 线程池
    executor = None

    def initialize(self,api,mode,thread_pool):
        self.api = api
        self.mode = mode
        if ServerHandler.executor == None:
            ServerHandler.executor = ThreadPoolExecutor(thread_pool)
    def reply_str(self, resp):
        ret = resp if type(resp) is str else json.dumps(resp, ensure_ascii=False).encode('utf8')
        self.set_status(200,'OK')
        self.set_header("Access-Control-Allow-Origin","*")
        self.set_header("Content-Type","text/javascript;charset=UTF-8")
        self.set_header("Content-Length",len(ret))
        self.write(ret)
        self.finish()
    ## GET method
    def get(self):
        self.handle_request()
    ## POST method
    def post(self):
        self.handle_request()

    ## 异步非阻塞
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def handle_request(self):
        params = {}
        for (k,v) in self.request.arguments.items():
            params[k] = ','.join(v)

        if not 'cmd' in params:
            r = '{"msg":"No [cmd=xxx] Found!"}'
            self.reply_str(r)
        else:
            if self.mode == 0: # Process
                r = self.my_process_function(params)
                self.reply_str(r)
            elif self.mode == 1: # Thread
                r = yield self.my_thread_function(params)
                self.reply_str(r)
            elif self.mode == 2:
                r = yield self.api.handle(params)
                self.reply_str(r)

        timing = int(round(self.request._finish_time - self.request._start_time)) * 1000
        cmd_line = self.request.uri
        if len(cmd_line) < 3:
            cmd_line += '?cmd=%s&...' % params['cmd']
        if timing > 1000:
            self.api.log.info("timeout %s : %d ms" % (cmd_line,timing))
        else:
            self.api.log.info("%s : %d ms" % (cmd_line,timing))

    # 线程处理
    @run_on_executor
    def my_thread_function(self, params):
        return self.api.handle(params)

    # 进程处理
    def my_process_function(self, params):
        return self.api.handle(params)

def main():
    ## 1.args parse
    usage = 'python ./server.py [options]\nExample: python ./server.py --port=9999 --mode=0 --processes=2 --threads=10'
    opt_parser = OptionParser(usage)
    opt_parser.add_option("--port", dest="port", default=9999, help="服务端口")
    opt_parser.add_option("--mode", dest="mode", default=0, help="服务模式: 0-同步阻塞（多进程）, 1-同步阻塞（多进程+线程池）, 2-异步非阻塞（多进程）")
    opt_parser.add_option("--processes", dest="num_process", default=1, help="启动进程数")
    opt_parser.add_option("--threads", dest="num_thread", default=1, help="每个进程下的线程池大小")
    opt_parser.add_option("--logdir", dest="log_dir", default= "./", help="日志位置")
    (options, args) = opt_parser.parse_args()

    ## 2.init log
    logger_name = 'server_logger'
    logger_filename = 'server.log'
    logger_level = logging.INFO
    logger_format = '%(asctime)s - %(message)s'
    logger_backup_count = 5
    logger_max_bytes = 128*1024*1024
    slogger = logging.getLogger(logger_name)
    slogger.handlers = []
    file_log = logging.handlers.RotatingFileHandler(options.log_dir+"/"+logger_filename,
               backupCount=logger_backup_count,maxBytes=logger_max_bytes)
    file_log.setFormatter(logging.Formatter(logger_format))
    slogger.addHandler(file_log)
    slogger.setLevel(logger_level)
    slogger.propagate = False

    ## 用户自定义接口
    service_api = ServiceAPI(slogger)

    ## 3.start server
    app = tornado.web.Application(handlers=[(r"/.*", ServerHandler, dict(api=service_api,mode=int(options.mode),thread_pool=int(options.num_thread))),])
    http_server = httpserver.HTTPServer(app)
    http_server.bind(int(options.port))
    http_server.start(int(options.num_process))
    ioloop.IOLoop.instance().start()
    return 0

if __name__=='__main__':
    sys.exit(main())
