#!/usr/bin/env python
#coding=utf8
'''
@author: cuiyan
@updated: wanli
'''
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('../../')
import json,math,MySQLdb
import re
from segment.chinese_segmenter import ChineseSegmenter
from common.db_fetcher import DataBaseFetcher

if __name__ == '__main__':
    global_words= {}
    global_count = 0

    ## 0.init segment and mysql
    segmenter = ChineseSegmenter('segment/data', 'segment/benz_stop_words_ch+en.gbk')
    fetcher = DataBaseFetcher()

    ## 1.fetch com content
    db_data = fetcher.get_sql_result("select id,name,full_name,brief,intro from company where status in (1,2) and is_deleted=0", "mysql_crm")
    for row in db_data:
        doc_words = {}
        for column in row[1:]:
            terms = segmenter.segment(column)
            for term in terms:
                if len(term.decode('utf8')) < 2: continue
                doc_words[term] = 1
        for term,tf in doc_words.items():
            if global_words.has_key(term):
                global_words[term] += 1
            else:
                global_words[term] = 1
        global_count += 1

    ## 2.fetch kr_articles content
    db_data = fetcher.get_sql_result("select id,article_json from insight.kr_articles", "mysql_insight")
    doc_len = 0
    doc_num = 0
    for row in db_data:
        doc_num += 1
        doc_words = {}
        json_str = row[1].replace('\r','').replace('\n','').replace('\\','<>').replace('<>"','\\"')
        article_arr = []
        try:
            article_obj = json.loads(json_str,strict=False)
            article_arr.append(article_obj['title'])
            content = re.sub('<[^>]+>', '', article_obj['content'])
            article_arr.append(content)
        except:
            continue
        for column in article_arr:
            terms = segmenter.segment(column)
            doc_len += len(terms)
            for term in terms:
                if len(term.decode('utf8')) < 2: continue
                doc_words[term] = 1

        for term,tf in doc_words.items():
            if global_words.has_key(term):
                global_words[term] += 1
            else:
                global_words[term] = 1
        global_count += 1

    ## 3.calc idf
    for term,df in global_words.items():
        if df < 3: continue
        idf = math.log(1.0 * global_count / df) / math.log(1.0 * global_count)
        print '%s\t%s\t%.4f' % (term, df, idf)

    print 'GlobalDocLenAvg\t3\t%0.4f' % (1.0 * doc_len / doc_num)
