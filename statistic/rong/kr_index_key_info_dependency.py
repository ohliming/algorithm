#!/usr/bin/env python
#coding=utf8
'''
@author: cuiyan
'''
import sys,MySQLdb
from info_proc import ComInfoProc

if __name__ == '__main__':
    online_db = MySQLdb.connect(host='rds60i0820sk46jfsiv0.mysql.rds.aliyuncs.com',user='readop',passwd='9ewF5OPp38cvHxUZ',db='krplus2')
    online_db.set_character_set('utf8')
    online_db_cursor = online_db.cursor()
    spider_db = MySQLdb.connect(host='rds60i0820sk46jfsiv0.mysql.rds.aliyuncs.com',user='analyst',passwd='JxM2sdUgVgKXMGOg',db='insight')
    spider_db.set_character_set('utf8')
    spider_db_cursor = spider_db.cursor()
    spider_db_cursor.execute("select app_id,app_name,app_url,type_name,rank_list from ann9_rank_info")

    base_filter = "status>1 and is_deleted=0 and operation_status=0 and length(brief)>0 and length(intro)>0 and address1 is not null"
    online_db_cursor.execute("select id,website,iphone_appstore_link,industry,finance_phase from company where %s" % base_filter)
    db_data = online_db_cursor.fetchall()
    com_total = 0
    com_tag = 0
    com_tag_total = 0
    com_website = 0
    com_website_top = 0
    com_appstore = 0
    com_appstore_top = 0
    com_presentable_krindex = 0
    com_industry = 0
    com_fund = 0
    for row in db_data:
        com_total += 1
        online_db_cursor.execute("select count(*) from company_tag where cid=%s" % row[0])
        com_tags = online_db_cursor.fetchall()[0][0]
        if com_tags > 0:
            com_tag += 1
            com_tag_total += com_tags
        is_presentable_website = False
        is_presentable_appstore = False
        if len(row[1]) > 0:
            com_website += 1
            site = ComInfoProc.url_stemming(row[1])
            if len(site) > 0:
                spider_db_cursor.execute("select count(*) from alexa_rank_info where site='%s'" % site)
                if spider_db_cursor.fetchall()[0][0] > 0:
                    com_website_top += 1
                    is_presentable_website = True
        if len(row[2]) > 0:
            com_appstore += 1
            app_id = ComInfoProc.extract_appid(row[2])
            if len(app_id) > 0:
                spider_db_cursor.execute("select count(*) from ann9_rank_info where app_id=%s" % app_id)
                if spider_db_cursor.fetchall()[0][0] > 0:
                    com_appstore_top += 1
                    is_presentable_appstore = True
        if is_presentable_website or is_presentable_appstore:
            com_presentable_krindex += 1
        if row[3] != None and row[3] != 0:
            com_industry += 1
        if row[4] != 0:
            com_fund += 1
        else:
            online_db_cursor.execute("select count(*) from past_finance where cid=%s" % row[0])
            if online_db_cursor.fetchall()[0][0] > 0:
                com_fund += 1
    online_db.close()
    spider_db.close()
    print '总公司数:\t%s' % com_total
    print '总Website数:\t%s (%.2f%%)' % (com_website, 100.0 * com_website/com_total)
    print 'Top列表可见Website数:\t%s (%.2f%%)' % (com_website_top, 100.0 * com_website_top/com_total)
    print '总App数:\t%s (%.2f%%)' % (com_appstore, 100.0 * com_appstore/com_total)
    print 'Top列表可见App数:\t%s (%.2f%%)' % (com_appstore_top, 100.0 * com_appstore_top/com_total)
    print '氪指数可见打分数:\t%s (%.2f%%)' % (com_presentable_krindex, 100.0 * com_presentable_krindex/com_total)
    print '公司标签覆盖率:\t%s (%.2f%%)' % (com_tag, 100.0 * com_tag/com_total)
    print '公司平均标签数:\t%.2f' % (1.0*com_tag_total/com_total)
    print '公司行业覆盖率:\t%s (%.2f%%)' % (com_industry, 100.0 * com_industry/com_total)
    print '公司融资轮次覆盖率:\t%s (%.2f%%)' % (com_fund, 100.0 * com_fund/com_total)

