# -*- coding:utf-8 -*- 

"""
Created on Mon Dec 15 10:38:02 2015
@author: liming
"""

import time,datetime
import os,sys,re
import json
import urllib
from urllib2 import Request, urlopen, URLError, HTTPError  #导入urllib2模块  

sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../seo')))
from seo_extractor import SeoExtractor
from common.db_fetcher import DataBaseFetcher

mysql_fetcher = DataBaseFetcher()

threshold = 15.85 # 阈值

class HotsFind(object):

    ch_title_dict = {}
    cache_weight_dict = {}

    def __init__(self,keyword_file):
        self.seo_extractor = SeoExtractor('../seo/com_df_idf')
        self.keyword_set,self.verb_set = self.read_keywords(keyword_file)
        self.entity_dict = self.load_entity_dict()

    def clear_history_init(self,keyword_file):
        self.seo_extractor = SeoExtractor('../seo/com_df_idf')
        self.keyword_set,self.verb_set = self.read_keywords(keyword_file)
        self.entity_dict = self.load_entity_dict()
        self.ch_title_dict.clear()
        self.cache_weight_dict.clear()

    def get_article_weight(self,str_title):
        data_page = self.seo_extractor.extract(str_title,'','',[])
        if (data_page is None) or len(data_page) < 1:
            return None
 
        return [x for x in data_page if len(x[0]) > 3]

    def read_keywords(self,keyword_file):
        words_list = []
        v_word = []
        with open(keyword_file) as key_f:
            for line in key_f:
                arr_words = line.strip().split(',')
                for pos in range(len(arr_words)):
                    words_list.append(arr_words[pos])

        with open('verb.txt') as verb_f:
            for line in verb_f:
                str_word = line.strip()
                v_word.append(str_word)

        return set(words_list),set(v_word)

    def read_articles_title(self,title_data):
        dict_title = {}
        dict_date = {}
        dict_en = {}
        n_count = 0
        with open(title_data) as f:
            for line in f:
                arr_info = line.strip().split('\t')
                if len(arr_info) !=4:
                    continue 
                try:
                    url = str(arr_info[1])
                    dict_title[url] = arr_info[2]
                    dict_date[url] = arr_info[0]
                    dict_en[url] = int(arr_info[3])
                except:
                    continue

        return dict_title,dict_date,dict_en
    
    def load_entity_dict(self):
        entity_dict = set()
        # handle company
        company_file = './com_name2id.txt'
        with open(company_file) as com_f:
            for line in com_f:
                tokens = line.strip().split('\t')
                if len(tokens) != 2:
                    continue
                entity_dict.add(tokens[0])

        # handle industry
        db_industry = mysql_fetcher.get_sql_result('select distinct name from dict_industry','mysql_crm')
        for row_industry in db_industry:
            entity_dict.add(row_industry[0])

        # handle organization
        db_organization = mysql_fetcher.get_sql_result('select distinct name_abbr from organization','mysql_crm')
        for row_organization in db_organization:
            entity_dict.add(row_organization[0])

        return entity_dict


    def cal_vector_inner(self,vector1,v2_dict):
        dict_center = {}
        v1_dict = {x[0]:x[1] for x in vector1}

        inner_v = 0.0
        for item in v1_dict:
            if item in self.verb_set or re.match(r'[+-]?\d+$',item):
                continue

            if item in v2_dict:
                inner_v += v2_dict[item] * v1_dict[item]
                dict_center[item] = (float(v2_dict[item]) + float(v1_dict[item]))/2
            else:
                dict_center[item] = v1_dict[item]/2

        return inner_v,dict_center

    def is_hot(self,weight_list):
        is_hot = False
        for pos in range(len(weight_list)):
            if weight_list[pos][0] in self.keyword_set:
                is_hot = True
                break

        return is_hot

    def translate_chinese(self,input_en):
        process_en = input_en.strip()
        quoteStr = urllib.quote(process_en)
        url = 'http://openapi.baidu.com/public/2.0/bmt/translate?client_id=WtzfFYTtXyTocv7wjUrfGR9W&q=' + quoteStr + '&from=auto&to=zh'
        try: 
            #调用百度翻译API进行批量翻译 
            resultPage = urlopen(url)                                
        except HTTPError as e:  
            print('The server couldn\'t fulfill the request.')  
            print('Error code: ', e.code)
            return None
        except URLError as e:  
            print('We failed to reach a server.')  
            print('Reason: ', e.reason)
            return None
        except Exception, e:
            print 'translate error.'  
            print e 
            return None

        #取得翻译的结果，翻译的结果是json格式  
        resultJason = resultPage.read().decode('utf-8')                
        json_dict = None   
        try:  
            #将json格式的结果转换成Python的字典结构
            json_dict = json.loads(resultJason) 
        except Exception, e:  
            print 'loads Json error.'  
            print e  
            return None 

        if u'trans_result' in json_dict:
            return json_dict["trans_result"][0]["dst"]
        else:
            return None

    def get_weight_list(self,title,url):
        if url in self.cache_weight_dict:
            weight_list = self.cache_weight_dict[url]
        else:
            weight_list = self.get_article_weight(title)
            self.cache_weight_dict[url] = weight_list

        return weight_list

    def find_hotspot(self,url_title,url_date,url_en):
        hotspot_dict = {}
        center_vector = {} # 中心向量
        for url,title in url_title.items():
            target_title,update_time,target_url = title,url_date[url],url

            # 去掉重名的title 判断
            if target_title in hotspot_dict or target_title =='' or title is None:
                continue

            cut_title = title
            if url_en[url] == 1:
                if url in self.ch_title_dict:
                	cut_title = self.ch_title_dict[url]
                else:
                	cut_title = self.translate_chinese(title)
                	self.ch_title_dict[url] = cut_title

            weight_list =  self.get_weight_list(cut_title,url)
            b_hot = self.is_hot(weight_list) if weight_list is not None else False
            if b_hot is False and (url_en[url] == 0):
                continue

            for pos in range(len(weight_list)):
                if weight_list[pos][0] in self.entity_dict:
                    weight_list[pos][1] *= 2

            is_merge = False
            dict_center = {}
            v_threshold = threshold
            dict_center = {x[0]:x[1] for x in weight_list}
            for cent_url in center_vector:
                inner_v,dict_v  = self.cal_vector_inner(weight_list,center_vector[cent_url])
                if inner_v > v_threshold:
                    target_title ,target_url= url_title[cent_url],cent_url
                    v_threshold,dict_center,is_merge = inner_v,dict_v,True

            if is_merge == False:
                hotspot_dict[target_title] = {}
                hotspot_dict[target_title][url] = title
                center_vector[target_url] = dict_center
                hotspot_dict[target_title]['update_time'] = update_time
                hotspot_dict[target_title]['report_time'] = update_time
            else:
                center_vector.pop(target_url)
                if cmp(update_time,hotspot_dict[target_title]['report_time']) < 0:
                    hotspot_dict[target_title]['report_time'] = update_time

                if cmp(update_time,hotspot_dict[target_title]['update_time']) > 0:
                    hotspot_dict[title] = hotspot_dict[target_title]
                    hotspot_dict.pop(target_title)
                    target_title,target_url = title,url
                else:
                    update_time = hotspot_dict[target_title]['update_time']
                
                center_vector[target_url] = dict_center
                hotspot_dict[target_title][url] = title
                hotspot_dict[target_title]['update_time'] = update_time
        return hotspot_dict

def main():
    hotfind = HotsFind('./keywords.txt')
    str_today =  time.strftime('%Y-%m-%d',time.localtime(time.time()))
    data_titile = './articles_snatch/data/title_list.%s' % str_today
    url_title,url_date,url_en = hotfind.read_articles_title(data_titile)
    dict_hots = hotfind.find_hotspot(url_title,url_date,url_en)
    ret = json.dumps(dict_hots, ensure_ascii=False).encode('utf8')
    print ret
    
if __name__=="__main__":
    main()
