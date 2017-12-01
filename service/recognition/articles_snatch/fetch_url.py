#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import logging
import time, datetime
import random
import urllib, urllib2
from urlparse import urlparse
import traceback
from cStringIO import StringIO
import gzip
import pdb
import json
import ConfigParser
import cookielib
from pyquery import PyQuery
import re

en_threshold = 31

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

sys.stdout = Unbuffered(sys.stdout)
sys.stderr = Unbuffered(sys.stderr)

config = ConfigParser.ConfigParser()
config.readfp(open('config.ini', "rb"))

out_title_file = '../test/title_list.%s' % time.strftime('%Y-%m-%d',time.localtime(time.time()))
str_today = time.strftime('%Y-%m-%d 00:00',time.localtime(time.time()))
end_today = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time()))

def setup_logging(pathname):
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                  "%Y-%m-%d %H:%M:%S")
    log = logging.getLogger("app")
    log.setLevel(logging.DEBUG)

    sth = logging.StreamHandler()
    sth.setLevel(logging.INFO)
    sth.setFormatter(formatter)
    log.addHandler(sth)

    fhnd = logging.FileHandler(pathname)
    fhnd.setLevel(logging.DEBUG)
    fhnd.setFormatter(formatter)
    log.addHandler(fhnd)
    return log

log = setup_logging('log/%s.log' %(sys.argv[0].split('.')[0]))

def extract_info_homepage(html,param_dict):
    dom = PyQuery(unicode(html, param_dict['encoding'], "ignore"))
    return extract(dom,param_dict)

def extract_info(html):
    j = json.loads(html)
    html = j["data"]
    dom = PyQuery(html)
    return extract(dom)

def http_get_request(str_url,re_rule):
    response = urllib2.urlopen(str_url)
    res_result = json.loads(response.read())
    arr_re = re_rule.strip().split(',')
    result_set = res_result
    for re_item in arr_re:
        result_set = result_set[re_item]

    return result_set

def get_day_timestamp():
    today = datetime.date.today()
    timeStamp = int(time.mktime(datetime.date(today.year,today.month,today.day).timetuple()))
    return int(timeStamp)

def get_skip_articles(dom,param_dict):
    res = []
    d_stamp = get_day_timestamp()
    result_list = http_get_request(param_dict['skip_url'],param_dict['skip_rule'])
    for pos in range(len(result_list)):
        article_dict = result_list[pos]
        date_stamp = int(article_dict['ctime'])
        if date_stamp <= d_stamp:
            continue

        # 时间戳转化成日期
        x = time.localtime(date_stamp)
        date = time.strftime('%Y-%m-%d %H:%M',x)
        url = article_dict['url']
        if 'http://' not in url:
            url = 'http://' + url
        title = article_dict['title']
        date = format_date_time(date)
        if cmp(date,str_today) > 0:
            res.append([date,url,title])

    return res

def fomate_date_output(date):
    ct = datetime.datetime.now()
    rech = re.search(u'(\d+)\s*(天|小时|分钟)前', date)
    if rech:
        num = rech.group(1)
        tt = rech.group(2)
        mapping = {
            u'天':"days",
            u'小时':"hours",
            u'分钟':"minutes",
        }
        param = {mapping[tt]:int(num)}
        date = (ct - datetime.timedelta(**param)).strftime("%Y-%m-%d %H:%M")
    elif re.search(u'今天', date):
        date = ''.join(x for x in date if ord(x) < 256).strip()
        today = datetime.date.today()
        date = '%s %s' % (today.strftime('%Y-%m-%d'),date)
    elif re.search(u'昨天', date):
        date = ''.join(x for x in date if ord(x) < 256).strip()
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        date = '%s %s' % (yesterday.strftime('%Y-%m-%d'),date)
    elif re.search(u'前天',date):
        date = ''.join(x for x in date if ord(x) < 256).strip()
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=2)
        date = '%s %s' % (yesterday.strftime('%Y-%m-%d'),date)
    else:
        date = ''.join(x for x in date if ord(x) < 256).strip()
        if ']' in date:
            date = date.replace(']','')
            arr_list = re.split(':| |-',date.strip())
            if len(arr_list) != 4:
                return ct.strftime("%Y-%m-%d 06:00")

            for pos in range(len(arr_list)):
                arr_list[pos] = '%s' % arr_list[pos] if len(arr_list[pos]) ==2 else '0%s' % arr_list[pos]
            n_year = time.strftime('%Y',time.localtime(time.time()))
            date = '%s-%s-%s %s:%s' % (n_year,arr_list[0],arr_list[1],arr_list[2],arr_list[3])
        elif len(date) == 12:
            date = date.replace(' ','').replace(':','')
            date = '%s-%s-%s %s:%s' %(date[:4],date[4:6],date[6:8],date[8:10],date[10:12])
        elif len(date) == 8 and ']' not in date:
            date = date.replace(' ','').replace(':','')
            date = '%s-%s-%s 10:00' %(date[:4],date[4:6],date[6:8])
        elif len(date) == 10 and ':' in date:
            n_year = time.strftime('%Y',time.localtime(time.time()))
            arr_time = date.strip().split(' ')
            if len(arr_time) != 2 or len(arr_time[0]) != 4:
                return ct.strftime("%Y-%m-%d 06:00")
            
            date = '%s-%s-%s %s' % (n_year,arr_time[0][:2],arr_time[0][2:4],arr_time[1])
        else:
            date = ct.strftime("%Y-%m-%d 06:00")

    return date

def format_date_time(date):
    format_date = ''
    arr_date = date.strip().split(':')
    if len(arr_date) == 1:
        format_date = time.strftime("%Y-%m-%d %H:%M",time.localtime(time.time()))
    elif len(arr_date) == 3:
        format_date = '%s:%s' % (str(arr_date[0]).strip(),str(arr_date[1]).strip())
    else:
        format_date = date

    return format_date

def extract(dom,param_dict):
    res = []

    # dom head
    head_list = str(param_dict['dom_head']).strip().split(',')
    d_divs = dom(head_list[0])

    if len(head_list) > 1:
        for pos in range(1,len(head_list)):
            try:
                value = int(head_list[pos])
                d_divs = d_divs.eq(value)
            except :
                d_divs = d_divs.children(head_list[pos])
    
    for div in d_divs:
        d_div = PyQuery(div)
        if param_dict['sandwich'] != 'None':
            sandwich_list = str(param_dict['sandwich']).strip().split(',')
            for sandwich in sandwich_list:
                try :
                    positon = int(sandwich)
                    d_div = d_div.eq(positon)
                except:
                    d_div = d_div.children(sandwich)

        header = str(param_dict['title']).strip().split(',')[0]
        if not d_div.children(header):
            continue

        # 获取url 信息
        url_list = str(param_dict['url']).strip().split(',')
        url = d_div.children(url_list[0])
        for pos in range(1,len(url_list)):
            try:
                n_url = int(url_list[pos])
                url = url.eq(n_url)
            except:
                if url_list[pos] == 'href':
                    url = url.attr('href')
                    break
                else:
                    url = url.children(url_list[pos])

        # join url 
        if 'www' not in url and 'http' not in url:
            match = re.search('^/', url)
            if match:
                url = param_dict['domain'] + url
            else:
                url = param_dict['domain'] + '/'+url

        if 'http://' not in url:
            url = 'http://' + url

        # 获取title 信息
        title_list = str(param_dict['title']).strip().split(',')
        title = d_div
        for item in title_list:
            try:
                n_title = int(item)
                title = title.eq(n_title)
            except:
                title = title.children(item)

        title = title.text()

        date_list = str(param_dict['date']).strip().split(',')
        date = d_div
        is_attr = False
        for item in date_list:
            try:
                n_item = int(item)
                date = date.eq(n_item)
            except:
                if 'attr' not in item:
                    date = date.children(item)
                else:
                    item = item[:item.find(':')]
                    date = date.attr(item)[:10]
                    is_attr = True

        date = date if is_attr else date.text()
        if ' / ' in date:
            date = date.replace(' / ','-')

        if re.search(u'\d{4}-\d{1,2}-\d{1,2}', date):
            date = ''.join(x for x in date if ord(x) < 256).strip()
            start_index = date.rfind('201')   #第一次出现的位置
            end_index1 = date.rfind('-')
            end_index2 = date.rfind(':')
            end_index = end_index1 if end_index1 > end_index2 else end_index2
            date = date[start_index:end_index+3]
        else :
            try:
                # 时间戳转化成日期
                date_stamp = int(date)
                x = time.localtime(date_stamp)
                date = time.strftime('%Y-%m-%d %H:%M',x)
            except:
                date = fomate_date_output(date)

        date = format_date_time(date)
        if len(date) == 16:
            if cmp(date,str_today) > 0 and cmp(date,end_today) < 0 and len(title) > 0:
                res.append([date,url,title])

    return res

def gen_url_header(url): 
    return {
            'Host': '%s' % urlparse(url)[1],
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
    }

def get_config_param(url):
    dict_param = {}
    dict_param['domain'] = config.get(url,'domain')
    dict_param['page_identifier'] = config.get(url,'page_identifier')
    dict_param['title'] = config.get(url,'title')
    dict_param['url'] = config.get(url,'url')
    dict_param['dom_head'] = config.get(url,'dom_head')
    dict_param['date'] = config.get(url,'date')
    dict_param['encoding'] = config.get(url,'encoding')
    dict_param['skip_url'] = config.get(url,'skip_url')
    dict_param['skip_rule'] = config.get(url,'skip_rule')
    dict_param['sandwich'] = config.get(url,'sandwich')
    return dict_param

def get_url_code(url,param_dict,record=True):
    log.info('[snatch][fetch wait][url=%s]', url)
    req = urllib2.Request(url, headers=gen_url_header(url))
    hh = urllib2.HTTPHandler()
    opener = urllib2.build_opener(hh)
    reply = opener.open(req, timeout=30)
    if reply.info().get('Content-Encoding') == 'gzip':
        buf = StringIO(reply.read())
        f = gzip.GzipFile(fileobj=buf)
        r = f.read()
        f.close()
        buf.close()
        reply.close()
    else:
        r = reply.read()

    if param_dict['skip_url'] == 'None':
        res = extract_info_homepage(r,param_dict)
    else:
        res = get_skip_articles(r,param_dict)
    return res

def existing_results_set():
    existing_dict = {}
    if not os.path.exists(out_title_file):
        os.mknod(out_title_file)
        return existing_dict

    with open(out_title_file) as f_info:
        for line in f_info:
            arr_info = line.strip().split('\t')
            if len(arr_info) == 4:
                existing_dict[arr_info[1]] = 1

    return existing_dict

def write_output_stream(res,existing_dict,out_handle,is_en):
    if res is None or len(res) < 1:
        return out_handle

    for item in res:
        if len(item) == 3:
            date ,url , title  = item[0],item[1],item[2]
            if url not in existing_dict:
                existing_dict[url] = 1
                out_handle.write('%s\t%s\t%s\t%s\n' % (date,url,title,is_en))

    return out_handle,existing_dict

def main():
    n_count = 0
    existing_dict = existing_results_set()
    out_handle = open(out_title_file,'a')
    with open('./urls.txt') as f_url:
        for line in f_url:
            try:
                str_url = line.strip()
                n_count += 1
                if n_count <= 33:
                    param_dict = get_config_param(str_url)
                    res = get_url_code(str_url,param_dict)
                    is_en = 1 if n_count >= 31 else 0
                    if len(res) > 0:
                        out_handle,existing_dict = write_output_stream(res,existing_dict,out_handle,is_en)
                    if param_dict['page_identifier'] != 'None':
                        arr_page = str(param_dict['page_identifier']).strip().split('|^|')
                        n_page = int(arr_page[0])+1
                        # 第二页开始
                        if n_page >= 2:
                            for pos in range(2,n_page):
                                page_url = arr_page[1] % pos
                                res2 = get_url_code(page_url,param_dict)
                                if len(res2) > 0:
                                    out_handle,existing_dict = write_output_stream(res2,existing_dict,out_handle,is_en)
                else:
                    break
            except Exception as e:
                print log.error('error:%s' % e)

    out_handle.close()

if __name__ == '__main__':
    main()
    #test()

