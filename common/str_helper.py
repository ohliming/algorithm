#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import traceback


def strQ2B(ustring):
    """全角转半角"""
    ustring = unicode(ustring)
    return "".join([_Q2B(uchar) for uchar in ustring])
    
def strB2Q(ustring):
    """半角转全角"""
    ustring = unicode(ustring)
    return "".join([_B2Q(uchar) for uchar in ustring])

def has_chinese(ustring):
    found = False
    ustring = unicode(ustring)
    for uc in ustring:
        if _is_chinese(uc):
            found = True
            break
    return found

def has_only_w(ustring):
    rech = re.match('^\w+$', ustring)
    if rech:
        return True
    return False
    

def _Q2B(uchar):
    inside_code=ord(uchar)
    if inside_code == 12288:                              #全角空格直接转换            
        inside_code = 32
    elif (inside_code >= 65281 and inside_code <= 65374): #全角字符（除空格）根据关系转化
        inside_code -= 65248
    return unichr(inside_code)

def _B2Q(uchar):
    inside_code=ord(uchar)
    if inside_code == 32:                                 #半角空格直接转化                  
        inside_code = 12288
    elif inside_code >= 32 and inside_code <= 126:        #半角字符（除空格）根据关系转化
        inside_code += 65248
    return unichr(inside_code)

def _is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
        return True
    else:
        return False
 
def _is_number(uchar):
    """判断一个unicode是否是数字"""
    if uchar >= u'\u0030' and uchar<=u'\u0039':
        return True
    else:
        return False
 
def _is_alphabet(uchar):
    """判断一个unicode是否是英文字母"""
    if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
        return True
    else:
        return False
 
def _is_other(uchar):
    """判断是否非汉字，数字和英文字符"""
    if not (_is_chinese(uchar) or _is_number(uchar) or _is_alphabet(uchar)):
        return True
    else:
        return False





## test
#a='ａｂｃ［］（）１２３'
#print a
#print strQ2B(a)



