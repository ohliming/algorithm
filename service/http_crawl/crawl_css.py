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
db_fetcher = DataBaseFetcher()

css_host = 'http://www.css88.com/' # css host
css_url = 'http://www.css88.com/book/css/' # main page

def parse_tag_syntax(css_syntax):
    try: # css
        describe_title = css_syntax.h2.text # title
        # new_str = re.sub('[^\w\u4e00-\u9fff]+', '','江苏 » 无锡市:婚礼司仪roger')
        items = css_syntax.div.find_all('p') # p
        content = '' # content
        for p in items: content  += '\n' + p.text

        content = content.replace("\'", "").strip() # do something
        return content # res
    except:
        return ''

def parse_tag_value(css_value):
    try: # css
        items = css_value.div.dl.find_all('dt')
        values = css_value.div.dl.find_all('dd')

        content = ''
        min_len = min(len(items), len(values)) # min len
        for i in range(0, min_len):
            content += '%s%s\n' % (items[i].text, values[i].text)

        content = content.replace("\'", "").strip() # value
        return content # res
    except:
        return ''

def parse_tag_intro(css_intro): # intro
    try:
        content = css_intro.div.strong.text
        items = css_intro.div.ul.find_all('li')
        for item in items:
            content += item.text + '\n'

        content = content.replace("\'", "").strip() # intro
        return content # intro
    except:
        return ''

def parse_tag_example(css_example):
    try:
        content = str(css_example.div.textarea)
        content = content.replace("<textarea cols=\"90\" rows=\"10\">","")
        content = content.replace("<meta charset=", "<html lang=\"zh-cmn-Hans\"><head> <meta charset=")
        content = content.replace("</style>", "</style></head><body>")
        content = content.replace("</textarea>", "/body></html>")

        content = content.replace("\'", "").strip() # example
        return content
    except:
        return ''

def parse_css_tag(css_tag, tag_url): # css
    css_html = get_request(tag_url, css_host, {}) # get htttp request
    if css_host is not None:
        css_soup = BeautifulSoup(css_html, 'lxml')
        css_section = css_soup.find('section',id = 'bd') # css

        # syntax
        css_syntax = css_section.find('section', id='syntax') 
        syntax_content = parse_tag_syntax(css_syntax)

        css_value = css_section.find('section', id= 'value')
        value_content = parse_tag_value(css_value)

        css_intro = css_section.find('section', id = 'intro')
        intro_content = parse_tag_intro(css_intro)

        css_example = css_section.find('section', id = 'example')
        example_content = parse_tag_example(css_example) # example

    return syntax_content, value_content, intro_content, example_content


main_html = get_request(css_url, css_host, {}) # css host
if main_html is not None:
    # crawl css main page
    soup = BeautifulSoup(main_html, 'lxml')
    section = soup.find('section',id = 'bd')

    contents = section.find_all('section')
    insert_sql = "insert into crawl_css(tag, classification, syntax, value, intro, example) values"
    cnt = 0
    for item in contents: # items
        try:
            item_title = str(item.h2.a.text)
            item_url = '%s%s' % (css_url, item.h2.a.attrs['href'])
            arr_li = item.div.ul.find_all('li') # get li tag
            for li in arr_li:
                css_tag = li.a.text
                tag_url = '%s%s' % (css_url, li.a.attrs['href'])
                syntax_content, value_content, intro_content, example_content = parse_css_tag(css_tag, tag_url)
                insert_sql += "(\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')" % (css_tag, item_title, syntax_content, value_content, intro_content, example_content)
                cnt += 1
                if cnt % 5 == 0:
                    res = db_fetcher.commit_sql_cmd(insert_sql, "mysql_duyi_core")
                    insert_sql = "insert into crawl_css(tag, classification, syntax, value, intro, example) values"
                else:
                    insert_sql += ','
        except:
            continue

    insert_sql = insert_sql[:len(insert_sql)-1] # process last ','
    db_fetcher.commit_sql_cmd(insert_sql, "mysql_duyi_core")

