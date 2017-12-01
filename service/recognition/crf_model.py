# -*- coding:utf-8 -*-
from __future__ import division

import sys,copy,json,re,heapq,math,MySQLdb
import time,datetime,os

sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
from ch_property_segmenter import ChineseSegmenterProperty

property_dict = {
1:'TC_A',  # 形容词
2:'TC_AD',# 副形词
3:'TC_AN',# 名形词
4:'TC_B',# 区别词
5:'TC_C',# 连词
6:'TC_D',# 副词
7:'TC_E',# 叹词
8:'TC_F',# 方位词
9:'TC_G',# 语素词
10:'TC_H',# 前接成分
11:'TC_I',# 成语
12:'TC_J',# 简称略语
13:'TC_K',# 后接成分
14:'TC_L',# 习用语
15:'TC_M',# 数词
16:'TC_N',# 名词
17:'TC_NR',# 人名
18:'TC_NRF',# 姓
19:'TC_NRG',# 名
20:'TC_NS',# 地名
21:'TC_NT',# 机构团体
22:'TC_NZ',# 其他专名
23:'TC_NX',# 非汉字串
24:'TC_O',# 拟声词
25:'TC_P',# 介词
26:'TC_Q',# 量词
27:'TC_R',# 代词
28:'TC_S',# 处所词
29:'TC_T',# 时间词
30:'TC_U',# 助词
31:'TC_V',# 动词
32:'TC_VD',# 副动词
33:'TC_VN',# 名动词
34:'TC_W',# 标点符号
35:'TC_X',# 非语素字
36:'TC_Y',# 语气词
37:'TC_Z',# 状态词
38:'TC_AG',# 形语素
39:'TC_BG',# 区别语素
40:'TC_DG',# 副语素
41:'TC_MG',# 数词性语素
42:'TC_NG',# 名语素
43:'TC_QG',# 量语素
44:'TC_RG',# 代语素
45:'TC_TG',# 时语素
46:'TC_VG',# 动语素
47:'TC_YG',# 语气词语素
48:'TC_ZG',# 状态词语素
49:'TC_SOS',# 开始词
0:'TC_UNK',# 未知词性

50:'TC_WWW',# URL
51:'TC_TELE',# 电话号码
52:'TC_EMAIL'# email
}

class CrfProcess(object):
    """docstring for CrfProcess"""
    def __init__(self,com_file='com_name2id.txt'):
        f1 = os.path.realpath(os.path.join(os.path.dirname(__file__), 'segment/data'))
        f2 = os.path.realpath(os.path.join(os.path.dirname(__file__), 'segment/benz_stop_words_ch+en.gbk'))
        self.ch_segmenter = ChineseSegmenterProperty(f1,f2)
        com_list = []
        with open(com_file) as com_f:
            for line in com_f:
                arr_com = line.strip().split('\t')
                if len(arr_com) != 2: continue 
                com_list.append(arr_com[0])
        self.set_com = set(com_list)

    # 如果flag is tag process
    def train_test(self,dir_content,output_name,flag = 'learn'):
        train_handle = open(output_name,'w')
        for file_name in os.listdir(dir_content):
            abs_name = os.path.join('%s/%s' % (dir_content,file_name))
            with open(abs_name) as train_f:
                for line in train_f:
                    arr_content = line.strip().split('\t')
                    if len(arr_content) < 3: continue
                    str_content = arr_content[2]
                    terms = self.ch_segmenter.segment(str_content)
                    for item in terms:
                        if len(item) != 2: continue
                        str_pro = property_dict[item[1]] if item[1] in property_dict else 'TC_UNK'
                        word = item[0]
                        tag =  1 if word in self.set_com else 0 
                        if flag == 'learn':
                            train_handle.write('%s %s %s\n' % (word,str_pro,tag))
                        else:
                            train_handle.write('%s %s\n' % (word,str_pro))
                    train_handle.write('\n')
        train_handle.close()

if __name__=='__main__':
    if len(sys.argv) < 4:
        sys.exit()

    crf_pro = CrfProcess()
    pro_dir = str(sys.argv[1])
    output_file = str(sys.argv[2])
    target = str(sys.argv[3])
    crf_pro.train_test(pro_dir,output_file,target)
