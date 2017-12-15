 # -*- coding: utf-8 -*-
from __future__ import division
import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
import json, math, MySQLdb, random
from cStringIO import StringIO
import httplib, urllib,urllib2,gzip,re,math,numpy
from common.db_fetcher import DataBaseFetcher

class RecommendQuestion(object):
    def __init__(self):
        self.db_fetcher = DataBaseFetcher() # mysql handle
        self.dict_topic = self.getTopicDict()
        self.dict_quality = {
            5:25,
            4:20,
            3:15,
            2:10,
            1:5
        }

        self.dict_question_base_info = self.getQuestionBaseInfo() # base
        self.dict_question_quality = self.getQuestionQuality()
        self.dict_question_topic, self.dict_topic_question = self.getQuestionTopic() # topic
         

    def getThisQuestionTopic(self):
        return self.dict_question_topic

    def getThisQuestionQUality(self):
        return self.dict_question_quality

    def getQuestionBaseInfo(self, save_file = 'question_base.txt'):
        dict_question_base_info = {}
        max_num = 0
        with open(save_file) as handle_f:
            for line in handle_f:
                arr = line.strip().split('\t')
                if len(arr) != 3: continue

                qid, difficulty, question_type = long(arr[0]), int(arr[1]), int(arr[2])
                dict_question_base_info[qid] = difficulty, question_type
                max_num = qid

        sql = "select id, difficulty, question_type from neworiental_v3.entity_question where subject_id = 4 and id > %s order by id asc" % max_num
        rows = self.db_fetcher.get_sql_result(sql, "mysql_logdata")
        with open(save_file, 'a') as write_f:
            for row in rows:
                qid, difficulty, str_question_type = row
                question_type = 1
                if str_question_type == '选择题' or str_question_type == '单选题':
                    question_type = 1
                elif str_question_type == '填空题':
                    question_type = 2
                else:
                    question_type = 3

                dict_question_base_info[qid] = difficulty, question_type
                write_f.write('%s\t%s\t%s\n' % (qid, difficulty, question_type))

        return dict_question_base_info

    def getQuestionQuality(self, save_file = 'quality.txt'):
        dict_question_quality = {}

        max_num = 0
        with open(save_file) as handle_f:
            for line in handle_f:
                arr = line.strip().split('\t')
                if len(arr) != 3: continue
                qid, question_id, extra_score = arr[0], long(arr[1]), int(arr[2])
                dict_question_quality[question_id] = extra_score
                max_num = qid

        sql = "select id, question_id, extra_score from neworiental_v3.entity_question_quality where id > %s" % max_num
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        with open(save_file, 'a') as write_f:
            for row in rows:
                qid, question_id, extra_score = row

                dict_question_quality[question_id] = extra_score
                write_f.write('%s\t%s\t%s\n' % (qid, question_id, extra_score))

        return dict_question_quality

    def getQuestionTopic(self, save_file = 'topic.txt'):
        dict_question_topic = {}
        dict_topic_question = {}
        max_num = 0
        with open(save_file) as handle_f:
            for line in handle_f:
                arr = line.strip().split('\t')
                if len(arr) != 3: continue
                tid, question_id, topic_id = arr[0], arr[1], arr[2]
                question_id = long(question_id)
                topic_id = long(topic_id)

                if question_id not in dict_question_topic: dict_question_topic[question_id] = set()
                if topic_id not in dict_topic_question: 
                    dict_topic_question[topic_id] = {}

                extra_score = 3
                if question_id in self.dict_question_quality:
                    extra_score = self.dict_question_quality[question_id]

                difficulty, question_type = 1, 1
                if question_id in self.dict_question_base_info:
                    difficulty, question_type = self.dict_question_base_info[question_id]

                dict_question_topic[question_id].add(topic_id) # add 
                key = '%s-%s' % (difficulty, question_type)
                if key not in dict_topic_question[topic_id]:
                    dict_topic_question[topic_id][key] = []

                dict_topic_question[topic_id][key].append((question_id, extra_score))
                max_num = tid

        sql = "select id, question_id, topic_id from neworiental_v3.link_question_topic where id > %s" % max_num
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        with open(save_file, 'a') as write_f:
            for row in rows:
                tid, question_id, topic_id = row
                if question_id not in dict_question_topic: dict_question_topic[question_id] = set()

                if topic_id not in dict_topic_question: 
                    dict_topic_question[topic_id] = {}

                extra_score = 3
                if question_id in self.dict_question_quality:
                    extra_score = self.dict_question_quality[question_id]

                difficulty, question_type = 1, 1
                if question_id in self.dict_question_base_info:
                    difficulty, str_question_type = self.dict_question_base_info[question_id]
                    if str_question_type == '选择题' or str_question_type == '单选题':
                        question_type = 1
                    elif str_question_type == '填空题':
                        question_type = 2
                    else:
                        question_type = 3

                dict_question_topic[question_id].add(topic_id) # add 
                if difficulty not in dict_topic_question[topic_id]:
                    dict_topic_question[topic_id][difficulty] = []

                key = '%s-%s' % (difficulty, question_type)
                dict_topic_question[topic_id][key].append((question_id, extra_score))
                write_f.write('%s\t%s\t%s\n' % (tid, question_id, topic_id))

        # sort 
        for topic in dict_topic_question:
            for key in dict_topic_question[topic]:
                dict_topic_question[topic][key] = sorted(dict_topic_question[topic][key], key = lambda x:x[-1], reverse = True) # 
        
        return dict_question_topic, dict_topic_question

    def getTopicDict(self):
        dict_topic = {}
        sql = "select id, `name` from neworiental_v3.entity_topic where subject_id = 4"
        rows = self.db_fetcher.get_sql_result(sql,'mysql_logdata')
        for row in rows:
            topic_id, name = row
            topic_id = str(topic_id)
            dict_topic[topic_id] = name

        return dict_topic

    def getQuestionRate(self):
        dict_question_rate = {}
        sql = "select question_id, rate from question_accuracy"
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        for row in rows:
            question_id, rate = row
            rate = float(rate)
            dict_question_rate[question_id] = rate

        return dict_question_rate

    def getHeaders(self, teacher_id = 'a5cc9ce422e74656a1334a990609b9c9'):
        return {
            'Host': 'jiaoshi.okjiaoyu.cn',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'is_new_okay': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36',
            'Referer': 'http://jiaoshi.okjiaoyu.cn/quizcenter_vm/quizcenter',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
            'Cookie': '_ga=GA1.2.1647528971.1502935646; _gid=GA1.2.1532869714.1506481969; org_id=113; teacher_id=%s; Hm_lvt_2014de1ca4ec84db492ebee33b1dc46c=1506044442,1506324027,1506407711,1506479104; Hm_lpvt_2014de1ca4ec84db492ebee33b1dc46c=1506492873' % teacher_id
        }

    def getUrlContent(self, url):
        req = urllib2.Request(url, headers=self.getHeaders())
        hh = urllib2.HTTPHandler()
        opener = urllib2.build_opener(hh)
        reply = opener.open(req, timeout=30)
        if reply.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(reply.read())
            f = gzip.GzipFile(fileobj=buf)
            res = f.read()
            f.close()
            buf.close()
            reply.close()
        else:
            res = reply.read()

        return res

    def normalLeven(self, str1, str2):
        len_str1 = len(str1) + 1
        len_str2 = len(str2) + 1
        #create matrix
        matrix = [0 for n in range(len_str1 * len_str2)]
        #init x axis
        for i in range(len_str1):
            matrix[i] = i

        #init y axis
        for j in range(0, len(matrix), len_str1):
            if j % len_str1 == 0:
                matrix[j] = j // len_str1

        for i in range(1, len_str1):
            for j in range(1, len_str2):
                if str1[i-1] == str2[j-1]:
                    cost = 0
                else:
                    cost = 1
                
                matrix[j*len_str1+i] = min(matrix[(j-1)*len_str1+i]+1,
                                          matrix[j*len_str1+(i-1)]+1,
                                          matrix[(j-1)*len_str1+(i-1)] + cost)

        return matrix[-1]

    def translate(self, str):
        line = str.strip().decode('utf-8', 'ignore')
        p2 = re.compile(ur'[^\u4e00-\u9fa5]')
        zh = " ".join(p2.split(line)).strip()
        zh = ",".join(zh.split())  
        outStr = zh

        return outStr

    def calScoreQustion(self, question_id, list_rank):
        dict_score = {}
        pos = 0
        dict_qid_type = {}
        set_source = self.dict_question_topic[question_id] if question_id in self.dict_question_topic else set()
        for item in list_rank:
            qid, qtype, topic_list, extra_score = item
            set_target = self.dict_question_topic[qid] if qid in self.dict_question_topic else set()
            score = (1 - numpy.tanh(0.03*pos)) * 60 + self.dict_quality[extra_score]
            if len(set_target & set_source) > 0:
                score += 15

            dict_score[qid] = score
            dict_qid_type[qid] = qtype
            pos += 1

        sort_res = sorted(dict_score.items(), key = lambda x:x[1], reverse = True)
        list_res = []
        for item in sort_res:
            qid = item[0]
            qtype = dict_qid_type[qid]
            list_res.append((qid,qtype))

        return list_res

    def getEsResult(self, question_id, text, keywords, difficulty, bqtype, pre_set, throld_size, throld_page = 10, throld_cost = 5, rank_size = 20):
        """
        url: http://jiaoshi.okjiaoyu.cn/ESRes4EMS/questionQuery?subjectId=4&keyword=%s&difficulty=&questionType=&page=3
        questionType:  1   选择题 2   填空题 3   判断题 4   简答题 6  综合题
        difficulty : １：易　２：中　３：难　４：极难
        """
        list_rank = []
        headers = self.getHeaders() # get headers
        str_pre = ''
        for page in range(1, throld_page):
            try:
                url = "http://jiaoshi.okjiaoyu.cn/teacher-center/search_singlequiz?_=1506480814420&teacher_id=ce36ea7e9c864af39d186b8e8b672864&type=&difficulty=%s&page=%s&keyword=%s&subject_id=4" % (difficulty, page, keywords)
                res = self.getUrlContent(url)
                res = res.replace('\r','').replace('\n','').replace('null', '').replace(':,',':\"\",').strip()
                dict_result = json.loads(res.encode('utf8'))
                total_page = dict_result['data']['total_page']
                if total_page < throld_page:  throld_page = total_page # range update
                list_result = dict_result['data']['list']
                for item in list_result:
                    qid = item['id']
                    question_body = self.translate(item['question_body'])
                    analysis = str(item['analysis']).strip().replace(' ', '')
                    topic_list = item['topic_list']
                    if len(topic_list) >= 1:
                        type_name = item['type_name']
                        if type_name == '选择题':
                            option_list = item['option_list']
                            if len(option_list) != 4: continue

                        cost = self.normalLeven( str_pre, question_body )
                        if qid in self.dict_question_quality:
                            extra_score = self.dict_question_quality[qid]
                        else:
                            extra_score = 1

                        if item['type_alias'] == '单选题' or item['type_alias'] == '选择题':
                            qtype = 1
                        elif item['type_alias'] == '填空题':
                            qtype = 2
                        else:
                            qtype = 3

                        bCharge = (cost > throld_cost) and (len(analysis) > 50) and bqtype == qtype
                        if bCharge:
                            list_rank.append((qid, qtype, item['topic_list'], extra_score)) 
                            str_pre = question_body
            except:
                continue

        list_index = self.calScoreQustion(question_id, list_rank) # rank
        if len(list_index) > throld_size -1:
            list_res = [x[0] for x in list_index[:throld_size-1] ] # end output
        else:
            list_res = [x[0] for x in list_index ] # end output

        # 头部数据处理
        if question_id in self.dict_question_topic:
            topic_set = self.dict_question_topic[question_id]
            tLen = len(topic_set) 
            if  tLen > 0:
                index = random.randint(0, tLen-1)
                topic = list(topic_set)[index] # first
                if question_id in self.dict_question_base_info:
                    difficulty, qtype = self.dict_question_base_info[question_id]

                    key = '%s-%s' % (difficulty, qtype)
                    if key in self.dict_topic_question[topic]:
                        list_res_question = []

                        arr_content_question = self.dict_topic_question[topic][key]
                        for content_item in arr_content_question:
                            res_question, extra_score = content_item

                            if res_question not in pre_set and res_question != question_id:
                                list_res_question.append(res_question)

                            if len(list_res_question) > rank_size: break

                        rnt = throld_size - len(list_res)
                        while rnt > 0:
                            pos = random.randint(0, len(list_res_question) - 1)
                            list_res.append(list_res_question[pos])
                            rnt += -1

        return list_res

if __name__=='__main__':
    recommend = RecommendQuestion()
    list_res = recommend.getEsResult(11011832, '', '双曲线,直线,交点,心率,重庆,取值', 3, 1, set(), 4)

    print list_res