#!/usr/bin/env python
#coding=utf8
from __future__ import division

import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
import json,math,MySQLdb,datetime
import similary_question as sq

from recommend import RecommendQuestion
from common.db_fetcher import DataBaseFetcher

class Report(object):
    """docstring for Report"""
    def __init__(self, update_time = '2017-11-01 00:00:00'):
        # do something inits
        self.db_fetcher = DataBaseFetcher()
        self.dict_content_answer = {} # error content
        self.curr_time = datetime.datetime.now()

        self.update_time = update_time # update time
        self.recommend = RecommendQuestion()

        self.dict_realtion_quesion, self.dict_question_num, self.dict_question_score = self.getRelationQuestion()
        self.dict_parent_quesion = self.getChildQuestion()
        self.dict_question_diff = self.getRightDifficulty()
        self.dict_point, self.dict_topic_point   = self.getPoints()

        self.dict_students = self.getStudentId()
        self.dict_student_score, self.dict_student_records = {}, {x:[] for x in self.dict_students }

        self.exam_list_records, self.practice_list_records = self.getExerciseRecord() #records

        # dict
        self.dict_question_types = {1:'选择题',2:'填空题',4:'简答题', 6:'综合题', 17:'计算题', 44:'证明题'}
        self.dict_question_difficulty = { 1:'易', 2:'中',3:'难', 4:'极难'}  # １：易　２：中　３：难　４：极难

        # feedback
        self.dict_students_resource = self.getStudentResource() # resource

    def getExerciseRecord(self):
        exam_list_records = []
        practice_list_records = []
        sql = "select a.question_id, a.student_id, a.ret_num, a.submit_answer, a.submit_time, b.question_type from entity_student_exercise a join \
                neworiental_v3.entity_question b on b.id = a.question_id where a.submit_time > \'%s\' and a.exercise_source = 6" % ( self.update_time )

        dict_is_choice = {}
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        for row in rows:
            question, student_id, ret, answer, submit_time, question_type = row
            student_id = long(student_id)

            if answer == 'null' or answer == 'None' or answer == '' or answer == 'NULL' or answer == None or len(answer) == 0: continue
            if question in self.dict_realtion_quesion:
                exam_list_records.append([question, student_id, ret, answer, submit_time, question_type])

                self.dict_student_records[student_id].append([question, student_id, ret, answer, submit_time, question_type])
                self.dict_content_answer['%s_%s' % (question, student_id)] = answer
            elif question in self.dict_parent_quesion:
                dict_content = self.dict_parent_quesion[question]
                parent_question_id = dict_content['parent_id']

                rank = dict_content['rank']
                link_question_id, link_point_id, question_num, difficulty, question_exercise_id, question_type = self.dict_realtion_quesion[parent_question_id]
                if  question_num >= 17 and question_num <= 21:
                    if rank == 1: 
                        exam_list_records.append([parent_question_id, student_id, ret, answer, submit_time, question_type])
                        self.dict_student_records[student_id].append([parent_question_id, student_id, ret, answer, submit_time, question_type])
                    elif rank == 2:
                        self.dict_content_answer['%s_%s'%(parent_question_id, student_id)] = answer
                elif question_num >= 22 and question_num <= 23:
                    key = '%s_%s' % (parent_question_id, student_id)
                    if rank == 1:
                        if answer == 'A':
                            dict_is_choice[key] = 1
                        else:
                            dict_is_choice[key] = 0
                    elif rank == 2:
                        if key in dict_is_choice:
                            if dict_is_choice[key] ==1:
                                exam_list_records.append([parent_question_id, student_id, ret, answer, submit_time, question_type])
                                self.dict_student_records[student_id].append([parent_question_id, student_id, ret, answer, submit_time, question_type])
                    elif rank == 3:
                        self.dict_content_answer[key] = answer
            else:
                practice_list_records.append([question, student_id, ret, answer, submit_time, question_type])

        return exam_list_records, practice_list_records

    def getStudentId(self,file_name ='students.txt'):
        list_students = []
        with open(file_name) as handle_f:
            for line in handle_f:
                system_id = long(line.strip())
                list_students.append(system_id)

        set_studends = set(list_students) # students set
        str_content = ','.join([str(x) for x in set_studends])
        sql = "select a.`system_id`, a.`name` from neworiental_user.entity_user a where type = 2 and a.system_id in (%s)" % str_content
        dict_students = {}
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        for row in rows:
            student_id, name = row
            if student_id in set_studends:
                dict_students[student_id] = name

        return dict_students

    def getRightDifficulty(self):
        dict_question_diff = {}
        sql = "select b.id, b.difficulty from neworiental_v3.entity_question b join link_question_answer a on  b.id = a.link_question_id where a.update_time >= \'%s\'" % self.update_time
        rows = self.db_fetcher.get_sql_result(sql,'mysql_logdata')
        for row in rows:
            question_id, difficulty = row
            dict_question_diff[question_id] = int(difficulty)

        return dict_question_diff

    def getChildQuestion(self):
        dict_parent_list = {}
        dict_parent_question = {}
        sql = "select a.id, a.parent_question_id from link_question_answer b join neworiental_v3.entity_question a on a.parent_question_id = b.link_answer_id \
                where b.question_num >= 17 and b.update_time >= \'%s\'"  % self.update_time
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        for row in rows:
            qid = row[0]
            parent_id = row[1]
            if parent_id not in dict_parent_list:
                dict_parent_list[parent_id] = []

            dict_parent_list[parent_id].append(qid)

        for parent_id in dict_parent_list:
            sort_question = sorted(dict_parent_list[parent_id], reverse = False)
            count = 1
            for item in sort_question:
                dict_parent_question[item] = {'parent_id':parent_id, 'rank':count}
                count += 1

        return dict_parent_question

    def getRelationQuestion(self):
        dict_realtion_quesion = {}
        dict_point_question_num = {}
        dict_question_score = {}
        sql = "select a.link_question_id, a.link_answer_id, a.link_point_id, a.question_num, b.difficulty, a.question_exercise_id, b.question_type, a.score \
        from link_question_answer a join neworiental_v3.entity_question b on a.link_question_id =  b.id  where a.update_time >= \'%s\'" % self.update_time
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        dict_parent_quesion  = {}
        link_parent_list = []
        for row in rows:
            link_question_id,link_answer_id, link_point_id, question_num, difficulty, question_exercise_id, question_type, score = row
            dict_realtion_quesion[link_answer_id] = link_question_id, link_point_id, question_num, difficulty, question_exercise_id, question_type
            dict_question_score[link_question_id] = score
            arr_point = link_point_id.strip().split(',')
            for point in arr_point:
                if point not in dict_point_question_num:
                    dict_point_question_num[point] = []

                dict_point_question_num[point].append([link_question_id, question_num, difficulty, question_exercise_id, question_type])

        return dict_realtion_quesion, dict_point_question_num, dict_question_score

    def getScore(self, question_num, answer, ascore):
        ascore, score = 0, 0
        if question_num >= 1 and question_num <= 16:
            score = 5  if (answer == 'A' or answer =='B') else 0
            ascore = 5
        elif question_num >= 17 and question_num <= 23:
            if answer == 'A':
                if ascore == 10:
                    score =4
                elif ascore == 12:
                    score = 4
                elif ascore == 13:
                    score = 5
                elif ascore == 14:
                    score = 5
                elif ascore == 15:
                    score = 6
            elif answer == 'B':
                if ascore == 10:
                    score =7
                elif ascore == 12:
                    score = 8
                elif ascore == 13:
                    score = 9
                elif ascore == 14:
                    score = 10
                elif ascore == 15:
                    score = 11
            elif answer == 'C':
                if ascore == 10:
                    score =9
                elif ascore == 12:
                    score = 11
                elif ascore == 13:
                    score = 12
                elif ascore == 14:
                    score = 13
                elif ascore == 15:
                    score = 15
            elif answer =='D':
                score = ascore
            
        return score

    def getRecentlyExercise(throld = 5):
        set_recent = set()
        sql = "select distinct question_exercise_id from link_question_answer order by question_exercise_id desc limit %s" % throld
        rows = self.db_fetcher.get_sql_result(sql , 'mysql_logdata')
        for row in rows:
            eid = row
            eid = long(eid)
            set_recent.add(eid)

        return set_recent

    def getAllScore(self, link_question_id, question_num):
        ascore = 0
        if link_question_id in self.dict_question_score:
            ascore = self.dict_question_score[link_question_id]
        else:
            if question_num >= 1 and question_num <= 16:
                ascore = 5
            elif question_num >= 17 and question_num <= 21:
                ascore = 12
            elif question_num >= 22 and question_num <= 23:
                ascore = 10

        return ascore

    def statQustionReport(self, range_throld = 4, range_target = 20):
        dict_students_point_question = {}
        dict_student_score = {}
        for item in self.exam_list_records:
            question, student_id, ret, answer, submit_time, question_type = item

            if question in self.dict_realtion_quesion:
                link_question_id, link_point_id, question_num, difficulty, question_exercise_id, question_type = self.dict_realtion_quesion[question]
                arr_points = link_point_id.strip().split(',')
                if student_id not in dict_student_score: dict_student_score[student_id] = 0
                ascore = self.getAllScore(link_question_id, question_num)
                score = self.getScore(question_num, answer, ascore)

                dict_student_score[student_id] += score

                is_right = (answer =='A') or (answer == 'B')
                if student_id not in dict_students_point_question: dict_students_point_question[student_id] = {} # student id

                point_name = '-'.join([str(x) for x in arr_points]) # name
                if point_name not in dict_students_point_question[student_id]:
                    dict_students_point_question[student_id][point_name] = [] 

                dict_students_point_question[student_id][point_name].append((link_question_id, is_right, question_type, difficulty, submit_time)) # question

        dict_res_student_point_question = {}
        for student_id in dict_students_point_question:
            target_rate = 0.5
            if student_id in dict_student_score:
                target_rate = (dict_student_score[student_id]*0.2* 1.2)/150

            dict_point_student_question = dict_students_point_question[student_id]
            dict_res_student_point_question[student_id] = {}
            for point_name in dict_point_student_question:  
                arr_question = dict_point_student_question[point_name]
                target_questions = []
                sort_question = sorted(arr_question, key = lambda x:x[-1], reverse = True)
                right_rate, cnt_rate = 0, range_target
                if len(sort_question) < cnt_rate: cnt_rate = len(sort_question)

                for item in sort_question[:cnt_rate]:
                    link_question_id, is_right, qtype, difficulty, submit_time  = item
                    if is_right == 0:
                        target_questions.append((link_question_id, qtype, difficulty, submit_time))
                    else:
                        right_rate += 1

                if right_rate/cnt_rate < target_rate and len(target_questions) > 0:
                    dict_res_student_point_question[student_id][point_name] = target_questions

        return dict_res_student_point_question

    def getErrorText(self, answer):
        if answer == 'C':
            return '审题时，粗心看错了'
        elif answer == 'D':
            return '审题时，题意读不懂'
        elif answer == 'E':
            return '析题时，思路模糊不清'
        elif answer == 'F':
            return '析题时，思路方向错误'
        elif answer == 'G':
            return '解题时，公式记错了'
        elif answer == 'H':
            return '解题时，计算出错了'
        elif answer == 'I':
            return '未作答（或未完成），时间来不及了'
        elif answer == 'A' or answer  == 'B':
            return '答题正确'

    def getQuestionWords(self):
        dict_question_words = {}
        str_question = ','.join([ str(self.dict_realtion_quesion[x][0]) for x in self.dict_realtion_quesion ])
        str_sql = "select c.id, c.subject_id, t.type_id,t.struct_id, c.json_data from neworiental_v3.entity_question c left join neworiental_v3.entity_question_type t on \
                    t.type_id=c.question_type_id where c.id in (%s)" % str_question

        s_rows = self.db_fetcher.get_sql_result(str_sql,'mysql_logdata')
        for row in s_rows:
            question, subject_id, type_id, struct_id, json_data = row
            if json_data !='' and json_data != 'None' and json_data != None:
                keywords, res = sq.predict(question, subject_id,type_id, struct_id, json_data)
                dict_question_words[question] = keywords, res

        return dict_question_words

    def getPoint2Question(self):
        dict_point_org_question = {}
        for answer_id in self.dict_realtion_quesion:
            link_question_id, link_point_id, question_num, difficulty, question_exercise_id, question_type = self.dict_realtion_quesion[answer_id]
            arr_point = link_point_id.strip().split(',')

            for item in arr_point:
                if item not in dict_point_org_question:
                    dict_point_org_question[item] = []

                dict_point_org_question[item].append(link_question_id)

        return dict_point_org_question

    def pointsRecQuestion(self, dict_students_point_question, throld = 4, error_range = 3):
        # 1,2 choice question 1:easy 2:difficulty 3,4: comprehensive problem 3:easy 4:difficulty
        # dict_point_org_question = self.getPoint2Question() # org question point
        dict_question_text = self.getQuestionWords()
        dict_question_target= {}
        dict_student_recommend_question = {}
        print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % ('学生id', '学生名字', '考点', '考点名称', '原题id', '推荐习题id', '关键词', '难度')
        for student_id in dict_students_point_question:
            sort_student_item = sorted(dict_students_point_question[student_id].items(), key = lambda x:len(x[-1]), reverse = False)
            student_name = self.dict_students[student_id]
            haveTime = 60
            recommend_questions = [] 
            pre_set = set()
            for item_target in sort_student_item:
                if haveTime <= 0: break
                item_point, arr_question = item_target
                item_one = item_point.strip().split('-')[0]

                key = '%s-%s' % (student_id, item_one) 
                pre_set = pre_set | set([x[0] for x in arr_question]) # 
                if len(arr_question) > error_range: 
                    arr_question = arr_question[:error_range]

                for base_question, qtype, difficulty, submit_time in arr_question:
                    if haveTime <= 0: break
                    keywords, text = dict_question_text[base_question]
                    text = text.replace('\n', '').strip('\r').strip() # filter

                    base_question_key = '%s-%s' % (base_question, difficulty)
                    if base_question_key in dict_question_target:
                        target_questions = dict_question_target[base_question_key]
                    else:
                        target_questions = self.recommend.getEsResult(base_question, text, keywords, difficulty, qtype, pre_set, throld)
                        dict_question_target[base_question_key] = target_questions

                    for rec_question in target_questions:
                        if haveTime <= 0: break
                        if rec_question in pre_set: continue

                        haveTime += -1
                        recommend_questions.append((base_question, keywords, rec_question, item_one, difficulty))
                        pre_set.add(rec_question)

            for rec_item in recommend_questions:
                source_question, keywords, rec_question, item_point, difficulty = rec_item
                point_name, ptype, question_type, level, parent_id, link_id = self.dict_point[item_point]
                print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (student_id, student_name, item_point, point_name, source_question, rec_question, keywords, difficulty)

    def import2DataBase(self, flag, is_new = 1, fname = 'student_rec.txt'):
        dict_question_base_info = self.recommend.getThisQuestionBaseInfo() # question quality
        dict_question_topic = self.recommend.getThisQuestionTopic() # question topic
        if is_new == 1:
            # self.db_fetcher.commit_sql_cmd('delete from entity_blackList_answer_question', 'mysql_v3_white_list') # update blacklist
            self.db_fetcher.commit_sql_cmd("delete from sync_student_recommend_question", 'mysql_v3_white_list') # update
        else:
            self.db_fetcher.commit_sql_cmd("delete from entity_recommend_question_bytopic", 'mysql_white_list') # update

        self.recommendMonday(dict_question_base_info) # input error qustion
        if flag == 1: # 1,3 5 recomend
            update_sql = "insert into entity_recommend_question_bytopic(system_id, type,chapter_id,topic_id, question_id, `master`, duration, important, subject_id, score, school_publish, org_id, org_type) values"
            insert_sql = "insert into entity_question_recommend(student_id,student_name,point,point_name,question_id,recommend_id,keywords,difficulty) values"

            # new_sql = "insert into sync_student_recommend_question(system_id, resource_type, resource_id, subject_id, tag1, tag2, score, type, type_level, type_id, upload_id) values"
            new_sql = "insert into sync_student_recommend_question(system_id, resource_type, resource_id, subject_id, tag1, tag2, score, type, type_level, type_id) values"
            insert_score, is_first = 0, 1
            with open(fname) as rec_f:
                for line in rec_f:
                    if insert_score > 1:
                        arr = line.strip().split('\t')
                        student_id, question_id = arr[0], long(arr[5])
                        type_id = 2186
                        if question_id in dict_question_base_info:
                            difficulty, question_type, upload_id = dict_question_base_info[question_id]
                        else:
                            upload_id = 0 

                        if question_id in dict_question_topic:
                            set_topic = dict_question_topic[question_id]
                            if len(set_topic) > 0:
                                type_id = set_topic.pop()

                        if is_first == 1:
                            update_sql += "(%s, 2, 0, 0, %s, 2, 2, 1, %s, %s, 0, 113, 2)" % (student_id, question_id, 0, insert_score)
                            insert_sql += "(%s,\'%s\',%s, \'%s\', %s, %s, \'%s\',%s)" % (arr[0], arr[1], arr[2], arr[3], arr[4], arr[5], arr[6], arr[7])
                            if is_new == 1: new_sql += "(%s, 1, %s, %s, \'最近新错\', \'重难点\', %s, %s, %s, %s)" % (student_id, question_id, 0, insert_score, 1, 3, type_id)
                            is_first = 0
                        else:
                            update_sql += ",(%s, 2, 0, 0, %s, 2, 2, 1, %s, %s, 0, 113, 2)" % (student_id, question_id, 0, insert_score)
                            insert_sql += ",(%s,\'%s\',%s, \'%s\', %s, %s, \'%s\',%s)" % (arr[0], arr[1], arr[2], arr[3], arr[4], arr[5], arr[6], arr[7])
                            if is_new == 1: new_sql += ",(%s, 1, %s, %s, \'最近新错\', \'重难点\', %s, %s, %s, %s)" % (student_id, question_id, 0, insert_score, 1, 3, type_id)

                    insert_score += 1

            # self.db_fetcher.commit_sql_cmd(insert_sql, 'mysql_logdata')
            if is_new == 1:  # update mysql
                self.db_fetcher.commit_sql_cmd(new_sql, 'mysql_v3_white_list') # new
            else:
                self.db_fetcher.commit_sql_cmd(update_sql, 'mysql_white_list')
                    
    def getPoints(self):
        dict_point = {}
        dict_topic_point = {}
        sql = 'select id, name, type, question_type, level, parent_id, link_id, topics_id from entity_exam_points' # do something
        rows = self.db_fetcher.get_sql_result(sql,'mysql_logdata')
        for row in rows:
            point_id, name, ptype, question_type, level, parent_id, link_id, topics_id = row
            point_id = str(point_id)
            dict_point[point_id] =  name, ptype, question_type, level, parent_id, link_id
            if ptype == 3: # 
                arr_topic = [ long(x) for x in topics_id.strip().split(',') ]
                for topic in arr_topic:
                    if topic not in dict_topic_point:
                        dict_topic_point[topic] = []

                    dict_topic_point[topic].append(point_id)

        return dict_point, dict_topic_point

    def getStudentResource(self):
        dict_students_resource = {}
        str_content = ','.join([str(x) for x in self.dict_students])
        sql = "select b.student_id, a.resource_id, b.deadline from neworiental_v3.link_respackage_publish_resource a JOIN neworiental_v3.link_respackage_student b on \
            a.publish_id = b.publish_id where a.resource_type = 2 and b.student_id in (%s)" % (str_content)

        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        for row in rows:
            student_id, resource_id, deadline = row
            if resource_id > 0:
                if student_id not in dict_students_resource:
                    dict_students_resource[student_id] = set()

                dict_students_resource[student_id].add(resource_id)

        return dict_students_resource

    def getQuestionBaseInfo(self, question_set):
        dict_question_difficulty = {}
        str_content = ','.join([str(x) for x in question_set])
        sql = "select b.id, b.difficulty from neworiental_v3.entity_question  where b.id in (%s)" % str_content
        rows = self.db_fetcher.get_sql_result(sql,'mysql_logdata')
        for row in rows:
            question_id, difficulty = row
            dict_question_diff[question_id] = int(difficulty)

        return dict_question_difficulty

    def getStudentScore(self):
        dict_student_score = {}
        for exam_item in self.exam_list_records:
            exam_question, student_id, ret, answer, submit_time, question_type = exam_item

            if exam_question in self.dict_realtion_quesion:
                link_question_id, link_point_id, question_num, difficulty, question_exercise_id, question_type = self.dict_realtion_quesion[exam_question]
                ascore = self.getAllScore(link_question_id, question_num)
                i_score = self.getScore(question_num, answer, ascore)
                exam_key = '%s-%s' % (student_id, question_exercise_id)

                if exam_key not in dict_student_score: dict_student_score[exam_key] = 0
                dict_student_score[exam_key] += i_score

        return dict_student_score

    def getFirstPoint(self): # point
        dict_relation_point13 = {}
        sql = "select a.id id3, a.`name` name3, c.id id1, c.`name` name1 from entity_exam_points a join entity_exam_points  \
                b on b.id = a.parent_id join entity_exam_points c on c.id = b.parent_id where a.type = 3"
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        for row in rows:
            point3, name3, point1, name1 = row
            dict_relation_point13[point3] = name3, point1, name1

        return dict_relation_point13

    def getExerciseName(self):
        dict_exercise_name = {}
        sql = "select DISTINCT a.question_exercise_id, b.resource_name from link_question_answer a join neworiental_v3.entity_exercise b \
                on b.id = a.question_exercise_id where a.update_time >= \'%s\'" % self.update_time

        exercise_rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        for exercise_row in exercise_rows:
            exercise_id, resource_name = exercise_row
            dict_exercise_name[exercise_id] = resource_name

        return dict_exercise_name

    def getExamData(self, dict_student_score, dict_relation_point13, dict_exercise_name):
        for exam_item in self.exam_list_records: # exam
            question, student_id, ret, answer, submit_time, question_type = exam_item
            if question in self.dict_realtion_quesion:
                link_question_id, link_point_id, question_num, difficulty, question_exercise_id, question_type = self.dict_realtion_quesion[question]
                arr_points = [int(x) for x in link_point_id.strip().split(',')]
                exam_key = '%s-%s' % (student_id, question_exercise_id)
                str_point1, str_name1, str_point3, str_name3 = '', '', '', ''
                is_first = True
                for point3 in arr_points:
                    name3, point1, name1 = dict_relation_point13[point3]
                    if is_first == True:
                        str_point3, str_name3, str_point1, str_name1 = str(point3), str(name3), str(point1), str(name1)
                        is_first = False
                    else:
                        str_point3 += ',%d' % point3
                        str_name3 += ',%s' % name3
                        str_point1 += ',%d' % point1
                        str_name1 += ',%s' % name1

                resource_name = dict_exercise_name[question_exercise_id]
                exercise_score = dict_student_score[exam_key] if exam_key in dict_student_score else 0
                a_score ,i_score =  self.getScore(question_num, answer)

                error_text = self.getErrorText(answer)
                print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (student_id, link_question_id, question_type, str_point1, str_name1, str_point3,
                    str_name3, submit_time, resource_name, exercise_score, question_exercise_id, a_score, i_score, difficulty, ret, question_num, error_text, 1)

    def getPracticeData(self, dict_relation_point13, dict_question_topic, dict_question_base_info):
        for practice_item in self.practice_list_records: # practice
            question, student_id, ret, answer, submit_time, question_type = practice_item
            str_point1, str_name1, str_point3, str_name3 = '', '', '', ''
            is_first = True
            if question in dict_question_topic:
                if question in dict_question_topic:
                    topic_set = dict_question_topic[question]
                    for topic in topic_set:
                        if topic in self.dict_topic_point:
                            arr_point3 = [ int(x) for x in self.dict_topic_point[topic] ]
                            for point3 in arr_point3:
                                name3, point1, name1 = dict_relation_point13[point3]
                                if is_first == True:
                                    str_point3, str_name3, str_point1, str_name1 = str(point3), str(name3), str(point1), str(name1)
                                    is_first = False
                                else:
                                    str_point3 += ',%s' % point3
                                    str_name3 += ',%s' % name3
                                    str_point1 += ',%s' % point1
                                    str_name1 += ',%s' % name1

            a_score, i_score = 0, 0
            # 单选题 选择题 填空题
            if question_type == '单选题' or question_type == '选择题' or question_type == '填空题':
                a_score = 5
            else:
                a_score = 12

            if ret == 1:
                i_score = a_score
            elif ret == 5:
                i_score = 0.5 * a_score

            difficulty, qtype  = 1, 1
            if question in dict_question_base_info:
                difficulty, qtype, upload_id = dict_question_base_info[question] 

            errorText = '正确' if ret == 1 else '错误'
            print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (student_id, question, question_type, str_point1, str_name1, str_point3, 
                str_name3, submit_time, '推送练习', 0, 0, a_score, i_score, difficulty, ret, 0, errorText, 0)

    def getData(self):
        dict_student_score = self.getStudentScore()
        dict_relation_point13 = self.getFirstPoint() # point
        dict_exercise_name = self.getExerciseName()

        dict_question_topic = self.recommend.getThisQuestionTopic() # question topic
        dict_question_base_info = self.recommend.getThisQuestionBaseInfo() # question quality
        print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % \
            ('学生id', '题目id', '题目类型', '一级考点id', '一级考点名称', '三级考点id', '三级考点名称', '提交时间', '试卷名称', '成绩', '题集id', '题目满分', '题目得分', '题目难度', '答题结果', '试卷题号', '错误原因', '考练类型')

        self.getExamData(dict_student_score, dict_relation_point13, dict_exercise_name) # exam
        self.getPracticeData(dict_relation_point13, dict_question_topic, dict_question_base_info) # practice

    def recommendMonday(self, dict_question_base_info, is_new = 1, throld = 500):
        dict_question_topic = self.recommend.getThisQuestionTopic() # question topic
        d1 = datetime.datetime.now()
        d3 = d1 + datetime.timedelta(days =-14)
        str_monday = d3.strftime("%Y-%m-%d 00:00:00")

        is_first, insert_score = 1, 0
        new_sql = "insert into sync_student_recommend_question(system_id, resource_type, resource_id, subject_id, tag1, tag2, score, type, type_level, type_id) values"
        update_sql = "insert into entity_recommend_question_bytopic(system_id, type,chapter_id, topic_id, question_id, `master`, duration, important, subject_id, score, school_publish, org_id, org_type) values"
        dict_student_cnt = {}
        records = self.exam_list_records #+ self.practice_list_records
        for item in records:
            question, student_id, ret, answer, submit_time, question_type = item
            if submit_time > str_monday:
                if question in self.dict_realtion_quesion:
                    link_question_id, link_point_id, question_num, difficulty, question_exercise_id, question_type = self.dict_realtion_quesion[question]

                    answer_key = '%s_%s' % (question, student_id)
                    if answer_key in self.dict_content_answer: answer = self.dict_content_answer[answer_key]
                    if answer == 'A' or answer == 'B':
                        ret = 1
                    else:
                        ret = 2
 
                if ret != 1:
                    if student_id not in dict_student_cnt: dict_student_cnt[student_id] = 0
                    if dict_student_cnt[student_id] < throld:
                        # print '%s\t%s' % (student_id, link_question_id)
                        if link_question_id in dict_question_base_info:
                            difficulty, question_type, upload_id = dict_question_base_info[link_question_id]
                        else:
                            upload_id = 0 

                        if is_first == 1:
                            update_sql += "(%s, 2, 0, 0, %s, 2, 2, 1, %s, %s, 0, 113, 2)" % (student_id, link_question_id, 0, insert_score)
                            if is_new == 1: new_sql += "(%s, 1, %s, %s, \'最近新错\', \'重难点\', %s, %s, %s, %s)" % (student_id, link_question_id, 0, insert_score, 1, 3, 2186)
                            is_first = 0
                        else:
                            update_sql += ",(%s, 2, 0, 0, %s, 2, 2, 1, %s, %s, 0, 113, 2)" % (student_id, link_question_id, 0, insert_score)
                            if is_new == 1: new_sql += ",(%s, 1, %s, %s, \'最近新错\', \'重难点\', %s, %s, %s, %s)" % (student_id, link_question_id, 0, insert_score, 1, 3, 2186)

                        dict_student_cnt[student_id] += 1
                        insert_score += 1

        if is_new == 1:
            self.db_fetcher.commit_sql_cmd(new_sql, 'mysql_v3_white_list')
        else:
            self.db_fetcher.commit_sql_cmd(update_sql, 'mysql_white_list')

if __name__=='__main__':
    report = Report()
    if sys.argv[1] == 'output':
        # 1: 考点版本 2: 习题版本
        # dict_question_words = report.getQuestionWords()
        dict_students_point_question = report.statQustionReport() # report
        # dict_diff = report.updateStuAdapt2Difficult() # update student feature
        dict_point_question_set = report.pointsRecQuestion(dict_students_point_question)
    elif sys.argv[1] == 'input':
        import datetime, calendar 
        now_date = datetime.date.today()
        is_flag = (now_date.weekday()  == calendar.FRIDAY or now_date.weekday() == calendar.MONDAY or now_date.weekday()  == calendar.WEDNESDAY)
        flag = 1 if is_flag == True else 0
        report.import2DataBase(flag)
    elif sys.argv[1] == 'base':
        report.getData() # base data
    else:
        pass # dual
