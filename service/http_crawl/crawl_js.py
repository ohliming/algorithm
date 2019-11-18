#!/usr/bin/python
# -*- coding: utf-8 -*- 
import sys
reload(sys)
sys.setdefaultencoding('UTF-8')

import json,urllib,urllib2,json,chardet,re,gzip
import requests
from http_request import *

from bs4 import BeautifulSoup

sys.path.append('../../')
from common.db_fetcher import DataBaseFetcher
db_fetcher = DataBaseFetcher() # database

js_host = "http://www.w3school.com.cn"
js_url = "http://www.w3school.com.cn/jsref/jsref_obj_array.asp"

def parse_table(table):
    trs  = table.find_all('tr')
    content = ''
    for tr in trs:
        xlist = [] 
        for x in tr:
            try:
                xlist.append(x.text.replace('\n', '').replace('\r','')) # add list 
            except:
                continue

        content += '|$|'.join([str(x).strip() for x in xlist]) + '\n' # content
    
    return content.strip() # res

# crawl tutorial
def parse_js_content(li_url): # parse
    js_html = get_request(li_url, js_host, {}) # text 

    js_soup = BeautifulSoup(js_html, 'lxml')
    contents = js_soup.find('div', id = 'maincontent')

    div_cnt = 0
    str_desc, str_attr, str_funs = '', '', '' # result
    for item in contents:
        if item.name is None: continue
        if item.name == 'div':
            div_cnt += 1
            if div_cnt == 1:
                str_desc = str(item.text).strip() # desc
            elif div_cnt == 2:
                for tag in item:
                    if tag.name is None: continue
                    str_attr += parse_table(tag) if tag.name == 'table' else tag.text + '\n'
            elif div_cnt == 3:
                for tag in item:
                    if tag.name is None: continue
                    str_funs += parse_table(tag) if tag.name == 'table' else tag.text + '\n'

    str_desc = str_desc.replace('\'', '')
    str_attr = str_attr.replace('\'', '')
    str_funs = str_funs.replace('\'', '')

    return str_desc, str_attr, str_funs

main_html = get_request(js_url, js_host, {}) # js host
insert_sql = "insert into crawl_js(js_obj, js_desc, js_attr, js_funs) values"
cnt = 0
if main_html is not None:
    soup = BeautifulSoup(main_html, 'lxml')
    course = soup.find('div', id = 'course') # course 
    jss = course.find_all('ul') # ul

    for ul in jss:
        lis = ul.find_all('li')
        for li in lis:
            li_text = str(li.a.text) # text
            li_href = li.a.attrs['href']
            li_url = "%s%s" % (js_host, li_href) # href

            try: # jsref
                if 'jsref_obj' in li_href:
                    # do something
                    str_desc, str_attr, str_funs = parse_js_content(li_url) # li
                    print li_text
                    cnt += 1
                    insert_sql += "(\'%s\', \'%s\', \'%s\',\'%s\')" % (li.text, str_desc, str_attr, str_funs)
                    if cnt % 3 == 0:
                        db_fetcher.commit_sql_cmd(insert_sql, "mysql_duyi_core")
                        insert_sql = "insert into crawl_js(js_obj, js_desc, js_attr, js_funs) values"
                    else:
                        insert_sql += ","
            except:
                print li_url

    insert_sql = insert_sql[:len(insert_sql)-1]
    db_fetcher.commit_sql_cmd(insert_sql, "mysql_duyi_core")


            