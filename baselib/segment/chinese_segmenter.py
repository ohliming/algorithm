#!/usr/bin/env python
#coding=utf8
import sys,re
from TCWordSeg import *

class ChineseSegmenter:

    seg_handle = ''

    def __init__(self,seg_dict, stop_word=None, filter_word=None):
        TCInitSeg(seg_dict)
        SEG_MODE = TC_CN|TC_USR|TC_S2D|TC_U2L|TC_T2S
        self.seg_handle = TCCreateSegHandle(SEG_MODE)

        self.stop_word_dict = {}
        if stop_word:
            file = open(stop_word)
            for line in file:
                line = line.lower().strip('\r\n')
                if len(line) == 0: continue
                self.stop_word_dict[line] = 0
            file.close()
        self.filter_word_dict = {}
        if filter_word:
            for itr_filter_word in filter_word.split(','):
                file = open(itr_filter_word)
                for line in file:
                    line = line.lower().strip()
                    if len(line) == 0: continue
                    self.filter_word_dict[line] = 0
                file.close()

    def normalize(self,text):
        seg_result = self.segment(text, is_orig=True)
        return ''.join(seg_result)

    def segment(self, text, is_orig=False):
        text = text.strip().replace('\t',' ').replace('\n',' ')
        text = text.decode('utf-8','replace').encode('gbk','replace')
        TCSegment(self.seg_handle, text)
        rescount = TCGetResultCnt(self.seg_handle)
        seg_result = []
        for i in range(rescount):
            word = TCGetWordAt(self.seg_handle, i)
            if not is_orig:
                if self.stop_word_dict.has_key(word): continue
                if len(self.filter_word_dict) > 0 and not self.filter_word_dict.has_key(word): continue
            word = word.decode('gbk','replace').encode('utf-8','replace')
            seg_result.append(word)
        return seg_result

    def close(self):
        TCCloseSegHandle(self.seg_handle)
        TCUnInitSeg()

if __name__=='__main__':
    text = '“Boss直聘”要用相亲交友的方式把老板和求职者撮合到一起'
    chunker1 = ChineseSegmenter('data')
    chunker2 = ChineseSegmenter('data', 'benz_stop_words_ch+en.gbk')
    for chunker in [chunker1, chunker2]:
        tokens = chunker.segment(text)
        print '|'.join(tokens)