#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import time,math,chardet,json
from seo_extractor import SeoExtractor

class ServiceAPI:
    '''
    ## 用户自定义的接口
    ## 1.新增接口名称需要增加至cmds列表
    ## 2.新增接口逻辑需要增加handle()函数
    ## 3.handle函数返回Str或Json格式: {"code':0,"msg":"ok","data":{}}
    ## extractKeyWords: 给定文章内容提取关键词
    ## extractArticle: 给定文章ID提取关键词
    ## extractTags：给定文章ID提取个数最多的SEO Tags范围内的Term
    '''
    cmds = ['alive', 'extractKeyWords', 'extractArticle', 'extractTags', 'entityId', 'update']
    def __init__(self, log):
        self.log = log
        self.idf_file = './com_df_idf'
        self.seo_extractor = SeoExtractor(self.idf_file, log)
        self.id_com_dict = {}
        self.id_organization_dict = {}
        self.id_investro_dict = {}
        self.log.info("Service Initialized.")


    def handle(self, params):
        if not params['cmd'] in ServiceAPI.cmds:
            return {'msg':'no such method %s!'} % params['cmd']
        ret = {}
        if params['cmd'] == 'alive':
            ret['msg'] = 'ok'
        elif params['cmd'] == 'extractKeyWords':
            ret['msg'] = 'ok'
            ret['data'] = []
            try:
                self.log.info('article=%s' %params['article'])
                article_obj = json.loads(params['article'], encoding="utf-8")
                ret['data'] = self.seo_extractor.extract(article_obj['title'],article_obj['descrip'], article_obj['content'],article_obj['tags'])
            except Exception,e:
                ret['msg'] = 'fail'
                self.log.error('Exception Seo extractor : %s' %(e))
        elif params['cmd'] == 'extractArticle':
            ret = {}
            ret['msg'] = 'ok'
            ret['data'] = []
            try:
                tag_num = int(params['tag_num']) if 'tag_num' in params and params['tag_num'] else 100
                tag_num = 100 if tag_num > 100 else tag_num
                if 'id' in params:
                    if tag_num < 10:
                        ret['data'] = self.seo_extractor.extract_article(int(params['id']), title_weight=2, title_coeff=1.0, req_num=tag_num)
                    else:
                        ret['data'] = self.seo_extractor.extract_article(int(params['id']), title_weight=2, title_coeff=2.0, req_num=tag_num)
                elif 'content' in params:
                    ret['data'] = self.seo_extractor.extract_content(params['content'], tag_num)
            except Exception,e:
                ret['msg'] = 'fail'
                self.log.error('Exception Seo extractor : %s' %(e))
        elif params['cmd'] == 'extractTags':
            article_id = params['id']
            ret['msg'] = 'ok'
            ret['data'] = []
            try:
                tag_num = int(params['tag_num']) if 'tag_num' in params and params['tag_num'] else 3
                tag_num = tag_num if tag_num < 100 else 100
                tags_result = self.seo_extractor.get_tags_result(article_id, req_num=tag_num)
                ret['data'] = tags_result
            except Exception,e:
                ret['msg'] = 'fail'
                self.log.error('Exception seo extractor: %s' % (e))
        elif params['cmd'] == 'update':
            self.seo_extractor.idf_dict = self.seo_extractor.load_idf_dict(self.idf_file)
            self.seo_extractor.load_entity_dict()
            ret['msg'] = 'ok'
            ret['data'] = 'entity dict update'
        elif params['cmd'] == 'entityId':
            article_id = params['id']
            ret['msg'] = 'ok'
            if article_id in self.id_com_dict:
                ret['company'] = self.id_com_dict[article_id]
            else:
                ret_company = self.seo_extractor.entity_name2id(article_id, self.seo_extractor.com_dict)
                self.id_com_dict[article_id],ret['company'] = ret_company,ret_company

            if article_id in self.id_organization_dict:
                ret['organization'] = self.id_organization_dict[article_id]
            else:
                ret_organization = self.seo_extractor.entity_name2id(article_id, self.seo_extractor.organization_dict)
                self.id_organization_dict[article_id],ret['organization'] = ret_organization,ret_organization

            if article_id in self.id_investro_dict:
                ret['investor'] = self.id_investro_dict[article_id]
            else:
                ret_investor = self.seo_extractor.entity_name2id(article_id, self.seo_extractor.investor_dict)
                self.id_investro_dict[article_id],ret['investor'] = ret_investor,ret_investor

        return ret


if __name__ == '__main__':
    pass
