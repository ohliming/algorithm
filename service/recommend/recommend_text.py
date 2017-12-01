# -*- coding:utf-8 -*-

"""
Created on Fri Oct 30 16:12:48 2015

@author: liming
@other :
    测试环境(可用)：data-internal.test.36tr.com/seo?cmd=extractKeyWords&article=xxxx
    线上环境(可用)：data-internal.36tr.com/seo?cmd=extractKeyWords&article=xxxx
"""
from __future__ import division

from urllib import urlencode
import redis
import urllib
import json
import cStringIO

import sys,os,copy,re,math,MySQLdb
import time,datetime

sys.path.append('../')
sys.path.append('../../')
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../seo')))
from common.db_fetcher import DataBaseFetcher
from seo_extractor import SeoExtractor

term_weight_threshold = 1.5
kForwardIndexRedisKey = 'DATA_MdFI'
kRevertIndexRedisKey = 'DATA_MdRI'

class TextAnalysis(object):
    media_dict = None
    entity_dict = None
    seo_extractor = SeoExtractor('../seo/com_df_idf')

    def __init__(self,mysql_fetcher=None,handler_redis=None):
        self.mysql_fetcher = mysql_fetcher
        if mysql_fetcher is None:
            self.mysql_fetcher = DataBaseFetcher()
        self.handler_redis = handler_redis
        if handler_redis is None:
            self.handler_redis = redis.Redis(host='1c34f95e1b12494b.m.cnbja.kvstore.aliyuncs.com',password='f9p3iUTOj91fO1ZGVglr', port=6379, db=5)
        self.load_entity_dict()

    def set_media_id(self,media_id):
        self.media_dict = self.get_media_dict(media_id)

    # 通过media_id 与向量字典关联
    def set_media_dict(self,media_id,forward_index_dict):
        if media_id in forward_index_dict:
            self.media_dict = forward_index_dict[media_id]
        else:
            self.media_dict = self.get_media_dict(media_id)

    def load_entity_dict(self):
        self.entity_dict = set()
        # handle company
        company_file = '../../company_recognize/com_name2id.txt'
        with open(company_file) as com_f:
            for line in com_f:
                tokens = line.strip().split('\t')
                if len(tokens) != 2:
                    continue
                self.entity_dict.add(tokens[0])

        # handle industry
        db_industry = self.mysql_fetcher.get_sql_result('select distinct name from dict_industry','mysql_crm')
        for row_industry in db_industry:
            self.entity_dict.add(row_industry[0])

        # handle organization
        db_organization = self.mysql_fetcher.get_sql_result('select distinct name_abbr from organization','mysql_crm')
        for row_organization in db_organization:
            self.entity_dict.add(row_organization[0])

    # 获取文章关键词-权重值列表
    def get_article_weight(self,media_id):
        response_list = self.seo_extractor.extract_article(media_id, title_weight=2, title_coeff=1.4)
        if response_list is None or len(response_list) == 0:
            return {}

        keyword_dict = {} # result dict
        for keyword,weight in response_list:
            if keyword in self.entity_dict:
                weight *= 1.4
            keyword_dict[unicode(keyword, 'utf8')] = weight

        keyword_dict = {key:value for key,value in keyword_dict.items() if value > term_weight_threshold}
        if len(keyword_dict) < 5:
            keyword_dict = {key:value for key,value in keyword_dict.items() if value > 0.68 * term_weight_threshold}

        return keyword_dict

    # 删除历史记录的文本向量
    def delete_redis_text(self,update_time_range):
        db_data = self.mysql_fetcher.get_sql_result("select id from kr_articles where publish < \'%s\'" % update_time_range, 'mysql_insight')
        for i in range(len(db_data)):
            media_id = db_data[i][0]
            str_key = '%s_%s' % (kForwardIndexRedisKey,media_id)
            self.handler_redis.delete(str_key)

    # 计算两个向量的余弦相似度
    def cos_similarity(self,v1,v2):
        if len(v1) != len(v2): # 向量维数必须相等
            return 0.0

        fen_divisor = 0.0 # 除数
        dividend_v1 = 0.0 # 被除数
        dividend_v2 = 0.0 # 被除数
        for pos in range(len(v1)):
            fen_divisor += v1[pos] * v2[pos]
            dividend_v1 += v1[pos] ** 2
            dividend_v2 += v2[pos] ** 2

        fen_dividend = math.sqrt(dividend_v1) *math.sqrt(dividend_v2)
        return (fen_divisor/fen_dividend if fen_dividend > 0.0 else 0.0)

    # 初始化文本向量
    def init_vector(self,vector1,dict_weight):
        if len(vector1) < 1:
            return []

        v1 = [] # 文本向量vector
        for pos in range(len(vector1)):
            if vector1[pos] in dict_weight:
                v1.append(dict_weight[vector1[pos]])
            else:
                v1.append(0.0)

        return v1

    # 重建media文本信息的正排，并更新redis
    def media_text_to_forward_index(self,media_id):
        # 获取需要的字符串
        dict_term_weight = self.get_article_weight(media_id)

        # 存入redis 文本关键词数据 key = media_id
        str_key = '%s_%s' % (kForwardIndexRedisKey,media_id)
        str_value = json.dumps(dict_term_weight)
        self.handler_redis.set(str_key,str_value)

        return dict_term_weight

    # 重建update_time_range时间之后的media文本信息的倒排，并更新redis
    def media_text_to_revert_index(self,update_time_range):
        #self.delete_redis_text(update_time_range)

        # 更新redis
        db_data = self.mysql_fetcher.get_sql_result('select id from kr_articles where publish >=\'%s\'' % update_time_range, 'mysql_insight')
        if len(db_data) < 1:
            return None

        revert_index_dict = {} # 倒排索引字典
        n_count = 1
        for i in range(len(db_data)):
            media_id = db_data[i][0]
            # self.cache_media_relate(media_id,update_time_range)

            # 缓存倒排索引
            media_dict = self.get_media_dict(media_id)
            for term,weight in media_dict.items():
                if term not in revert_index_dict:
                    revert_index_dict[term] = {}
                revert_index_dict[term][media_id] = weight

        str_key = kRevertIndexRedisKey
        str_value = str(revert_index_dict)
        self.handler_redis.set(str_key,str_value)

        return revert_index_dict

    # 获取正排
    def get_media_dict(self,media_id):
        media_dict = None
        str_key = '%s_%s' % (kForwardIndexRedisKey,media_id)
        str_value = self.handler_redis.get(str_key)
        # 判断redis 数据库中是否包含media_id 信息
        if str_value is None:
            media_dict = self.media_text_to_forward_index(media_id)
        else:
            media_dict = json.loads(str_value)
        return media_dict

    # 用倒排计算文本相似度
    def calc_simi_using_revert_index(self,revert_index_dict,meta_dict):
        if revert_index_dict is None:
            return {}

        dict_molecule =     {} # 分子对象
        dict_denominator1 = 0.0 # 分母对象1

        result_dict = {} # 结果集字典 key = media_id
        media_list = []
        # 计算所有的d 与该文档的相似度的分子分母
        for term,weight in self.media_dict.items():
            dict_denominator1 += weight**2
            if term not in revert_index_dict:
                continue
            doc_weight_list = revert_index_dict[term]
            for media_id in doc_weight_list:
                # 获取相关列表
                media_list.append(media_id)

                if media_id in dict_molecule:
                    dict_molecule[media_id] += weight*doc_weight_list[media_id]
                else:
                    dict_molecule[media_id] = weight*doc_weight_list[media_id]

        for media_id in media_list:
            if media_id not in meta_dict:
                continue

            x,y,dict_denominator2 = meta_dict[media_id] # 分母对象2
            fen_dividend = math.sqrt(dict_denominator1) * math.sqrt(dict_denominator2)
            result_dict[media_id] = dict_molecule[media_id]/fen_dividend if fen_dividend > 0.0 else 0.0

        return result_dict

    # 构造相似向量
    def dict_merge2list(self,d_media,d_compare):
        vec_words = []
        b_similarity = False

        for media_key in d_media:
            if media_key in d_compare:
                vec_words.append(media_key)
                b_similarity = True

        return vec_words,b_similarity

    # 用正排计算文本相似度
    def calculate_text_weight(self,compare_id,forward_index_dict):
        # 判断该向量是否存在
        if self.media_dict is None:
            return 0.0

        if compare_id in forward_index_dict:
            compare_dict = forward_index_dict[compare_id]
        else:
            compare_dict = self.get_media_dict(compare_id)

        # 判断比较向量是否存在
        if compare_dict is None:
            return 0.0

        vec_words,b_similarity = self.dict_merge2list(self.media_dict,compare_dict)
        if b_similarity == False:
            return 0.0

        v1 = self.init_vector(vec_words,self.media_dict)
        v2 = self.init_vector(vec_words,compare_dict)

        # 计算余弦相似度值
        d_result = self.cos_similarity(v1,v2)
        return d_result

def main():
    start = time.clock()
    m_text_analysis = TextAnalysis()
    keywords = m_text_analysis.get_article_weight(5044606)
    print '\t'.join(map(lambda x: '%s:%s' % (x[0],x[1]), keywords.items()))
    end = time.clock()
    print ("read: %f s" % (end - start))

if __name__=='__main__':
    main()
