# -*- coding: utf-8 -*-
from __future__ import division
import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
import json, math, MySQLdb
from cStringIO import StringIO
import httplib, urllib,urllib2,gzip,re,math,numpy
from common.db_fetcher import DataBaseFetcher
from common.cache_helper import CacheHelper

class QualityQuestion(object):
    """docstring for QualityQuestion"""
    def __init__(self):
        self.db_fetcher =  DataBaseFetcher() # mysql handle
        self.redis_cache = CacheHelper('127.0.0.1', 6379, 1 , '') # redis
        self.dict_simple_science, self.dict_simple_art = self.getSimpleQustion()

        self.dict_question_topic = self.getQuestionTopic()
        self.dict_topic = self.getTopicDict()

    def getQuestionTopic(self, save_file = 'topic.txt'):
        dict_question_topic = {}
        max_num = 0
        with open(save_file) as handle_f:
            for line in handle_f:
                arr = line.strip().split('\t')
                if len(arr) != 3: continue
                tid, question_id, topic_id = arr[0], long(arr[1]), int(arr[2])
                if question_id not in dict_question_topic:
                    dict_question_topic[question_id] = set()

                dict_question_topic[question_id].add(topic_id)
                max_num = tid

        sql = "select id, question_id, topic_id from neworiental_v3.link_question_topic where id > %s" % max_num
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        with open(save_file, 'a') as write_f:
            for row in rows:
                tid, question_id, topic_id = row
                if question_id not in dict_question_topic:
                    dict_question_topic[question_id] = set()

                dict_question_topic[question_id].add(topic_id)
                write_f.write('%s\t%s\t%s\n' % (tid, question_id, topic_id))
        
        return dict_question_topic

    def getTopicDict(self):
        dict_topic = {}
        sql = "select id, `name` from neworiental_v3.entity_topic where subject_id = 4"
        rows = self.db_fetcher.get_sql_result(sql,'mysql_logdata')
        for row in rows:
            topic_id, name = row
            topic_id = int(topic_id)
            dict_topic[topic_id] = name

        return dict_topic

    def makeSet2Dict(self, set_simple):
        dict_simple = {}
        for item in set_simple:
            arr = item.split('\t')
            qid, question_type, json_data = arr[0], arr[1], arr[2]
            qid = long(qid)
            dict_simple[qid] = question_type, json_data

        return dict_simple

    def getSimpleQustion(self):
        dict_simple_science = {}
        dict_simple_art = {}

        is_redis = self.redis_cache.exists('62951166961') and self.redis_cache.exists('62951084550')
        if  is_redis:
            # science
            set_simple_science = self.redis_cache.smembers('62951166961')
            dict_simple_science = self.makeSet2Dict(set_simple_science)
            # art
            set_simple_art = self.redis_cache.smembers('62951084550')
            dict_simple_art = self.makeSet2Dict(set_simple_art)
        else:
            sql = "SELECT id, question_type, json_data, upload_id from neworiental_v3.entity_question where upload_id in (62951166961, 62951084550) and json_data !=\'\' "
            rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
            for row in rows:
                qid, question_type, json_data, upload_id = row
                upload_id = str(upload_id)
                json_data = json_data.replace('\t', '')
                if upload_id == '62951166961': # students majored in science
                    dict_simple_science[qid] = question_type, json_data
                elif upload_id == '62951084550':
                    dict_simple_art[qid] = question_type, json_data

                str_content = '%s\t%s\t%s' % (qid, question_type, json_data)
                self.redis_cache.sadd(upload_id, str_content)

        return dict_simple_science, dict_simple_art

    def getTopicSimpleQuestion(self):
        dict_topic_question = {}
        for qid in self.dict_simple_art:
            if qid in self.dict_question_topic:
                set_topic = self.dict_question_topic[qid]
                for topic in set_topic:
                    if topic not in dict_topic_question:
                        dict_topic_question[topic] = set()

                    dict_topic_question[topic].add(qid)

        for topic in dict_topic_question:
            set_topic = dict_topic_question[topic]
            str_content = '\t'.join([str(x) for x in set_topic])
            print '%s\t%s\t%s' % (topic, self.dict_topic[topic], str_content)

if __name__=='__main__':
    print 'this is quality question!'
    quality = QualityQuestion() # 
    quality.getTopicSimpleQuestion()