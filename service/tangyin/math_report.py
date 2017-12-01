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
    def __init__(self, exercise_id, update_time = '2017-06-06 00:00:00'):
        # do something inits
        self.db_fetcher = DataBaseFetcher()
        self.exercise_id = exercise_id
        self.dict_content_answer = {} # error content
        self.curr_time = datetime.datetime.now()

        self.update_time = update_time # update time 
        self.recommend = RecommendQuestion()

        self.dict_realtion_quesion, self.dict_question_num = self.getRelationQuestion()
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
        sql = "select question_id, student_id, ret_num, submit_answer, submit_time from entity_student_exercise where submit_time > \'%s\' and exercise_source = 6" % ( self.update_time )
        dict_is_choice = {}
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        for row in rows:
            question, student_id, ret, answer, submit_time = row
            student_id = long(student_id)

            if answer == 'null' or answer == 'None' or answer == '' or answer == 'NULL' or answer == None or len(answer) == 0: continue
            if question in self.dict_realtion_quesion:
                exam_list_records.append([question, student_id, ret, answer, submit_time])
                self.dict_student_records[student_id].append([question, student_id, ret, answer, submit_time])
                self.dict_content_answer['%s_%s' % (question, student_id)] = answer
            elif question in self.dict_parent_quesion:
                dict_content = self.dict_parent_quesion[question]
                parent_question_id = dict_content['parent_id']

                rank = dict_content['rank']
                link_question_id, link_point_id, question_num, difficulty, question_exercise_id = self.dict_realtion_quesion[parent_question_id]
                if  question_num >= 17 and question_num <= 21:
                    if rank == 1: 
                        exam_list_records.append([parent_question_id, student_id, ret, answer, submit_time])
                        self.dict_student_records[student_id].append([parent_question_id, student_id, ret, answer, submit_time])
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
                                exam_list_records.append([parent_question_id, student_id, ret, answer, submit_time])
                                self.dict_student_records[student_id].append([parent_question_id, student_id, ret, answer, submit_time])
                    elif rank == 3:
                        self.dict_content_answer[key] = answer
            else:
                practice_list_records.append([question, student_id, ret, answer, submit_time])

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
        sql = "select a.link_question_id, a.link_answer_id, a.link_point_id, a.question_num, b.difficulty, a.question_exercise_id from link_question_answer a join neworiental_v3.entity_question b on a.link_question_id = \
            b.id  where a.update_time >= \'%s\'" % self.update_time
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        dict_parent_quesion  = {}
        link_parent_list = []
        for row in rows:
            link_question_id,link_answer_id, link_point_id, question_num, difficulty, question_exercise_id = row
            dict_realtion_quesion[link_answer_id] = link_question_id, link_point_id, question_num, difficulty, question_exercise_id
            arr_point = link_point_id.strip().split(',')
            for point in arr_point:
                if point not in dict_point_question_num:
                    dict_point_question_num[point] = []

                dict_point_question_num[point].append([link_question_id, question_num, difficulty, question_exercise_id])

        return dict_realtion_quesion, dict_point_question_num

    def getScore(self, question_num, answer):
        ascore, score = 0, 0
        if question_num >= 1 and question_num <= 16:
            score = 5  if (answer == 'A' or answer =='B') else 0
            ascore = 5
        elif question_num >= 17 and question_num <= 21:
            if answer == 'A':
                score = 4
            elif answer == 'B':
                score = 7
            elif answer == 'C':
                score = 9
            elif answer =='D':
                score = 12
            ascore = 12
        elif question_num >= 22 and question_num <= 23:
            if answer == 'A':
                score = 4
            elif answer == 'B':
                score = 7
            elif answer == 'C':
                score = 9
            elif answer =='D':
                score = 10
            ascore = 10

        return ascore, score

    def statQustionReport(self):
        dict_question_count, dict_question_right  = {} , {}
        dict_point_count, dict_point_right = {}, {}
        dict_error_students , dict_right_students = {}, {}

        for item in self.exam_list_records:
            question, student_id, ret, answer, submit_time = item

            if question in self.dict_realtion_quesion:
                link_question_id, link_point_id, question_num, difficulty, question_exercise_id = self.dict_realtion_quesion[question]
                arr_points = link_point_id.strip().split(',')
                ascore, score = self.getScore(question_num, answer)

                is_right = (answer =='A') or (answer == 'B')
                # 1 point
                for point in arr_points:
                    if point in self.dict_point:
                        name, ptype, question_type, level, parent_id, link_id = self.dict_point[point]
                        if name not in dict_point_count:
                            dict_point_count[name] = 0
                            dict_point_right[name] = 0

                        dict_point_right[name] += 1 if (question_num <= 16 and is_right) or (question_num >= 17 and answer =='D') else 0 # 
                        dict_point_count[name] += 1

                if link_question_id not in dict_question_count:
                    dict_question_right[link_question_id] = 0
                    dict_question_count[link_question_id] = 0

                dict_question_right[link_question_id] += 1 if ret == 1 else 0 # 
                dict_question_count[link_question_id] += 1
                
                # questions
                if link_question_id not in dict_right_students:
                    dict_right_students[link_question_id] = []
                    dict_error_students[link_question_id] = []

                if (question_num <= 16 and is_right) or (question_num >= 17 and answer =='D'):
                    dict_right_students[link_question_id].append(student_id)
                else:
                    dict_error_students[link_question_id].append(student_id)

                if student_id not in self.dict_student_score:
                    self.dict_student_score[student_id] = 0

                self.dict_student_score[student_id] += score

        dict_point_acc = {}
        for point_name in dict_point_count:
            acc = dict_point_right[point_name] / dict_point_count[point_name]
            dict_point_acc[point_name] = acc
            #print '%s \t%s' % (point_name, acc)

        # students 
        dict_students_point_question = self.calStudentPoints(dict_point_acc)
        return dict_students_point_question

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

    def calStudentPoints(self, dict_point_acc):
        dict_coef = {x:1.0 for x in self.dict_point} # 
        bate = 0.25
        dict_student_points = {}
        dict_students_point_question = {} # student -> error question
        for student_id in self.dict_students:
            if student_id not in dict_student_points:
                dict_student_points[student_id] = {}

            records = sorted(self.dict_student_records[student_id], key = lambda x:x[-1], reverse = True)
            dict_error = {'C':0.0, 'D':0.0,'E':0.0,'F':0.0,'G':0.0,'H':0.0}
            mass_score = 0
            dict_question_point = {}
            for item in records:
                question, student_id, ret, answer, submit_time = item

                if question in self.dict_realtion_quesion:
                    link_question_id, link_point_id, question_num, difficulty, question_exercise_id = self.dict_realtion_quesion[question]
                    if question_num <= 12:
                        qtype = 1
                    elif question_num >= 13 and question_num <=16:
                        qtype = 2
                    else:
                        qtype = 3

                    difficulty = self.dict_question_diff[link_question_id]
                    arr_points = link_point_id.strip().split(',')

                    a_score ,score =  self.getScore(question_num, answer)
                    content = '%s_%s' % (question, student_id)
                    if content in self.dict_content_answer:
                        answer = self.dict_content_answer[content]
                        if answer != 'A' and answer != 'B':
                            dict_error[answer] += a_score - score
                            if  answer == 'C' or answer == 'G' or answer == 'H':
                                mass_score += a_score - score

                        for point in arr_points:
                            if point not in dict_question_point:
                                dict_question_point[point] = []

                            dict_question_point[point].append((link_question_id, qtype))
                            name, ptype, question_type, level, parent_id, link_id = self.dict_point[point]
                            acc = dict_point_acc[name]
                            if point not in dict_student_points[student_id]:
                                dict_student_points[student_id][point] = 0.0

                            rfa = 1 if submit_time > self.update_time else 10
                            dict_student_points[student_id][point] += dict_coef[point]*(a_score - score)*acc / math.log(rfa+bate*(level + difficulty))

            sort_error = sorted(dict_error.items(), key = lambda x:x[1], reverse = True)
            if len(dict_student_points[student_id]) > 0:
                sort_point = sorted(dict_student_points[student_id].items(), key = lambda x:x[1], reverse = True)
                point  = sort_point[0][0]
                student_name = self.dict_students[student_id]
                point_name1, ptype1, question_type1, level1, parent_id1, link_id1 = self.dict_point[point]
                point_name2, ptype2, question_type2, level2, parent_id2, link_id2 = self.dict_point[sort_point[1][0]]
                point_name3, ptype3, question_type3, level3, parent_id2, link_id3 = self.dict_point[sort_point[2][0]]

                is_power = 1 if mass_score > 5 else 0
                error1, error1score = sort_error[0][0], sort_error[0][1]
                error2, error2score = sort_error[1][0], sort_error[1][1]
                error1_name, error2_name = self.getErrorText(error1), self.getErrorText(error2)

                arr_question = dict_question_point[point]
                dict_students_point_question[student_id] = point, arr_question

        return dict_students_point_question

    def getPoint2Question(self):
        dict_point_org_question = {}
        for answer_id in self.dict_realtion_quesion:
            link_question_id, link_point_id, question_num, difficulty, question_exercise_id = self.dict_realtion_quesion[answer_id]
            arr_point = link_point_id.strip().split(',')

            for item in arr_point:
                if item not in dict_point_org_question:
                    dict_point_org_question[item] = []

                dict_point_org_question[item].append(link_question_id)

        return dict_point_org_question

    def pointsRecQuestion(self, dict_students_point_question, dict_diff, throld = 5):
        # 1,2 choice question 1:easy 2:difficulty 3,4: comprehensive problem 3:easy 4:difficulty
        # dict_point_org_question = self.getPoint2Question() # org question point
        dict_question_text = self.getQuestionWords()
        dict_question_target= {}
        dict_student_recommend_question = {}
        print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % ('学生id', '学生名字', '考点', '考点名称', '原题id', '题集id(非答题卡)', '推荐习题id', '关键词', '难度')
        for student_id in dict_students_point_question:
            point, arr_question = dict_students_point_question[student_id]
            key = '%s-%s' % (student_id, point)
            rateRight, difficulty = dict_diff[key] if key in dict_diff else (0.0, 1)
            haveTime = 60
            recommend_questions, set_de_weight = [], set(arr_question)
            pre_set = set() # 
            for base_question, qtype in arr_question:
                if haveTime <= 0: break
                keywords, text = dict_question_text[base_question]
                text = text.replace('\n', '').strip('\r').strip() # filter

                if base_question in dict_question_target:
                    target_questions = dict_question_target[base_question]
                else:
                    target_questions = self.recommend.getEsResult(base_question,text, keywords, difficulty, qtype)
                    dict_question_target[base_question] = target_questions

                if len(target_questions) > 5: target_questions = target_questions[:throld]
                for target in target_questions:
                    if haveTime <= 0: break
                    rec_question, types = target
                    if rec_question in set_de_weight: continue
                    if types == 1:
                        haveTime += -4
                    else:
                        haveTime += -15

                    if rec_question not in pre_set:
                        recommend_questions.append((base_question, keywords, rec_question))
                        pre_set.add(rec_question)

            student_name = self.dict_students[student_id]
            point_name, ptype, question_type, level, parent_id, link_id = self.dict_point[point]
            for rec in recommend_questions: 
                source_question, keywords, rec_question = rec
                print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (student_id, student_name, point, point_name, source_question, exercise_id, rec_question, keywords, difficulty)
    
    def importDefault(self):
        defult_list = [(10805815,0), (10806190, 2), (10805815, 4), (10806184, 6), (10806182, 8), (10806169, 10), (10806104, 12), (10806057, 14), (10805815, 16), (10806068, 18)]
        update_sql = "insert into entity_recommend_question_bytopic(system_id, type,chapter_id,topic_id, question_id, `master`, duration, important, subject_id, score, school_publish, org_id, org_type) values"
        db_rows = self.db_fetcher.get_sql_result("select student_id from entity_student_white_list", "mysql_white_list")
        is_first = 1
        for row in db_rows:
            student_id = row[0]
            for item in defult_list:
                question_id, subject_id = item
                if is_first == 1:
                    update_sql += "(%s, 2, 0, 0, %s, 2, 2, 1, %s, %s, 0, 113, 2)" % (student_id, question_id, subject_id, 0)
                    is_first = 0
                else:
                    update_sql += ",(%s, 2, 0, 0, %s, 2, 2, 1, %s, %s, 0, 113, 2)" % (student_id, question_id, subject_id, 0)

        self.db_fetcher.commit_sql_cmd(update_sql, 'mysql_white_list')

    def import2DataBase(self, flag, fname = 'student_rec.txt'):
        self.db_fetcher.commit_sql_cmd("delete from entity_recommend_question_bytopic", 'mysql_white_list') # update
        self.importDefault()
        if flag == 1: # 1,3 5 recomend
            update_sql = "insert into entity_recommend_question_bytopic(system_id, type,chapter_id,topic_id, question_id, `master`, duration, important, subject_id, score, school_publish, org_id, org_type) values"
            insert_sql = "insert into entity_question_recommend(student_id,student_name,point,point_name,question_id,exercise_id,recommend_id,keywords,difficulty) values"
            score = 10
            is_first = 1
            with open(fname) as rec_f:
                for line in rec_f:
                    score += 1
                    arr = line.strip().split('\t')
                    student_id, question_id = arr[0], arr[6]
                    if is_first == 1:
                        update_sql += "(%s, 2, 0, 0, %s, 2, 2, 1, %s, %s, 0, 113, 2)" % (student_id, question_id, 4, score)
                        insert_sql += "(%s,\'%s\',%s, \'%s\', %s, %s, %s, \'%s\',%s)" % (arr[0], arr[1], arr[2], arr[3], arr[4], arr[5], arr[6], arr[7], arr[8])
                        is_first = 0
                    else:
                        update_sql += ",(%s, 2, 0, 0, %s, 2, 2, 1, %s, %s, 0, 113, 2)" % (student_id, question_id, 4, score)
                        insert_sql += ",(%s,\'%s\',%s, \'%s\', %s, %s, %s, \'%s\',%s)" % (arr[0], arr[1], arr[2], arr[3], arr[4], arr[5], arr[6], arr[7], arr[8])

            self.db_fetcher.commit_sql_cmd(insert_sql, 'mysql_logdata')
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
                arr_topic = topics_id.strip().split(',')
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

    def updateStuAdapt2Difficult(self, range_throld = 10, difficulty_throld = 10):
        dict_exam_question = {}
        dict_exam_difficulty = {}
        dict_question_topic = self.recommend.getThisQuestionTopic() # 

        for exam_item in self.exam_list_records:
            question, student_id, ret, answer, submit_time = exam_item
            if question in self.dict_realtion_quesion:
                link_question_id, link_point_id, question_num, difficulty, question_exercise_id = self.dict_realtion_quesion[question]
                arr_point = link_point_id.strip().split(',')
                is_right = 1 if answer == 'A' or answer == 'B' else 0

                for point in arr_point:
                    key = '%s-%s' % (student_id, point)
                    if key not in dict_exam_question:
                        dict_exam_question[key] = []
                        dict_exam_difficulty[key] = {}

                    record = (question, is_right, difficulty, submit_time)
                    dict_exam_question[key].append(record)
                    if difficulty not in dict_exam_difficulty[key]: dict_exam_difficulty[key][difficulty] = []        
                    dict_exam_difficulty[key][difficulty].append(record)

        question_set = set([x[0] for x in self.practice_list_records])
        dict_question_difficulty = self.getQuestionBaseInfo(question_set)

        for practice_item in self.practice_list_records:
            question, student_id, ret, answer, submit_time = practice_item
            is_right = 1 if ret == 1 else 0
            if question in dict_question_difficulty:
                difficulty = self.dict_question_difficulty[question]
                if question in dict_question_topic:
                    topic_set = dict_question_topic[question]
                    for topic in topic_set:
                        if topic in self.dict_topic_point:
                            point = self.dict_topic_point[topic]
                            key = '%s-%s' % (student_id, point)
                            if key not in dict_exam_question:
                                dict_exam_question[key] = []
                                dict_exam_difficulty[key] = {}

                            if difficulty not in dict_exam_difficulty[key]: dict_exam_difficulty[key][difficulty] = []
                            record = (question, is_right, difficulty, submit_time)
                            dict_exam_difficulty[key][difficulty].append(record)
                            dict_exam_question[key].append(record)

        dict_res = {}
        self.db_fetcher.commit_sql_cmd('delete from entity_student_feature', 'mysql_logdata')
        for key in dict_exam_question:
            arr_content = key.split('-')
            student_id, point = arr_content[0], arr_content[1]
            question_records = sorted(dict_exam_question[key], key = lambda x:x[-1], reverse =True)
            right_cnt = 0
            throld = min(len(question_records), range_throld)
            #if throld < 10: continue
            for record_item in question_records[:throld]:
                question, is_right, difficulty, submit_time = record_item
                right_cnt += is_right

            rateRight = right_cnt / range_throld
            adaDiff, pDiff = 0, -1
            for difficulty in dict_exam_difficulty[key]:
                drecords = sorted(dict_exam_difficulty[key][difficulty], key = lambda x:x[-1], reverse = True)
                difficulty_throld = min(len(drecords), difficulty_throld)
                #if difficulty_throld < 4: continue
                dright_cnt = 0
                for diff_item in drecords[:difficulty_throld]:
                    question, is_right, difficulty, submit_time = diff_item
                    dright_cnt += is_right

                drateRight = dright_cnt / difficulty_throld
                if drateRight > pDiff:
                    adaDiff = difficulty
                    pDiff = drateRight

            point_name, ptype, question_type, level, parent_id, link_id = self.dict_point[point]
            insert_sql = "insert into entity_student_feature(student_id, point_id, point_name, adapt_difficulty, master) values(%s, %s, \'%s\', %s, %s)" \
                    % (student_id, point, point_name, adaDiff, rateRight)

            insert_id = self.db_fetcher.commit_sql_cmd(insert_sql, 'mysql_logdata')
            dict_res[key] = rateRight, difficulty

        return dict_res

    def getData(self):
        dict_merge = {}
        print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % \
        ('b.student_id', '名字', 'question_id', 'answer', '得分', 'point_id', '原题目id', '题号', '满分','point_name_三级', 'level', 'point_id_二级', 'point_id_一级', 'point_name_二级','point_name_一级')
        for item in self.exam_list_records:
            question, student_id, ret, answer, submit_time = item
            if question in self.dict_realtion_quesion:
                link_question_id, link_point_id, question_num, difficulty, question_exercise_id = self.dict_realtion_quesion[question]
                arr_points = link_point_id.strip().split(',')
                score_s, score = self.getScore(question_num, answer)

                content = '%s_%s' % (question, student_id)
                if content in self.dict_content_answer:
                    answer = self.dict_content_answer[content]
                    for point in arr_points:
                        name, ptype, question_type, level, parent_id, link_id = self.dict_point[point]

                        # two level 
                        parent_id = str(parent_id)
                        name2, ptype2, question_type2, level2, parent_id2, link_id2 = self.dict_point[parent_id]

                        # 1
                        parent_id2 = str(parent_id2)
                        name1, ptype1, question_type1, level1, parent_id1, link_id1 = self.dict_point[parent_id2]

                        print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % \
                        (student_id, self.dict_students[student_id],question, answer, score, point, link_question_id, question_num, score_s,name, level , parent_id, parent_id2, name2, name1 )

if __name__=='__main__':
    exercise_id = 437366
    report = Report(exercise_id)
    # do something
    if sys.argv[1] == 'output':
        #dict_question_words = report.getQuestionWords()
        dict_students_point_question = report.statQustionReport() # report
        #report.getData()
        dict_diff = report.updateStuAdapt2Difficult() # update student feature
        dict_point_question_set = report.pointsRecQuestion(dict_students_point_question, dict_diff)
    elif sys.argv[1] == 'input':
        import datetime, calendar 
        now_date = datetime.date.today()  
        is_flag = now_date.weekday()  == calendar.FRIDAY or now_date.weekday()  == calendar.MONDAY or now_date.weekday()  == calendar.WEDNESDAY
        flag = 1 # if is_flag == True else 1
        report.import2DataBase(flag)
        