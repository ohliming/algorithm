# -*- coding:utf-8 -*-
from __future__ import division

import sys,copy,json,re,heapq,math,MySQLdb
import time,datetime,os

sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
from segment.chinese_segmenter import ChineseSegmenter
from common.db_crud import DbCrud
from common import config

col_num = 3
re_rule = [r'^[1-9].*万',r'.*亿',r'.*个',r'^2015',r'^2017',r'^2016',r'.*\..*',r'^[1-9]月',r'^[1-9].*年',r'^[1-9]日'] # 规则列表,正则表达式

threshold = 20

class ChineseRecognition(object):
    """docstring for ChineseRecognition"""
    words_common = ['发布','推出','研发','启动','新品','新产品','版本','业务','进军','入股','战略','上线','领投','估值','分拆',\
    '融资','投资','美元','人民币','种子轮','天使轮','PreA','A轮','B轮','C轮','D轮','E轮','IPO','上市','私有化','收购','并购','合并','倒闭']

    def __init__(self,com_name = 'com_name2id.txt',com_filter= 'com_filter.txt'):
        f1 = os.path.realpath(os.path.join(os.path.dirname(__file__), 'segment/data'))
        f2 = os.path.realpath(os.path.join(os.path.dirname(__file__), 'segment/benz_stop_words_ch+en.gbk'))
        self.segmenter = ChineseSegmenter(f1, f2)
        self.set_company = self.org_company_cache(com_name)
        self.set_filter = self.filter_company_cache(com_filter)

        # 向前词频 向后词频
        self.front_dict, self.back_dict = self.cache_bound_words('./train',self.set_company)
        self.set_internet = self.cache_internet_name()
        self.set_crf = self.cache_crf_model_words()

        self.db_crm = DbCrud(
                            config.mysql_crm["host"],
                            config.mysql_crm["user"],
                            config.mysql_crm["pwd"],
                            config.mysql_crm["db"])

    def cache_internet_name(self,internet_name = './internet_name.txt'):
        internet_list = []
        with open(internet_name) as internet_f:
            for line in internet_f:
                str_name = line.strip()
                internet_list.append(str_name)

        return set(internet_list)

    def cache_crf_model_words(self,crf_result='result.txt'):
        crf_list = []
        with open(crf_result) as crf_f:
            for line in crf_f:
                str_content = line.strip()
                if str_content[-1:] == '1':
                    arr_content = str_content.split('TC_')
                    str_com = arr_content[0].strip()
                    crf_list.append(str_com)

        return set(crf_list)

    def cache_bound_words(self,dir_train,com_set):
        front_dict = {} # 向前词频
        back_dict = {} # 向后词频
        for file_name in os.listdir(dir_train):
            abs_name = os.path.join('%s/%s' % (dir_train,file_name))
            with open(abs_name) as abs_f:
                for line in abs_f:
                    arr_content =  line.strip().split('\t')
                    if len(arr_content) < col_num: continue
                    terms = self.segmenter.segment(arr_content[2])
                    front_item = ''
                    for pos in range(len(terms)):
                        if len(terms[pos]) < 4: continue

                        if front_item in com_set:
                            if terms[pos] not in back_dict: 
                                back_dict[terms[pos]] = 1
                            else:
                                back_dict[terms[pos]] += 1

                        if terms[pos] in com_set and front_item != '':
                            if front_item not in front_dict:
                                front_dict[front_item] = 1
                            else:
                                front_dict[front_item] += 1

                        front_item = terms[pos]

        return front_dict, back_dict

    def org_company_cache(self,com_name):
        company_list = []
        with open(com_name) as com_f:
            for line in com_f:
                arr_com = line.strip().split('\t')
                company_list.append(arr_com[0])
        return set(company_list)

    def filter_company_cache(self,filter_name):
        filter_list = []
        with open(filter_name) as filter_f:
            for line in filter_f:
                common = line.strip()
                filter_list.append(common)

        return set(filter_list)

    # 过滤噪音条件过则
    def re_filter_noise(self,str_content):
        b_flag = True
        for item  in re_rule:
            if re.match(item,str_content):
                b_flag = False
                break

        return b_flag

    def write_entity_filter(self,set_company,internet_name = './internet_name.txt'):
        with open(internet_name,'a') as filter_f:
            for item in set_company:
                if item not in self.set_internet:
                    filter_f.write('%s\n' % item)

    def store_database_entity(self,set_company,url_dict,title_dict):
        for item in set_company:
            url = url_dict[item] if item in url_dict else ''
            title = title_dict[item] if item in title_dict else ''
            self.db_crm.insert('insert into entity_recognition(name,title,url) values(\'%s\',\'%s\',\'%s\')' % (item,title,url))

    def find_possible_company(self,process_file):
        company_list = []
        url_dict = {}
        title_dict = {}
        with open(process_file) as pro_f:
            for line in pro_f:
                arr_content = line.strip().split('\t')
                if len(arr_content) < col_num: continue
                str_content, url  = arr_content[2],arr_content[1]
                terms = self.segmenter.segment(str_content)
                front_item = ''
                for item in terms:
                    if len(item) < 4: continue

                    item_filter = (item not in self.set_filter) and (item not in self.set_company) \
                                    and self.re_filter_noise(item) and (item not in self.words_common) \
                                    and  item not in self.set_internet
                    if front_item in self.front_dict and item_filter:
                        if self.front_dict[front_item] > threshold:
                            company_list.append(item)

                    front_filter = (front_item != '') and (front_item not in self.set_filter) \
                                     and (front_item not in self.set_company) and self.re_filter_noise(front_item) \
                                     and front_item not in self.words_common and front_item not in self.set_internet
                    if item in self.back_dict and front_filter:
                        if self.back_dict[item] > threshold:
                            company_list.append(front_item)

                    if item in self.words_common and front_filter: company_list.append(front_item)
                    if item in self.set_crf and item_filter : company_list.append(item)
                    url_dict[item], title_dict[item] = url, str_content
                    front_item = item

        set_company =  set(company_list)
        self.write_entity_filter(set_company)
        self.store_database_entity(set_company,url_dict,title_dict)
        return list(set_company)

if __name__=='__main__':
    ch_recognition = ChineseRecognition()
    out_title_file = './test/title_list.%s' % time.strftime('%Y-%m-%d',time.localtime(time.time()))
    company_list = ch_recognition.find_possible_company(out_title_file)
    print "%s" % json.dumps(company_list, ensure_ascii=False)
