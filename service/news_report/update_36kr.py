#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os,json,datetime,re,time
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
from common.db_fetcher import DataBaseFetcher

db_fetcher = DataBaseFetcher()

if __name__=="__main__":
    # update news_report company
    now_time = datetime.datetime.now()
    yes_time = now_time + datetime.timedelta(days=-1)
    yes_date = yes_time.strftime('%Y-%m-%d')
    db_data = db_fetcher.get_sql_result('select id, article_json, publish from kr_articles where publish = \'%s\'' % yes_date, 'mysql_insight')
    for pos in range(len(db_data)):
        kid = str(db_data[pos][0])
        try:
            article_json = str(db_data[pos][1])
            article_obj = json.loads(article_json, strict=False)

            url   = 'http://36kr.com/p/%s.html' %  kid
            title =  article_obj['title']
            source = "36Kr"
            publish_date =  '%s 00:00:00' % str(db_data[pos][2])
            domain = '36kr.com'
            content_html = article_obj['content'].encode('utf-8') if 'content' in article_obj and article_obj['content'] else ''
            content = re.sub('<[^>]+>', '', content_html)

            insert_sql = "insert into news_report(url, publish_date, title, content, source, domain, aid) values(\'%s\', \'%s\', \'%s\', \'%s\', \'%s\',\'%s\',%s)" % (url, publish_date, title, content, source, domain, kid)
            db_fetcher.commit_sql_cmd(insert_sql, 'mysql_insight')
        except:
            print 'the error article id :%s' % kid
        
