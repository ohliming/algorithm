# -*- coding:utf-8 -*-
from __future__ import division

import sys,copy,json,re,heapq,math,MySQLdb
import time,datetime
import httplib,redis

sys.path.append('../')
sys.path.append('../../')

from common.db_fetcher import DataBaseFetcher
from recommend_text import TextAnalysis

text_weight = 80.0
time_weight = 10.0
company_weight = 20.0
kTimeRange = 123
kRecommendRedisKey = 'DATA_MdRcmd'

class  RecommArticles(object):
    def __init__(self,mysql_fetcher=None,handler_redis=None):
        self.mysql_fetcher = mysql_fetcher
        if mysql_fetcher is None:
            self.mysql_fetcher = DataBaseFetcher()
        self.handler_redis = handler_redis
        if handler_redis is None:
            self.handler_redis = redis.Redis(host='1c34f95e1b12494b.m.cnbja.kvstore.aliyuncs.com',password='f9p3iUTOj91fO1ZGVglr',port=6379, db=5)

        self.m_text_analysis = TextAnalysis(self.mysql_fetcher,self.handler_redis)

    def get_related_company(self,media_id):
        db_company = self.mysql_fetcher.get_sql_result("select a.similar_weight from company_similarity a \
                join media_report b on b.reported_com = a.id where b.aid =%s and source=\'\' limit 1" % media_id,'mysql_insight')
        if len(db_company) == 0 or len(db_company[0][0]) == 0:
            return {}

        # 获取权重公司字典
        list_company = json.loads(db_company[0][0])
        dict_company = {}
        for com in list_company:
            dict_company[com[0]] = com[1]
        return dict_company

    # 推荐文章
    def recommend_media(self,media_id,publish_date,update_time_range,forward_index_dict,revert_index_dict,meta_dict,recommend_size):
        self.m_text_analysis.set_media_dict(media_id,forward_index_dict)

        dict_media = {} # 媒体列表

        # 获取公司和文本相似度相近字典
        dict_company = self.get_related_company(media_id)
        dict_text_result = self.m_text_analysis.calc_simi_using_revert_index(revert_index_dict, meta_dict)

        for compare_id in dict_text_result:
            if media_id == compare_id:
                continue

            # 文本相关度评分
            #text_score = text_weight * self.m_text_analysis.calculate_text_weight(compare_id,forward_index_dict)
            text_score = text_weight * dict_text_result[compare_id]

            compare_publish_date = None
            reported_com = None
            if compare_id in meta_dict:
                compare_publish_date,reported_com,text_sum_quares = meta_dict[compare_id]
            # 计算时间评分
            time_score = 0.0
            if compare_publish_date is not None:
                gaussian_param = -(abs((publish_date-compare_publish_date).days)/10.0)**2/2.0
                gaussian_value = math.exp(gaussian_param)
                time_score = time_weight * gaussian_value
            # 计算公司评分
            campany_score = 0.0
            if reported_com is not None:
                if reported_com in dict_company:
                    com_value = 1.0 if dict_company[reported_com] > 1.0 else dict_company[reported_com]
                    campany_score = company_weight * com_value

            dict_media[compare_id] = campany_score + time_score + text_score
            #print compare_id,text_score,time_score,campany_score

        # 返回media_id 列表信息
        list_rank = heapq.nlargest(recommend_size, dict_media.items(), key=lambda x:x[1])

        # 结果列表
        list_result = ['%s:%s' % (str(x[0]),str(x[1])) for x in list_rank ]
        str_key = '%s_%s' % (kRecommendRedisKey, media_id)
        str_value = ','.join(list_result)
        self.handler_redis.set(str_key,str_value)

        return list_result

    # 获取候选集文本正排和倒排
    def load_media_dict(self,update_time_range):
        # 正排
        forward_index_dict = {}
        meta_dict = {}

        db_data = self.mysql_fetcher.get_sql_result("select kr_articles.id,kr_articles.publish,media_report.reported_com from kr_articles left join media_report on kr_articles.id=media_report.aid where kr_articles.publish >='%s'" % update_time_range, "mysql_insight")
        for row in db_data:
            media_id, publish, reported_com = row
            media_dict = self.m_text_analysis.get_media_dict(media_id)
            forward_index_dict[media_id] = media_dict
            text_sum_quares = 0.0
            for weight in media_dict.values():
                text_sum_quares += weight**2
            time_publish = time.strptime(str(publish),'%Y-%m-%d')
            datetime_publish = datetime.datetime(time_publish[0],time_publish[1],time_publish[2])
            meta_dict[media_id] = (datetime_publish, reported_com, text_sum_quares)

        # 倒排
        revert_index_dict = self.m_text_analysis.media_text_to_revert_index(update_time_range)

        return forward_index_dict,revert_index_dict,meta_dict

    def delete_redis_media(self,update_time_range):
        db_data = self.mysql_fetcher.get_sql_result("select id from kr_articles where publish < \'%s\'" % update_time_range, 'mysql_insight')
        for pos in range(len(db_data)):
            media_id = db_data[pos][0]
            str_key = '%s_%s' % (kRecommendRedisKey, media_id)
            self.handler_redis.delete(str_key)

    def load_redis_media(self,update_time_range,forward_index_dict,revert_index_dict,meta_dict,recommend_size):
        # self.delete_redis_media(update_time_range)

        count = 1
        db_data = self.mysql_fetcher.get_sql_result("select id,publish from kr_articles where publish >=\'%s\'" % update_time_range, 'mysql_insight')
        for pos in range(len(db_data)):
            media_id = db_data[pos][0]
            publish = db_data[pos][1]
            time_publish = time.strptime(str(publish),'%Y-%m-%d')
            datetime_publish = datetime.datetime(time_publish[0],time_publish[1],time_publish[2])
            list_result = self.recommend_media(media_id,datetime_publish,update_time_range,forward_index_dict,revert_index_dict,meta_dict,recommend_size)
            print media_id,count,len(list_result)
            count += 1

    # 查询并返回缓存或临时结果
    def get_cache_or_temp(self,media_id,recommend_size):
        is_cached = False
        list_result = None
        str_key = '%s_%s' % (kRecommendRedisKey, media_id)
        str_media = self.handler_redis.get(str_key)
        if str_media is None:
            pass
            #list_result = self.get_latest_articles(recommend_size)
        else:
            is_cached = True
            list_result = map(lambda x: x.split(':')[0], str_media.split(','))
        return list_result,is_cached

    # 获取最新文章列表
    def get_latest_articles(self,recommend_size):
        conn = httplib.HTTPConnection("", 80, True, 20)
        retry = 3
        while retry > 0:
            try:
                conn.request("GET", "/p/api/post?client_id=ef89a88d739f4f07b85b894d9fbf6c5d49e98180&client_key=9686c23cd8ee1d865e29204fb869c3796d1d73b1&state=published&page=%s&per_page=%s" % (1, recommend_size))
                res = conn.getresponse()
                json_str = res.read()
                json_articles = json.loads(json_str)
                return map(lambda x: str(x['id']), json_articles['data']['data'])
            except:
                retry -= 1
        return None

def main():
    today = datetime.date.today()
    update_time_range = today - datetime.timedelta(days=kTimeRange)
    recommend_size = 6
    recom = RecommArticles()

    week_num = int(time.strftime("%w"))
    if week_num == 0:
        print 'Clear before Batch Calculation'
        recom.m_text_analysis.delete_redis_text(today)
        recom.delete_redis_media(today)

    print 'Batch Calculation'
    start = time.clock()

    forward_index_dict,revert_index_dict,meta_dict = recom.load_media_dict(update_time_range)
    recom.load_redis_media(update_time_range,forward_index_dict,revert_index_dict,meta_dict,recommend_size)

    end = time.clock()
    print ("Time Used: %f s" % (end - start))

if __name__=='__main__':
    main()
