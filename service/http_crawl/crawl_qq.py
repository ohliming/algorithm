#!/usr/bin/python
# -*- coding: utf-8 -*- 
import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )

import json,urllib,urllib2,json,chardet,re,os,time
from http_request import *

from bs4 import BeautifulSoup

sys.path.append('../../')
from common.db_fetcher import DataBaseFetcher
db_fetcher = DataBaseFetcher()

qq_host = 'https://qun.qq.com/' # css host
qq_url = 'https://qun.qq.com/cgi-bin/qun_mgr/search_group_members' # main page

qq_qun = '32415808'
max_num = 2000
curl_command = "curl 'https://qun.qq.com/cgi-bin/qun_mgr/search_group_members' -H 'cookie: pgv_pvi=9242132480; pgv_pvid=4599621902; RK=W7qZWPucdN; \
ptcz=d432b08c7964b08d417654ee7c11d91f17871c0bbd9caf2713a0ea2419f0fa8b; luin=o1183520426; lskey=00010000b4baed70a5541f21fdb3b7008f1d24649d24038cb68eefd6da1557d51513f2aef77f88a07b265073; qq_openid=D0151F19CC20590A2F185A1B99D6627F; qq_access_token=8B284BCA332E1BE8954F4CC3C352A42E;\
 qq_client_id=101487368; LW_sid=M185x4y7N3h5S6i6l1r052R4k5; LW_uid=w115a4g7b3P536T6h1o0O224W6; eas_sid=R1f5a4r7a3A5C6q6T1z0o8O633; \
 o_cookie=1183520426; pac_uid=1_1183520426; _qpsvr_localtk=0.7148706400413105; pgv_si=s6567623680; ptui_loginuin=1183520426; ptisp=ctc; \
 uin=o1183520426; skey=@8iVoycvEe; p_uin=o1183520426; pt4_token=RPoYi88CoFYiCtYIROM3rXfbBM72282zki1W3o5t3M8_; \
 p_skey=JuEYxX3OyeCibG2lZDXNsbCpLisPBQKxshkZCVTk9XU_' -H 'origin: https://qun.qq.com' -H 'accept-encoding: gzip, deflate, br' -H \
 'accept-language: zh-CN,zh;q=0.9' -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36' -H \
 'content-type: application/x-www-form-urlencoded; charset=UTF-8' -H 'accept: application/json, text/javascript, */*; q=0.01' -H 'referer: https://qun.qq.com/member.html' -H 'authority: qun.qq.com' -H \
 'x-requested-with: XMLHttpRequest' --data 'gc=%s&st=0&end=%s&sort=0&bkn=38671463' --compressed" % (qq_qun, max_num)

json_data = os.popen(curl_command).readline() # read
dict_data = json.loads(json_data) # to dict

cards = dict_data['mems']
for card in cards:
    if card['g'] == 0:
        sex = '男'
    elif card['g'] == 1:
        sex = '女'
    elif card['g'] == 255:
        sex = '未知'

    join_time_arr = time.localtime(card['join_time'])
    join_time = time.strftime("%Y-%m-%d %H:%M:%S", join_time_arr)

    last_speak_time_arr = time.localtime(card['last_speak_time'])
    last_speak_time = time.strftime("%Y-%m-%d %H:%M:%S", last_speak_time_arr)

    print card['nick'], card['uin'], sex, card['qage'], join_time, last_speak_time

