#!/usr/bin/env python
#coding=utf8
from __future__ import division

import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
import json,math,MySQLdb,datetime,time
import similary_question as sq

from recommend import RecommendQuestion
from common.db_fetcher import DataBaseFetcher

recommend = RecommendQuestion() # object
db_fetcher = DataBaseFetcher()

question_list = [] # set

rows = db_fetcher.get_sql_result("select question_id from error_question_log", 'mysql_logdata')
for row in rows:
    qid = row[0]
    question_list.append(qid)

def getQuestionWords(question_list): # 
    dict_question_info = {}
    lSet = int(len(question_list) / 1000) + 1 
    start, end = 0, 0
    for i in range(1, lSet):
        end = i * 1000
        if end > len(question_list): end = len(question_list)
        str_question = ','.join([str(x) for x in question_list[start:end] ])
        str_sql = "select c.id, c.subject_id, t.type_id,t.struct_id, c.json_data, c.difficulty, c.question_type from neworiental_v3.entity_question c left \
            join neworiental_v3.entity_question_type t on t.type_id=c.question_type_id where c.id in (%s) and subject_id = 4" % str_question

        print str_sql
        s_rows = db_fetcher.get_sql_result(str_sql,'mysql_logdata')
        for row in s_rows:
            question, subject_id, type_id, struct_id, json_data, difficulty, question_type = row
            if json_data !='' and json_data != 'None' and json_data != None:
                keywords, res = sq.predict(question, subject_id, type_id, struct_id, json_data)
                dict_question_info[question] = keywords, res, question, subject_id, type_id, struct_id, difficulty, question_type

        start = end

    return dict_question_info

dict_question_info = getQuestionWords(question_list) # insert 
for key in dict_question_info:
    keywords, res, question, subject_id, type_id, struct_id, difficulty, question_type = dict_question_info[key]
    if question_type == '选择题':
        qtype = 1
    elif question_type == '填空题':
        qtype = 2
    else:
        qtype = 3

    target_questions = recommend.getEsResult(question, res, keywords, difficulty, qtype, [], 4)
    str_target = ','.join([str(x) for x in target_questions])
    db_fetcher.commit_sql_cmd("update error_question_log set res = '%s' where question_id = %s" % (str_target, question), 'mysql_logdata') # update
