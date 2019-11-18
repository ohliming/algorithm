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
import re, codecs

sys.path.append('../../')
from common.db_fetcher import DataBaseFetcher
db_fetcher = DataBaseFetcher()

en_threshold = 50

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

out_title_file = './data/title_list.%s' % time.strftime('%Y-%m-%d',time.localtime(time.time()))
str_today = time.strftime('%Y-%m-%d 00:00',time.localtime(time.time()))
end_today = time.strftime('%Y-%m-%d 23:59',time.localtime(time.time()))
proxy_today = time.strftime('%Y-%m-%d 23:00',time.localtime(time.time()))

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
    return extract(dom, param_dict)

def extract_info(html):
    j = json.loads(html)
    html = j["data"]
    dom = PyQuery(html)
    return extract(dom)

def http_get_request(str_url, re_rule):
    response = urllib2.urlopen(str_url).read()
    if response[:3]==codecs.BOM_UTF8:
        response = response[3:]
    
    if 'data_callback(' in response:
        response = response.replace('data_callback(','{\"result\":').replace(')','}')
        response = response.decode('gbk').encode('utf8')
    res_result = json.loads(response)
    arr_re = re_rule.strip().split(',')
    result_set = res_result
    for re_item in arr_re:
        result_set = result_set[re_item]

    return result_set

def get_day_timestamp():
    today = datetime.date.today()
    timeStamp = int(time.mktime(datetime.date(today.year,today.month,today.day).timetuple()))
    return int(timeStamp)

def get_skip_articles(dom, param_dict):
    res = []
    result_list = http_get_request(param_dict['skip_url'],param_dict['skip_rule'])
    if param_dict['domain'] == 'www.xtecher.com':
        return extract_info_homepage(str(result_list),param_dict)
    for pos in range(len(result_list)):
        article_dict = result_list[pos]
        article_time = article_dict[param_dict['skip_time']]
        try:
            date_stamp = int(article_time)

            # 时间戳转化成日期
            x = time.localtime(date_stamp)
            date = time.strftime('%Y-%m-%d %H:%M',x)
        except:
            if re.search(u'\d{4}-\d{1,2}-\d{1,2}', article_time):
                date = ''.join(x for x in article_time if ord(x) < 256).strip()
                if ':' not in date:
                    date = '%s %s' % (date,time.strftime('%H:%M',time.localtime(time.time())))
                else:
                    arr_date = date.split(':')
                    date = '%s:%s' % (arr_date[0],arr_date[1])
            else:
                date = fomate_date_output(article_time)

        url = article_dict[param_dict['skip_uri']]
        if param_dict['domain'] not in url:
            url = param_dict['domain'] +'/'+ url

        if 'http://' not in url:
            url = 'http://' + url

        title = article_dict[param_dict['skip_title']]
        date = format_date_time(date)
        content = extract_url_content(url, param_dict)
        if cmp(date,str_today) >= 0 and len(title) >0 and len(content) > 0:
            res.append([date,url,title, content])

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
    elif re.search(u'月',date) and re.search(u'日',date) and not re.search(u'年',date):
        date = ''.join(x for x in date if ord(x) < 256).strip()
        if len(date) == 4:
            date = '%s-%s-%s %s' % (ct.strftime("%Y"), date[:2], date[2:],ct.strftime("%H:%M"))
        elif len(date) == 9:
            date = '%s-%s-%s %s' % (ct.strftime("%Y"),date[:2], date[2:4], date[4:])
	else:
            date = ct.strftime("%Y-%m-%d %H:%M")      
    elif re.search(u'年',date) and re.search(u'月',date) and re.search(u'日',date) and ':' not in date:
        date = ''.join(x for x in date if ord(x) < 256).strip()
        arr_date = [ '%s' % x if int(x) > 10 else '0%s' % x for x in date.strip().split(' ') if x != '']
        if len(arr_date) == 3:
            date = '%s-%s-%s %s' % (arr_date[0],arr_date[1],arr_date[2],ct.strftime("%H:%M"))
        elif len(arr_date) == 1 and len(arr_date[0]) != 8:
            d_month = int(arr_date[0][4:6])
            n_month = int(ct.strftime("%m"))
            month_pos = 1
            if n_month >= 10 and d_month < 13:
                month_pos = 2

            n_month = int(arr_date[0][4:4+month_pos])
            n_day = int(arr_date[0][4+month_pos:])
            d_month = '0%s'% n_month if  n_month < 10 else '%s' % n_month
            d_day =  '0%s' % n_day if n_day < 10 else '%s' % n_day
            date = '%s-%s-%s %s' % (arr_date[0][:4],d_month,d_day,ct.strftime("%H:%M"))
        elif len(arr_date) == 1 and len(arr_date[0]) == 8:
            date = '%s-%s-%s %s' % (arr_date[0][:4],arr_date[0][4:6],arr_date[0][6:], ct.strftime("%H:%M"))
        else:
            date = ct.strftime("%Y-%m-%d %H:%M")
    elif re.search(u'年',date) and re.search(u'月',date) and re.search(u'日',date) and ':' in date and not re.search(u'上午',date) and not re.search(u'下午',date):
        date = date.replace(' ','')
        date = date.replace(u'日',' ')
        date = date.replace(u'年','-').replace(u'月','-')
    else:
        date = ''.join(x for x in date if ord(x) < 256).strip()
        if ',' in date: date = date.replace(',','').strip()
        if ']' in date:
            date = date.replace(']','')
            arr_list = re.split(':| |-',date.strip())
            if len(arr_list) != 4:
                    return ct.strftime("%Y-%m-%d %H:%M")
            for pos in range(len(arr_list)):
                arr_list[pos] = '%s' % arr_list[pos] if len(arr_list[pos]) ==2 else '0%s' % arr_list[pos]
            n_year = time.strftime('%Y',time.localtime(time.time()))
            date = '%s-%s-%s %s:%s' % (n_year,arr_list[0],arr_list[1],arr_list[2],arr_list[3])
        elif len(date) == 5 and '-' in date:
            n_year = time.strftime('%Y',time.localtime(time.time()))
            n_time = time.strftime('%H:%M',time.localtime(time.time()))
            date = '%s-%s %s' % (n_year,date,n_time)
        elif len(date) == 12:
            date = date.replace(' ','').replace(':','')
            date = '%s-%s-%s %s:%s' %(date[:4],date[4:6],date[6:8],date[8:10],date[10:12])
        elif len(date) == 8 and ']' not in date:
            date = date.replace(' ','').replace(':','')
            date = '%s-%s-%s %s' % (date[:4],date[4:6],date[6:8],ct.strftime("%H:%M"))
        elif len(date) == 14  and ':' in date:
            arr_time = date.split(' ')
            date = '%s-%s-%s %s' % (arr_time[0][:4],arr_time[0][4:6],arr_time[0][6:8],arr_time[1])
        elif len(date) == 10 and ':' in date:
            n_year = time.strftime('%Y',time.localtime(time.time()))
            arr_time = date.strip().split(' ')
            if len(arr_time) != 2 or len(arr_time[0]) != 4:
                return ct.strftime("%Y-%m-%d %H:%M")
            date = '%s-%s-%s %s' % (n_year,arr_time[0][:2],arr_time[0][2:4],arr_time[1])
        else:
            date = ct.strftime("%Y-%m-%d %H:%M")

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

def extract(dom, param_dict):
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
        try:
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
            url = d_div
            for pos in range(0,len(url_list)):
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

            url = url.strip()
           
            # 获取title 信息
            title_list = str(param_dict['title']).strip().split(',')
            title = d_div
            for item in title_list:
                try:
                    n_title = int(item)
                    title = title.eq(n_title)
                except:
                    title = title.children(item)

            title = title.text().strip()

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
                        date = date.attr(item)[:20].strip()
                        is_attr = True
            
            date = date if is_attr else date.text()
            if ' / ' in date: date = date.replace(' / ','-')
            if '/' in date: date = date.replace('/','-')
            if re.search(u'\d{4}-\d{1,2}-\d{1,2}', date):
                date = ''.join(x for x in date if ord(x) < 256).strip()
                start_index = date.rfind('201')   #第一次出现的位置
                end_index1 = date.rfind('-')
                end_index2 = date.rfind(':')
                end_index = end_index1 if end_index1 > end_index2 else end_index2
                date = date[start_index:end_index+3]
                if len(date) == 10:
                    date = '%s %s' % (date,time.strftime("%H:%M",time.localtime(time.time())))
            elif re.search(u'\d{1,2}-\d{1,2}-\d{4} \d{1,2}:\d{1,2}:\d{1,2}', date):
                arr_time = date.split(' ')
                arr_date = arr_time[0].split('-')
                date = '%s-%s-%s %s' % (arr_date[2],arr_date[0],arr_date[1],arr_time[1])
            else :
                try:
                    # 时间戳转化成日期
                    date_stamp = int(date)
                    if date_stamp > 9999999999:
                        date_stamp = int(date[:10])
                    
                    x = time.localtime(date_stamp)
                    date = time.strftime('%Y-%m-%d %H:%M',x)
                except:
                    date = date.replace(' ','')
                    date = fomate_date_output(date)

            date = format_date_time(date)
            content = extract_url_content(url, param_dict)
            if len(date) == 16:
                if cmp(date,str_today) >= 0 and cmp(date,end_today) <= 0 and len(title) > 0 and len(content) > 0:
                    res.append([date, url, title, content])
        except:
            continue

    return res

def extract_url_content(url, param_dict):
    try:
        if param_dict['proxy'] == 'No':
            req = urllib2.Request(url, headers=gen_url_header(url))
            hh = urllib2.HTTPHandler()
            opener = urllib2.build_opener(hh)
            reply = opener.open(req, timeout = 40)
            if reply.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(reply.read())
                f = gzip.GzipFile(fileobj=buf)
                r = f.read()
                f.close()
                buf.close()
                reply.close()
            else:
                r = reply.read()
        else:
            r = get_http_proxy(url, param_dict)
            span = random.uniform(1,3)
            time.sleep(span)

        dom = PyQuery(unicode(r, param_dict['encoding'], "ignore"))
        # dom body
        content_list = str(param_dict['content']).strip().split(',')
        d_divs = dom(content_list[0])
        if len(content_list) > 1:
            for pos in range(1,len(content_list)):
                try:
                    value = int(content_list[pos])
                    d_divs = d_divs.eq(value)
                except :
                    d_divs = d_divs.children(content_list[pos])

        str_content = d_divs.text()
        # process tech qq
        filter_list = ['var', '#endText', '[].forEach','function','.tag-editor','jQuery.ajax','.heading','.list']
        for str_filter in filter_list:
            if str_filter in str_content:
                end_pos = str_content.find(str_filter)
                str_content = str_content[:end_pos]

        return str_content.strip()
    except:
        return '' # 返回空字符

def gen_url_header(url): 
    return {
            'Host': '%s' % urlparse(url)[1],
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0',
            'Accept-Encoding': '*;q=0',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
    }

def get_http_proxy(url, param_dict):
    gen_header  = {'Host': '%s' % param_dict['domain'],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36',
        'Accept-Encoding': '*;q=0',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Cookie': '',
    }
    retry = 3
    req = urllib2.Request(url,headers = gen_header)
    while retry > 0:
        try:  
            # 高匿列表：http://www.xicidaili.com/nn/
            # http://www.kuaidaili.com/api/getproxy/?orderid=911437689066915&num=800&browser=1&protocol=2&method=2&sort=0&sep=2 
            proxy_handler = urllib2.ProxyHandler({'http': '%s' % '212.91.189.162:80'})
            opener = urllib2.build_opener(proxy_handler)
            reply = opener.open(req, timeout=30)
            r = reply.read()
            reply.close()
            return r.strip()
        except Exception,e:
            retry -= 1
    return ''

def get_config_param(config, url):
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
    dict_param['skip_time'] = config.get(url,'skip_time')
    dict_param['skip_uri'] = config.get(url,'skip_uri')
    dict_param['skip_title'] = config.get(url,'skip_title')
    dict_param['content'] = config.get(url,'content')
    dict_param['proxy'] = config.get(url, 'proxy')

    return dict_param

def get_url_code(url, param_dict, record=True):
    log.info('[snatch][fetch wait][url=%s]', url)
    if param_dict['proxy'] == 'No':
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
    else:
        now_time = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time())) 
        if now_time <= proxy_today: return []
        r = get_http_proxy(url, param_dict)
        span = random.uniform(1,3)
        time.sleep(span)

    if r == '': return []
    if param_dict['skip_url'] == 'None':
        res = extract_info_homepage(r, param_dict)
    else:
        res = get_skip_articles(r,param_dict)

    return res

# get fetch url list
def get_exist_url_set():
    db_data = db_fetcher.get_sql_result("select url from news_report where publish_date >= \'%s\'" % str_today,'mysql_insight')
    url_list = []
    for pos in range(len(db_data)):
        url = str(db_data[pos][0])
        url_list.append(url)

    existing_set = set(url_list)
    return existing_set

def write_databases_stream(res, existing_set, param_dict):
    source_dict = {
    'www.huxiu.com':'虎嗅',
    'tech.qq.com':'腾讯科技',
    'tech.sina.com.cn':'新浪科技',
    'tech.163.com':'163科技',
    'www.lieyunwang.com':'猎云网',
    'www.iyiou.com':'亿欧网',
    'www.iheima.com':'i黑马',
    'www.pedaily.cn':'投资界',
    'www.leiphone.com':'雷锋网',
    'www.pingwest.com':'pingwest品玩',
    'www.geekpark.net':'极客学院',
    'www.tmtpost.com':'钛媒体',
    'www.techweb.com.cn':'TechWeb',
    'www.ikanchai.com':'砍柴网',
    'www.cnbeta.com':'cnBeta',
    'www.pintu360.com':'品途360',
    'www.21jingji.com':'21经济网',
    'www.duozhi.com':'多知网',
    'www.jiemodui.com':'芥末堆',
    'www.pinchain.com':'品橙旅游',
    'www.traveldaily.cn':'环球旅讯',
    'www.vcbeat.net':'动脉网',
    'm.cheyun.com':'车云网',
    'news.mydrivers.com':'快科技',
    'www.sootoo.com':'速途网',
    'www.ifanr.com':'爱范儿',
    'www.donews.com':'donews',
    'www.pencilnews.cn':'铅笔道',
    'www.2b.cn':'托比网',
    'www.jiemian.com':'界面新闻',
    'www.xfz.cn':'小饭桌',
    'www.xtecher.com':'xtecher',
    'chuansong.me':'传送门',
    'zhidx.com':'智东西',
    'www.vr2048.com':'VR2048',
    'www.3wyu.com':'三文娱',
    'www.vrzinc.com':'vrzinc',
    'www.expar.cn':'极AR',
    'newseed.pedaily.cn':'新芽',
    'toutiao.welian.com':'微链',
    'www.b12.cn':'12楼',
    'cn.technode.com':'动点科技',
    'it.sohu.com':'搜狐科技',
    'www.cyzone.cn':'创业邦',
    'tech2ipo.com':'Tech2IPO创见',
    'www.chinaventure.com.cn':'ChinaVenture'
    }

    for item in res:
        date, url, title, content = item[0], item[1], item[2], item[3]
        if url in existing_set: continue
        domain = param_dict['domain']
        source = source_dict[domain] if domain in source_dict else 'UnKnown'
        if '\'' in title: title = title.replace('\'','\"')
        if '\'' in content: content = content.replace('\'', '\"')
        insert_sql = "insert into news_report(url, publish_date, title, content, source, domain) values(\'%s\', \'%s\', \'%s\', \'%s\', \'%s\',\'%s\')" % (url, date, title, content, source, domain)
        db_fetcher.commit_sql_cmd(insert_sql, 'mysql_insight')

# url.txt path
def cache_domain_param(fetch_path = '.'):
    dict_domain_param = {}
    url_file = '%s/urls.txt' % fetch_path
    config = ConfigParser.ConfigParser()
    config.readfp(open('%s/config.ini' % fetch_path, "rb"))

    with open(url_file) as url_f:
        for line in url_f:
            str_url = line.strip()
            param_dict = get_config_param(config,str_url)
            domain = param_dict['domain']
            dict_domain_param[domain] = param_dict

    return dict_domain_param

# source: 描述:文章来源, 类型: text 例子: it 桔子
def storage_news_resport(cid, url, title, domain, source, flag, publish_date, dict_domain_param):
    str_content = ''
    if domain in dict_domain_param:
        dict_param = dict_domain_param[domain]
        str_content = extract_url_content(url, dict_param)
    update_sql = "REPLACE INTO news_report(url, reported_com, title, source, type, publish_date, content, domain) VALUES(\'%s\', %s,\'%s\', \'%s\', %s, \'%s\',\'%s\',\'%s\')" \
                % (url, cid, title, source, flag, publish_date, str_content, domain)
    db_fetcher.commit_sql_cmd(update_sql, 'mysql_insight')

def main():
    n_count = 0
    existing_set = get_exist_url_set()
    config = ConfigParser.ConfigParser()
    config.readfp(open('config.ini', "rb"))
    with open('./urls.txt') as f_url:
        for line in f_url:
            try:
                str_url = line.strip()
                n_count += 1
                if n_count <= 48:
                    param_dict = get_config_param(config, str_url)
                    res = get_url_code(str_url, param_dict)
                    if len(res) > 0:
                        write_databases_stream(res, existing_set, param_dict)

                    if param_dict['page_identifier'] != 'None':
                        arr_page = str(param_dict['page_identifier']).strip().split('|^|')
                        n_page = int(arr_page[0])+1
                        # 第二页开始
                        if n_page >= 2:
                            for pos in range(2, n_page):
                                page_url = arr_page[1] % pos
                                res2 = get_url_code(page_url, param_dict)
                                if len(res2) > 0:
                                    write_databases_stream(res2, existing_set, param_dict)
                else:
                    break
            except Exception as e:
                print log.error('error:%s' % e)

if __name__ == '__main__':
    main()
    # test storage_news_resport
    """
    fetch_path = '.' # news_report path 
    dict_domain_param = cache_domain_param(fetch_path)
    cid = 158310
    url   = 'http://www.geekpark.net/topics/216656'
    title = 'Twitter 将[卖身]：蓝色小鸟飞不过沧海，你是否忍心责怪'
    source = 'it桔子'
    flag = 1
    publish_date = '2016-09-07 16:09:00'
    domain = 'www.geekpark.net'
    storage_news_resport(cid, url, title, domain, source, flag, publish_date, dict_domain_param)"""

