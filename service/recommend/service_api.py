#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
import time,datetime
import recommend,recommend_text
from recommend import RecommArticles
from recommend_text import TextAnalysis

class ServiceAPI:
    '''
    ## 用户自定义的接口
    ## 1.新增接口名称需要增加至cmds列表
    ## 2.新增接口逻辑需要增加handle()函数
    ## 3.handle函数返回Str或Json格式: {"code':0,"msg":"ok","data":{}}
    '''
    cmds = ['alive','recommend','update']
    m_recommend = RecommArticles()
    forward_index_dict = {}
    revert_index_dict = {}
    meta_dict = {}
    def __init__(self, log):
        self.log = log
        self.update_source_dict()
        self.log.info('Service Initialized: ForwardIndex(%s), InvertIndex(%s), Meta(%s)' % (len(self.forward_index_dict),len(self.revert_index_dict),len(self.meta_dict)))

    def update_source_dict(self):
        update_time_range = datetime.date.today() - datetime.timedelta(days=recommend.kTimeRange)
        self.m_recommend.m_text_analysis.load_entity_dict()
        self.forward_index_dict,self.revert_index_dict,self.meta_dict = self.m_recommend.load_media_dict(update_time_range)

    def handle(self, params):
        if not params['cmd'] in ServiceAPI.cmds:
            return {'msg':'no such method %s!'} % params['cmd']
        ret = {}
        ret['msg'] = 'ok'
        if params['cmd'] == 'alive':
            return ret
        elif params['cmd'] == 'update':
            self.update_source_dict()
            return ret
        elif params['cmd'] == 'recommend':
            if 'id' not in params or 'publish' not in params:
                ret['msg'] = 'fail'
                self.log.error('Exception recommend meida article: %s' %(e))
                return ret
            media_id = int(params['id'])
            publish = str(params['publish'])
            result,is_cached = self.m_recommend.get_cache_or_temp(media_id,6)
            if is_cached == True:
                self.log.info('Cached: %s' % media_id)
            else:
                # 计算推荐结果
                update_time_range = datetime.date.today() - datetime.timedelta(days=recommend.kTimeRange)
                time_publish = time.strptime(publish,'%Y-%m-%d')
                datetime_publish = datetime.datetime(time_publish[0],time_publish[1],time_publish[2])
                list_result = self.m_recommend.recommend_media(media_id,datetime_publish,update_time_range,self.forward_index_dict,self.revert_index_dict,self.meta_dict,6)
                result = map(lambda x: x.split(':')[0], list_result)

                # 更新正排与倒排索引
                media_dict = self.m_recommend.m_text_analysis.get_media_dict(media_id)
                text_sum_quares = 0.0
                for weight in media_dict.values():
                    text_sum_quares += weight**2
                self.forward_index_dict[media_id] = media_dict
                self.meta_dict[media_id] = (datetime_publish, None, text_sum_quares)
                for term,weight in media_dict.items():
                    if term not in self.revert_index_dict:
                        self.revert_index_dict[term] = {}
                    self.revert_index_dict[term][media_id] = weight
            return result

if __name__ == '__main__':
    pass

