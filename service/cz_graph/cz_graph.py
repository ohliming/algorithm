#!/usr/bin/env python
#coding=utf8
from __future__ import division
import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
import json,math,MySQLdb
import numpy as np
import pandas as pd
from common.db_fetcher import DataBaseFetcher
from pgmpy.models import BayesianModel
from pgmpy.estimators import MaximumLikelihoodEstimator, BayesianEstimator
from pgmpy.factors.discrete import TabularCPD
from pgmpy.readwrite import BIFReader, BIFWriter

stageDict = {
    "CZ":1,
    "GZ":2
}

subjectDict ={
    "cz_chinese":1,
    "gz_chinese":2,
    "cz_math":3,
    "gz_math":4,
    "cz_english":5,
    "gz_english":6,
    "cz_physical":7,
    "gz_physical":8,
    "cz_chemical":9,
    "gz_chemical":10,
    "cz_biological":11,
    "gz_biological":12,
    "cz_history":13,
    "gz_history":14,
    "cz_geographic":15,
    "gz_geographic":16,
    "cz_political":17,
    "gz_political":18,
}

class CzMathGraph(object):
    """docstring for czMathGraph"""
    def __init__(self, stage, subject):
        self.fetcher = DataBaseFetcher()
        self.topicDict, self.topicImportDict = self.getTopic(stage, subject)
        self.quesTopicDict, self.topicQuestionDict = self.getQuestionTopic() # static 

        # student exercise
        self.recordList = self.cacheRecord('question_result.txt')
        self.topicStudentDict = self.getTopicStudent()

    # sample 
    def cacheRecord(self, fName, maxWin = 3000000):
        recordList = []
        pos = 0
        with open(fName) as handleFile:
            for line in handleFile:
                arrContent = line.strip().split('\t')
                studyId, questionId, res = int(arrContent[1]), int(arrContent[2]), arrContent[5]
                isFlag = False
                if questionId in self.quesTopicDict:
                    topicSet = self.quesTopicDict[questionId]
                    for topic in topicSet:
                        if topic in self.topicDict:
                            isFlag = True
                            break

                if isFlag == False: continue
                # normalize data
                try:
                    res = int(res)
                except: 
                    try:
                        result = 0
                        decode_json = json.loads(res)
                        for resDict in decode_json:
                            if resDict['result'] == 1:
                                result += 1
                            else:
                                result -= 1
                        
                        res = 1 if result > 0 else 2
                    except:
                        pass

                if res != 1: continue # 过滤负样本
                recordList.append((studyId, questionId, res))
                pos += 1
                if pos >= maxWin:
                    break

        return recordList

    def getTopicStudent(self):
        topicStudentDict = {}
        for item in self.recordList:
            studyId, questionId, res = item

            if questionId not in self.quesTopicDict: continue
            for topic in self.quesTopicDict[questionId]:
                if topic not in topicStudentDict:
                    topicStudentDict[topic] = {}

                if studyId not in topicStudentDict[topic]:
                    topicStudentDict[topic][studyId] = 0

                topicStudentDict[topic][studyId] += 1

        return topicStudentDict

    # 统计条件概率
    def staticTopicProb(self, topic, topicList):
        if topic not in self.topicStudentDict:
            return 0.0

        fenmuSet = set()  # 条件student集合
        isFirst = True
        for item in topicList:
            if item not in self.topicStudentDict: continue
            itemSet = set([ x for x in self.topicStudentDict[item]])
            if isFirst:
                fenmuSet = itemSet
            else:
                fenmuSet = fenmuSet & itemSet

        fenmu, fenzi = 0.0, 0.0
        for student in fenmuSet:
            for item in topicList:
                fenmu += self.topicStudentDict[item][student]

            if student in self.topicStudentDict[topic]:
                fenzi += self.topicStudentDict[topic][student]

        p = fenzi / fenmu if fenmu > 0 and fenzi < fenmu else 0.0
        return p

    #  获取词典
    def getTopic(self, stage, subjectId):
        topicDict = {}
        topicImportDict = {}
        sql = "select id, name, is_important from entity_topic where subject_id= %s and stage_id = %s" % (subjectId, stage)
        db_rows = self.fetcher.get_sql_result(sql, "mysql_v3")
        for row in db_rows:
            topicId, name, important = row
            topicDict[topicId] = name
            topicImportDict[topicId] = important

        return topicDict, topicImportDict

    # 获取问题主题
    def getQuestionTopic(self):
        quesTopicDict = {}
        topicQuestionDict = {}
        db_rows = self.fetcher.get_sql_result("select topic_id, question_id from link_question_topic ","mysql_v3")
        for row in db_rows:
            topicId, questionId = row
            if topicId not in topicQuestionDict:
                topicQuestionDict[topicId] = []

            topicQuestionDict[topicId].append(questionId)

            if questionId not in quesTopicDict:
                quesTopicDict[questionId] = []

            quesTopicDict[questionId].append(topicId)

        quesTopicDict = { key : set(value)  for key, value in quesTopicDict.items() } # list to set
        topicQuestionDict = { key: set(value) for key, value in topicQuestionDict.items() }

        return quesTopicDict, topicQuestionDict

    # 统计问题正确率
    def statisQuestion(self, subject_id):
        questionDict = {}
        db_rows = self.fetcher.get_sql_result("select question_id, sum(answer_num) answernum, sum(right_num) rightnum from entity_trail_question where subject_id = %s GROUP BY question_id " % subject_id, "mysql_v3")
        for row in db_rows:
            questionId, answer, right = row
            questionDict[questionId] = answer,  right

        return questionDict

    def isLoopGraph(self,pairTopic, iniRelList, childDict):
        startTopic, endTopic = pairTopic
        if startTopic == endTopic: return True # loop
        stackList = [ startTopic ]
        missSet, popSet = set(), set() # init set and pop set
        while len(stackList) > 0:
            if endTopic in missSet:
                return True # the graph is unicom

            topic = stackList[-1]
            stackList.pop() # pop
            if (topic not in childDict) or topic in missSet: continue
            popSet.add(topic) # add pop set
            childSet = childDict[topic]
            for child in childSet:
                stackList.append(child)
                missSet.add(child)

        return False

    # 构造有像图知识网络
    def getTopicDAG(self, threshold = 30, inDegreeThr = 3, outDegreeThr = 4):
        iniRelList = []
        relDict = {}
        topicList = [ topic for topic in self.topicDict ]
        for i  in xrange(len(topicList)):
            for j in xrange(i+1, len(topicList)):
                if topicList[i] in self.topicQuestionDict and topicList[j] in self.topicQuestionDict:
                    iSet, jSet  = self.topicQuestionDict[topicList[i]], self.topicQuestionDict[topicList[j]]
                    key = "%s-%s" % (topicList[i], topicList[j])
                    mLen =  len(iSet & jSet)
                    if mLen > threshold:
                        relDict[key] = mLen

        sortRel = sorted(relDict.items(),  key = lambda x:x[1],  reverse = True)
        inDegreeDict = {} # 入度记录字典
        outDegreeDict = {} #  出度记录字典
        childDict = {} # child 
        for item in sortRel:
            inDegreeThr, outDegreeThr = 3, 4
            arrTopic = [ int(x) for x in item[0].split("-") ]
            if len(arrTopic) != 2: continue

            start, end = arrTopic[0], arrTopic[1]

            # 判断转移方向
            p0 = self.staticTopicProb(start, [end])
            p1 = self.staticTopicProb(end, [start])
            pairTopic = (start, end) if p1 < p0 else (end, start)
            start, end = pairTopic #

            if self.topicImportDict[start] < 1:
                outDegreeThr = 1

            if self.topicImportDict[end] < 1:
                inDegreeThr = 1

            inDegree = inDegreeDict[end] if end in inDegreeDict else 0
            outDegree = outDegreeDict[start] if start in outDegreeDict else 0

            isLoop = self.isLoopGraph(pairTopic, iniRelList, childDict)
            bFlag = (isLoop == False) and (inDegree < inDegreeThr) and (outDegree < outDegreeThr)
            if bFlag:
                iniRelList.append(pairTopic)
                if end not in childDict:
                    childDict[end] = set()

                childDict[end].add(start)
                # 出度 and 入度
                outDegreeDict[start] = 1 + outDegree
                inDegreeDict[end] = 1 + inDegree

        return iniRelList

    # 构建系数矩阵数组
    def getRowsNormalize(self, topicList):
        rowsData = []
        topicLen = len(topicList)
        topicIndex = { topicList[i]:i for i in xrange(topicLen) }
        for item in self.recordList:
            studyId, questionId, res = item
            arr = [0] * topicLen
            if questionId in self.quesTopicDict:
                topicSet = self.quesTopicDict[questionId]
                for topic in topicSet:
                    if topic in topicIndex:
                        arr[topicIndex[topic]] = 1

            sparr = pd.SparseArray(arr)
            rowsData.append(arr)

        return rowsData

    def makeModel(self):
        # graph structure 
        initRelation = self.getTopicDAG()  # 概率图构建
        relationList = []
        stuModel = BayesianModel()  # DAG
        for edge in initRelation:
            try:
                start, end = edge
                stuModel.add_edge(str(start), str(end))
                relationList.append(edge)
            except:
                continue

        # save file
        with open('model.txt', 'w') as write_f:
            for item in relationList:
                write_f.write('%s,%s\n' % (self.topicDict[item[0]], self.topicDict[item[1]]))

        # learning from data
        topicList = [ topic for topic in self.topicDict]
        rowsData = self.getRowsNormalize(topicList)
        print 'the rows len is:%s' % len(rowsData)

        #data = pd.DataFrame(rowsData, columns= [str(x) for x in topicList])
        #print 'the data len is:%s' % len(data)

        #stuModel.fit(data[:3000], estimator = MaximumLikelihoodEstimator)

        #writer = BIFWriter(stuModel)
        #writer.write_bif('stuModel.bif')

if __name__=='__main__':
    # do samething
    cz_math = CzMathGraph(stageDict["GZ"], subjectDict["gz_physical"])
    cz_math.makeModel()
