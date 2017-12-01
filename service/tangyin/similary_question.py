# -*- coding: utf-8 -*-
from __future__ import division
import sys
import json
import logging
import MySQLdb
import codecs
from  textrank4zh import TextRank4Keyword

reload(sys)
sys.setdefaultencoding('utf-8')
word = TextRank4Keyword()

def structone(struct, json):
    res = ""
    kaodian=''
    zhuanti=''
    dianping=''
    body = json["body"]

    for text in body:
        try:
            if "type" in text.keys():
                type = text["type"]
                if "text" == type:
                    res += text["value"]
        except:
            res += text

    if struct == 1 or struct == 5:
        option = json["options"]
        if option != "" or option != None:
            for ops in option:
                for op in ops:
                    # print "struct-option is", op
                    try:
                        if "type" in op.keys():
                            type = op["type"]
                            if "text" == type:
                                # print "op value::::",op["value"]
                                if len(op["value"]) == 1:
                                    try:
                                        res += op["value"]
                                    except:
                                        continue;
                                elif len(op["value"]) > 1:
                                    for value in op["value"]:
                                        # print "value:::",value
                                        try:
                                            mm = str(value)
                                            res += mm
                                        except:
                                            continue
                    except:
                        res += op

    answer = json["answer"]
    if answer != "" or answer != None:
        if struct == 5 or struct == 4:
            # print "struct answer 5:::;",answer
            try:
                for ns in answer:
                    # print "ns:::;",ns
                    if "group" in ns.keys():
                        ans = ns["group"]
                        for an in ans:
                            if type in an.keys():
                                if "text" == type["type"]:
                                    res += type["value"]
                    if "text" in ns.keys():
                        res += ns["value"]
                if ns in list(["A", "B", "C", "D"]):
                    res += ns
                    try:
                        if "group" in ns.keys():
                            ans = ns["group"]
                            for an in ans:
                                if type in an.keys():
                                    if "text" == type["type"]:
                                        res += type["value"]
                        if "text" in ns.keys():
                            res += ns["value"]
                    except:
                        res += ns
                elif type(ns) == list:
                    for answerlist in ns:
                        if 'text' in answerlist.keys():
                            res += answerlist['value']
            except:
                for ns in answer:
                    # print "ns:::;",ns
                    try:
                        if "group" in ns.keys():
                            ans = ns["group"]
                            for an in ans:
                                if type in an.keys():
                                    if "text" == type["type"]:
                                        res += type["value"]
                        if "text" in ns.keys():
                            res += ns["value"]
                    except:
                        try:
                            res += ns
                        except:
                            for nlist in ns:
                                if 'text' in nlist.keys():
                                    res += nlist['value']

        elif struct == 1 or struct == 2:
            try:
                res += answer[0]
            except:
                # print "answer::::", answer
                res += str(answer)
        elif struct == 3:
            for answer_arr in answer:
                # print "answer_arr:::", answer_arr
                try:
                    for an in answer_arr:
                        type = an["type"]
                        # print "group key",s.keys()
                        if "text" == type:
                            # print "s value::",s["value"]
                            res += an["value"]
                except:
                    for answer_arr in answer:
                        # print "answer_arr:::", answer_arr
                        type = answer_arr["type"]
                        # print "group key",s.keys()
                        if "text" == type:
                            # print "s value::",s["value"]
                            res += answer_arr["value"]

        else:
            for an in answer:
                # print "answer is",an.keys(),answer
                if struct == 4:  #
                    ans = an["group"]
                    for s in ans:
                        type = s["type"]
                        # print "group key",s.keys()
                        if "text" == type:
                            # print "s value::",s["value"]
                            res += s["value"][0]
                else:
                    type = an["type"]
                    if "text" == type:
                        res += an["value"]

    analysis = json["analysis"]
    # print "analysis::;",analysis
    for analy in analysis:
        try:
            if u'type' in analy.keys():
                type = analy["type"]
                if "text" == type:
                    try:
                        if '考点' in analy["value"]:
                            kaodian+=analy["value"]
                        elif '专题' in analy["value"]:
                            zhuanti+=analy["value"]
                        elif '点评' in analy["value"] or '点睛' in analy["value"]:
                            dianping += analy["value"]
                        res += analy["value"]
                    except:
                        print "error analysis"
                        # print "analysis text:::;",analy["value"]
        except:
            res += analy

    return res,kaodian,zhuanti,dianping


def parseJson(input_data):
    data = input_data.split("\t")
    res = ""
    kaodian=''
    zhuanti=''
    dianping=''
    # print data
    qid = data[0]
    struct = int(data[2])
    subject = data[1]

    json_str = eval(data[3])
    json_string = json.dumps(json_str)

    questionjson = json.loads(json_string)
    if struct == 1 or struct == 4 or struct == 3 or struct == 2:
        res,kaodian,zhuanti,dianping= structone(struct, questionjson)

    elif struct == 5 or struct == 7:
        materialjson = questionjson["material"]
        for mater in materialjson:
            if "type" in mater.keys():
                if "text" == mater["type"]:
                    res += mater["value"]

        questions = questionjson["questions"]
        for question in questions:
            res1,kaodian,zhuanti,dianping= structone(struct, question)
            res+=res1
    elif struct == 6:  # translation
        translation = questionjson["translation"]
        questions = questionjson["questions"]

    return res, kaodian, zhuanti, dianping

def predict(qid, subject, type_id, struct, json_data):
    word_for_all_text=[]
    stoplist = []
    with codecs.open('stopwords.txt', 'rb', 'utf-8') as f:
        for words in f.readlines():
            stoplist.append(words.strip())

    question_json = json.loads(json_data)
    content = question_json["content"]
    res = ""
    res = str(content)
    result = str(qid) + "\t" + str(subject) + "\t" + str(struct) + "\t" + res
    text, kaodian, zhuanti, dianping = parseJson(result)

    word.analyze(text, window=5, lower=True)
    w_list = word.get_keywords(num=6, word_min_len=2)
    keylist=[]
    for w in w_list:
        if w.word not in stoplist:
            keylist.append(w.word)

    return ','.join([str(x) for x in keylist]), text
