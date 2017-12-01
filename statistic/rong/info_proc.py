#!/usr/bin/env python
#coding=utf8
'''
@author: cuiyan
'''
import sys,re,math

class ComInfoProc:
    @staticmethod
    def url_stemming(url):
        url = url.strip('/')
        pos = url.find('://')
        if pos != -1:
            url = url[pos+3:]
        if url.startswith('www.'):
            url = url[4:]
        #if re.search('com\...$', url):
        #    url = url[:-3]
        return url
    @staticmethod
    def extract_appid(app_url):
        app_id = ''
        app_re = re.search('/id\d+', app_url)
        if app_re:
            app_id = app_re.group()[3:]
        elif app_url.isdigit():
            app_id = app_url
        return app_id

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print '[Usage] %s id_name_url_app' % sys.argv[0]
        sys.exit(-1)

