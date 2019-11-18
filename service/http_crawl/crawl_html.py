#!/usr/bin/python
# -*- coding: utf-8 -*- 
import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )

import json,urllib,urllib2,json,chardet,re
from http_request import *

from bs4 import BeautifulSoup

sys.path.append('../../')
from common.db_fetcher import DataBaseFetcher
db_fetcher = DataBaseFetcher() # database

html_host = "https://www.w3cschool.cn" # host
html_url = "https://www.w3cschool.cn/htmltags/" # html

def parse_html_attribute(tag_url):
    str_content = ''
    attribute_html = get_request(tag_url, html_host, {}) # get host
    soup = BeautifulSoup(attribute_html, 'lxml')
    header = soup.find('div', id = 'pro-mian-header').find('div', class_ = 'content-top')
    title = header.h1.text # title 
    
    contents = soup.find('div', class_ = 'article-intro') # content
    if contents is None: contents = soup.find('div', class_ = 'content-intro')

    for item in contents:
        if item.name == 'table':
            # this is table process
            trs  = item.tbody.find_all('tr')
            for tr in trs:
                xlist = [] # list 
                for x in tr:
                    try:
                        xlist.append(x.text.replace('\n', '').replace('\r','')) # add list 
                    except:
                        continue

                str_content += '|$|'.join([str(x).strip() for x in xlist]) + '\n' # content
        else:
            try:
                str_content += item.text + '\n' # normal
            except:
                continue

    str_content = str_content.replace('\'', '').strip() # str
    return str_content

# crawl tutorial
main_html = get_request(html_url, html_host, {}) # jquery host
cnt = 0

insert_sql = "insert into crawl_html(html_title, `type`, html_content) values"
if main_html is not None:
    soup = BeautifulSoup(main_html, 'lxml') # soup 
    left = soup.find('div', id = 'nestable_handbook')
    items = left.find_all('ol', class_='dd-list')
    is_first = True 
    for item in items:
        if is_first == True:
            # do something more
            dd_items = item.find_all('li', class_='dd-item') # dd
            for dd in dd_items:
                tag_name =  dd.div.a.text # text
                tag_reference = dd.attrs['data-id']
                tag_url = '%s%s.html' % (html_url, tag_reference) # reference
                ctype = 1 if 'tag' in tag_reference else 2

                try: # html attribute
                    str_content =  parse_html_attribute(tag_url) # parase
                    insert_sql += "(\'%s\', %s, \'%s\')" % (tag_name, ctype, str_content)
                    cnt += 1
                    if cnt % 5 == 0:
                        res = db_fetcher.commit_sql_cmd(insert_sql, "mysql_duyi_core")
                        insert_sql = "insert into crawl_html(html_title, `type`, html_content) values"
                    else:
                        insert_sql += "," # insert
                except:
                    print tag_url
                    
            is_first = False # false 
        else:
            break

    insert_sql = insert_sql[:len(insert_sql)-1]
    res = db_fetcher.commit_sql_cmd(insert_sql, "mysql_duyi_core") # core 
