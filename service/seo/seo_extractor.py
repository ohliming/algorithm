#!/usr/bin/env python
#coding=utf8
import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')
#sys.path.append('../../')
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
import json,math,MySQLdb
import re
import urllib2
from segment.chinese_segmenter import ChineseSegmenter
from common.db_fetcher import DataBaseFetcher
import MySQLdb
import formatter,htmllib
from datasource_opration.kr_article_pipeline import ArticleProcessor
from datasource_opration.kr_media_report_pipeline import MediaReportProcessor
from company_recognize.report_to_company import ComLib
from common import config_es

default_idf_weight = 0.6
threshold = 0.5
baseurl = config_es.webapi["article"]

class SeoExtractor:
    def __init__(self,idf_file,log=None):
        #self.segmenter = ChineseSegmenter('segment/data', 'segment/benz_stop_words_ch+en.gbk')
        f1 = os.path.realpath(os.path.join(os.path.dirname(__file__), 'segment/data'))
        f2 = os.path.realpath(os.path.join(os.path.dirname(__file__), 'segment/benz_stop_words_ch+en.gbk'))
        self.fetcher = DataBaseFetcher()
        self.segmenter = ChineseSegmenter(f1, f2)
        self.idf_dict = self.load_idf_dict(idf_file)
        self.com_dict = {}
        self.organization_dict = {}
        self.investor_dict = {}
        self.tag_set = set()
        self.load_entity_dict()
        self.article_processor = ArticleProcessor()
        self.media_report_processor = MediaReportProcessor()

        self.tag_freq_dict = {}
        self.log = log

    def _send_http_req(self, url):
        try:
            req = urllib2.Request(url)
            hh = urllib2.HTTPHandler()
            opener = urllib2.build_opener(hh)
            reply = opener.open(req, timeout=30)
            r = reply.read()
            reply.close()
            j = json.loads(r)
            return j['data']
        except Exception:
            return {}

    def replace_html(self, s):
        s = s.replace('','')
        s = s.replace('&quot;','"')
        s = s.replace('&amp;','&')
        s = s.replace('&lt;','<')
        s = s.replace('&gt;','>')
        s = s.replace('&nbsp;',' ')
        return s

    def load_idf_dict(self, idf_file):
        idf_dict = {}
        for line in open(idf_file):
            if not line.strip(): continue
            term,df,idf = line.strip().split('\t')
            if term =='GlobalDocLenAvg':
                self.GlobalDocLenAvg = float(idf)
            else:
                idf_dict[term] = float(idf)
        return idf_dict

    def extract(self, title, description, content, tags, title_weight=3, title_coeff=3.0, req_num=100):
        doc_words = {}
        ## 1.seg title
        terms_title = self.segmenter.segment(title)
        doc_len = len(terms_title)
        for term in terms_title:
            if len(term.decode('utf8')) < 2: continue
            if term in doc_words:
                doc_words[term] += title_weight
            else:
                doc_words[term] = title_weight
        ## 2.seg description and content
        descrip = re.sub('<[^>]+>', '', self.replace_html(description))
        content = re.sub('<[^>]+>', '', self.replace_html(content))
        terms_content = self.segmenter.segment(descrip+content)
        doc_len += len(terms_content)
        for term in terms_content:
            if len(term.decode('utf8')) < 2: continue
            if term in doc_words:
                doc_words[term] += 1
            else:
                doc_words[term] = 1

        # normalize tf scope
        for term in doc_words:
            doc_words[term] = math.log(1.0 + doc_words[term], 2.0)

        ## 3.add tags to top and get top100
        tags_vague_dict = {x:1 for x in ['国内创业公司','国外创业公司','国内资讯','国外资讯','大公司晚报','大公司早报','草根思维','专栏文章','生活方式']}
        for tag in tags:
            tag_weight = 2
            if tag in tags_vague_dict:
                tag_weight = 1
            if tag in doc_words:
                doc_words[tag] += tag_weight
            else:
                doc_words[tag] = tag_weight

        ## calc tf-idf score and sort
        word_score = {}
        for term,tf in doc_words.items():
            if term == '36氪': continue
            idf = default_idf_weight
            if term in self.idf_dict:
                idf = self.idf_dict[term]

            if term in self.com_dict or term in self.organization_dict or term in self.tag_set:
                tf *= 2.4
                idf = 0.6 + 0.4 * idf
            word_score[term] = tf * idf

        for term in terms_title:
            if term in word_score:
                word_score[term] *= title_coeff

        sort_words = sorted(word_score.items(), key=lambda x:x[1], reverse=True)
        result_words = map(lambda x:[x[0],x[1]], sort_words[:req_num])

        return result_words

    def extract_article(self, article_id, title_weight=3, title_coeff=3.0, req_num=100):
        ## 1.Check if article_id exist
        db_data = self.fetcher.get_sql_result('select id,article_json from kr_articles where id=%s' % article_id, "mysql_insight")
        if len(db_data) >0:
            try:
                article_obj = json.loads(db_data[0][1], strict=False)
                title = article_obj['title'].encode('utf-8') if 'title' in article_obj and article_obj['title'] else ''
                content_html = article_obj['content'].encode('utf-8') if 'content' in article_obj and article_obj['content'] else ''
                content = re.sub('<[^>]+>', '', content_html)
                summary = article_obj['summary'].encode('utf-8') if 'summary' in article_obj and article_obj['summary'] else ''
                tags = map(lambda x: x.encode('utf-8'),article_obj['tag_list']) if 'tag_list' in article_obj and article_obj['tag_list'] else []
                return self.extract(title, summary, content, tags, title_weight, title_coeff, req_num)
            except:
                pass

        ## 2.Fetch New article
        url = "%s/p/api/post/%s?client_id=ef89a88d739f4f07b85b894d9fbf6c5d49e98180&client_key=9686c23cd8ee1d865e29204fb869c3796d1d73b1" %(baseurl,article_id)
        resp = self._send_http_req(url)
        if not resp:
            return []
        ## 更新kr_article表
        try:
            ## 已发布的文章才入库
            if resp['published_at']:
                self.article_processor.process_article(article_id)
                self.media_report_processor.update_media_report_table(article_id)
        except Exception,e:
            self.log.info("[Article into kr_article id-%s]:error-[%s]" %(article_id, str(e)))
            pass

        title = resp['title'].encode('utf-8') if 'title' in resp and resp['title'] else ''
        summary = resp['summary'].encode('utf-8') if 'summary' in resp and resp['summary'] else ''
        content_html = resp['content'].encode('utf-8') if 'content' in resp and resp['content'] else ''
        content = re.sub('<[^>]+>', '', content_html)
        tags = map(lambda x: x.encode('utf-8'),resp['tag_list']) if 'tag_list' in resp and resp['tag_list'] else []
        return self.extract(title, summary, content, tags, title_weight, title_coeff, req_num)

    def extract_content(self,article_content, tag_num=100):
        return self.extract('', '', article_content, [], req_num=tag_num)

    def load_entity_dict(self):
        self.com_dict = {}
        # handle company
        company_file = '../../company_recognize/com_name2id.txt'
        with open(company_file) as com_f:
            for line in com_f:
                tokens = line.strip().split('\t')
                if len(tokens) != 2:
                    continue
                self.com_dict[tokens[0]] = tokens[1]

        # handle organization
        self.organization_dict = {}
        db_organization = self.fetcher.get_sql_result('select distinct name_abbr,attach_id from organization where name_abbr != \'\'','mysql_crm')
        for pos in range(len(db_organization)):
            self.organization_dict[db_organization[pos][0]] = db_organization[pos][1]

        # handle investor
        self.investor_dict = {}
        db_investor = self.fetcher.get_sql_result('select distinct attach_uid,name from investor where investor_type in (10,20) and name !=\'\'','mysql_crm')
        for pos in range(len(db_investor)):
            self.investor_dict[db_investor[pos][1]] = db_investor[pos][0]

        # handle industry and tag
        self.tag_set = set()
        tag_rows = self.fetcher.get_sql_result('select name from dict_industry', 'mysql_crm')
        for tag_row in tag_rows:
            self.tag_set.add(tag_row[0].lower().strip())
        tag_rows = self.fetcher.get_sql_result('select tag from top_tag', 'mysql_crm')
        for tag_row in tag_rows:
            self.tag_set.add(tag_row[0].lower().strip())
        tag_rows = self.fetcher.get_sql_result('select tag,count(*) as cnt from company_tag group by tag having cnt>10', 'mysql_crm')
        for tag_row in tag_rows:
            self.tag_set.add(tag_row[0].lower().strip())

    def entity_name2id(self,article_id,entity_dict):
        result_words = self.extract_article(article_id)
        word_dict = {x[0]:x[1] for x in result_words}
        filter_word_dict = {x[0]:entity_dict[x[0]] for x in result_words if x[0] in entity_dict and x[1] > threshold}
        id_dict = {}
        for key,value in filter_word_dict.items():
            if value in id_dict:
                id_dict[value] += word_dict[key]
            else:
                id_dict[value] = word_dict[key]

        sort_list = sorted(id_dict.iteritems(), key=lambda x:x[1], reverse=True)
        if len(sort_list) > 5:
            list_entity = [x[0] for x in sort_list[:5]]
        else:
            list_entity = [x[0] for x in sort_list ]

        return list_entity

    # SEO Tags词库
    def load_seo_tags(self):
        rows = self.fetcher.get_sql_result("select uri,keyword from seo_tags ",'mysql_sitemgr')
        return rows

    # 只保留SEO Tags词库中的Term
    def filter_words_in_seo_tags(self, article_id, seo_tags):
        words_in_seo_tags =[]
        sort_words = self.extract_article(article_id)
        tags_dict = {x[1]:x[0] for x in seo_tags}
        #print json.dumps(sort_words,ensure_ascii=False)
        for i in range(0,len(sort_words)):
            if sort_words[i][0] not in tags_dict:
                pass
            else:
                uri = tags_dict.get(sort_words[i][0])
                key_uri = [sort_words[i][0],uri]
                words_in_seo_tags.append(key_uri)
                #print json.dumps(sort_words[i],ensure_ascii=False).encode('utf8')
        return words_in_seo_tags

    # 过滤去除Anchor Term
    def filter_anchor_words(self, article_id, words_in_seo_tags):
        content_html = ''
        try:
            db_data = self.fetcher.get_sql_result('select id,article_json from kr_articles where id=%s' % article_id, "mysql_insight")
            if len(db_data) >0:
                article_obj = json.loads(db_data[0][1], strict=False)
                content_html = article_obj['content'].encode('utf-8') if 'content' in article_obj and article_obj['content'] else ''
            else:
                url = "%s/p/api/post/%s?client_id=ef89a88d739f4f07b85b894d9fbf6c5d49e98180&client_key=9686c23cd8ee1d865e29204fb869c3796d1d73b1" %(baseurl, article_id)
                resp = self._send_http_req(url)
                content_html = resp['content'].encode('utf-8') if 'content' in resp and resp['content'] else ''
        except: return []

        relink ='<a href=".*?">.*?</a>'
        relink2 = '>.*?</a>'
        links = re.findall(relink,content_html)
        anchor_words  = []
        for link in links :
            anchor_text = re.findall(relink2,link)
            str_anchor_text = ''.join(anchor_text)
            str_anchor_text = re.sub('>|</a>','',str_anchor_text)
            anchor_words.append(str_anchor_text)

        for i in  range(0,len(words_in_seo_tags)-1):
            if words_in_seo_tags[i] in anchor_words:
                words_in_seo_tags.remove(words_in_seo_tags[i])
        return words_in_seo_tags

    def get_tags_result(self,article_id, req_num=3):
        seo_tags = self.load_seo_tags()
        words_in_seo_tags = self.filter_words_in_seo_tags(article_id, seo_tags)
        words_without_anchor = self.filter_anchor_words(article_id, words_in_seo_tags)

        tag_num = 0
        tags_result = []
        for num in range(0,len(words_without_anchor)-1):
            word = words_without_anchor[num][0]
            word_uri = words_without_anchor[num]
            if word not in self.tag_freq_dict:
                self.tag_freq_dict[word] = 1
                tags_result.append(word_uri)
            elif self.tag_freq_dict[word] < 1000:
                self.tag_freq_dict[word] += 1
                tags_result.append(word_uri)
            tag_num += 1
            if tag_num == req_num : break
        return tags_result

if __name__ == '__main__':
    seo_extractor = SeoExtractor('com_df_idf')
    ret = seo_extractor.extract_article(sys.argv[1])
    #print "%s" % json.dumps(ret, ensure_ascii=False).encode('utf8')
    com_dict,organization_dict,investor_dict = seo_extractor.load_entity_dict()
    com_list = seo_extractor.entity_name2id(sys.argv[1],com_dict)
    organization_list = seo_extractor.entity_name2id(sys.argv[1],organization_dict)
    investor_list = seo_extractor.entity_name2id(sys.argv[1],investor_dict)
    seo_tags = seo_extractor.load_seo_tags()
    words_in_seo_tags = seo_extractor.filter_words_in_seo_tags(sys.argv[1], seo_tags)
    words_without_anchor = seo_extractor.filter_anchor_words(sys.argv[1], words_in_seo_tags)

    print "%s" % json.dumps(com_list, ensure_ascii=False).encode('utf8')
    print "%s" % json.dumps(organization_list, ensure_ascii=False).encode('utf8')
    print "%s" % json.dumps(investor_list, ensure_ascii=False).encode('utf8')
