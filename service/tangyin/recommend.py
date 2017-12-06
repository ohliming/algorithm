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

class RecommendQuestion(object):
    def __init__(self):
        self.db_fetcher = DataBaseFetcher() # mysql handle
        self.dict_topic = self.getTopicDict()
        self.dict_question_rate = self.getQuestionRate() # rate
        self.dict_question_quality = self.getQuestionQuality()
        self.dict_question_topic = self.getQuestionTopic() # topic

        self.dict_quality = {
            5:25,
            4:20,
            3:15,
            2:10,
            1:5
        }

    def getThisQuestionTopic(self):
        return self.dict_question_topic

    def getThisQuestionQUality(self):
        return self.dict_question_quality

    def getQuestionQuality(self, save_file = 'quality.txt'):
        dict_question_quality = {}

        max_num = 0
        with open(save_file) as handle_f:
            for line in handle_f:
                arr = line.strip().split('\t')
                if len(arr) != 4: continue
                qid, question_id, extra_score, difficulty = arr[0], long(arr[1]), arr[2], float(arr[3])
                dict_question_quality[question_id] = extra_score, difficulty
                max_num = qid

        sql = "select id, question_id, extra_score, difficulty from neworiental_v3.entity_question_quality where id > %s" % max_num
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        with open(save_file, 'a') as write_f:
            for row in rows:
                qid, question_id, extra_score, difficulty = row
                dict_question_quality[question_id] = extra_score, difficulty
                write_f.write('%s\t%s\t%s\t%s\n' % (qid, question_id, extra_score, difficulty))

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
                if topic_id not in dict_topic_question: dict_topic_question[topic_id] = set()

                dict_question_topic[question_id].add(topic_id)
                dict_topic_question[topic_id].add(question_id)
                max_num = tid

        sql = "select id, question_id, topic_id from neworiental_v3.link_question_topic where id > %s" % max_num
        rows = self.db_fetcher.get_sql_result(sql, 'mysql_logdata')
        with open(save_file, 'a') as write_f:
            for row in rows:
                tid, question_id, topic_id = row
                if question_id not in dict_question_topic: dict_question_topic[question_id] = set()
                if topic_id not in dict_topic_question: dict_topic_question[topic_id] = set()

                dict_question_topic[question_id].add(topic_id)
                dict_topic_question[topic_id].add(question_id)
                write_f.write('%s\t%s\t%s\n' % (tid, question_id, topic_id))
        
        return dict_question_topic

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

    def getHeaders(self, teacher_id = '670ce809de6448629e6b422f659abede'):
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

    def filterQuestion(self,qid_source, source_str, qid_target, target_str, min_throld = 0.1, max_throld =  0.9): # filter
        isfilter = 1
        rate_target = self.dict_question_rate[qid_target] if qid_target in self.dict_question_rate else 0.0
        if rate_target > 0:
            if rate_target < min_throld or rate_target > max_throld:
                isfilter = -1

        return isfilter

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

    def getEsResult(self, question_id, text, keywords, difficulty, bqtype, throld_page = 10, throld_word = 5):
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
                        isfilter = self.filterQuestion(question_id, text, qid, question_body)
                        if qid in self.dict_question_quality:
                            extra_score, difficulty = self.dict_question_quality[qid]
                        else:
                            extra_score = 1

                        if item['type_alias'] == '单选题' or item['type_alias'] == '选择题':
                            qtype = 1
                        elif item['type_alias'] == '填空题':
                            qtype = 2
                        else:
                            qtype = 3
                        bCharge = (cost > throld_word) and (isfilter > 0) and (len(analysis) > 50) and (bqtype == qtype)
                        if bCharge:
                            list_rank.append((qid, qtype, item['topic_list'], extra_score))
                            str_pre = question_body
            except:
                continue

        list_res = self.calScoreQustion(question_id, list_rank) # rank
        return list_res

if __name__=='__main__':
    recommend = RecommendQuestion()
    list_res = recommend.getEsResult(10800488,'','函数,lg,ln2,已知,ln', 3, 1)
    print list_res