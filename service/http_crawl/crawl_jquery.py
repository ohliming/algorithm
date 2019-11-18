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

jquery_host = "http://jquery.cuishifeng.cn"
jquery_url = "http://jquery.cuishifeng.cn/index.html"

def parse_jquery_attribute(attribute_url):
    attribute_html = get_request(attribute_url, jquery_host, {})
    soup = BeautifulSoup(attribute_html, 'lxml')
    content = soup.find_all('div', id = 'content')

    # retVal
    retVal = content.h2.span.text if content.h2 is not None else ''

    # summarize
    summarize = soup.find('div', class_='desc')
    str_summarize = '' 
    if summarize is not None:
        p_items = summarize.find_all('p') # items
        str_summarize = ''
        for item in p_items: str_summarize += '\n' + item.text # text
        str_summarize = str_summarize.strip() # resss

    # param
    parameter = soup.find('div', class_='parameter')
    str_parameter = '\n'.join([str(x.text) for x in parameter]) if parameter is not None else ''
    str_parameter = str_parameter.strip() # param 

    # example
    example = soup.find('div', class_='example')
    str_example = '\n'.join([str(x.text) for x in example ]) if example is not None else ''
    str_example = str_example.strip() # example

    # remove \'
    retVal = retVal.replace("\'", "")
    str_summarize = str_summarize.replace("\'", "")
    str_parameter = str_parameter.replace("\'", "")
    str_example   = str_example.replace("\'", "")
    
    return retVal, str_summarize, str_parameter, str_example

main_html = get_request(jquery_url, jquery_host, {}) # jquery host
if main_html is not None:
    # crawl jquery main page
    soup = BeautifulSoup(main_html, 'lxml')
    wraper = soup.find('div', class_='main-wraper') # select 

    col_list = wraper.find('div', id = 'col-list')
    col_items = col_list.find_all('div', class_= 'col-item') # items
    cnt = 0
    insert_sql = "insert into crawl_jquery(attribute, first_class, second_class, ret_value, summarize, parameter, example) values"
    for col in col_items:
        first_text =  col.h2.text

        ul = col.find_all('ul') # ul 
        is_first = 1
        for u in ul:
            if is_first > 0: # parse
                lis = u.find_all('li')
                for li in lis:
                    if li.h3 is not None:
                        second_text = li.h3.text
                        thirds = li.ul.find_all('li')
                        for th in thirds:
                            attribute_url = '%s/%s' % (jquery_host, th.a.attrs['href'])
                            attribute = th.a.text # attribute
                            print attribute
                            retVal, str_summarize, str_parameter, str_example = parse_jquery_attribute(attribute_url)
                            cnt += 1
                            insert_sql += "(\'%s\', \'%s\', '%s', '%s', '%s', '%s', '%s')" % \
                                    (attribute, first_text, second_text, retVal, str_summarize, str_parameter, str_example)
                            if cnt % 10 == 0:
                                res = db_fetcher.commit_sql_cmd(insert_sql, "mysql_duyi_core")
                                insert_sql = "insert into crawl_jquery(attribute, first_class, second_class, ret_value, summarize, parameter, example) values"
                            else:
                                insert_sql += ','


                is_first = -1
            else:
                break

    insert_sql = insert_sql[:len(insert_sql)-1] # process last ','
    db_fetcher.commit_sql_cmd(insert_sql, "mysql_duyi_core")