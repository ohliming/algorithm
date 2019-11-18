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

def get_cmd(qq_qun, start, end):
    curl_command = "curl 'https://qun.qq.com/cgi-bin/qun_mgr/search_group_members' -H 'cookie: pgv_pvid=109100192; pac_uid=0_5c621c4f6abb8; pgv_pvi=4775654400; RK=nyrRSPu8dN; ptcz=25651d36da38193c1695a435f7fa2098f62c1ac738e8b655ae4052b3dbaccfd5; luin=o1183520426; lskey=000100000a7c075cd0942eb01df00100b0e3ad1d22d916a784107e715a3ccd595c337db08ce8e69fa37ce65f; tvfe_boss_uuid=f94dc704caf30c11; o_cookie=1183520426; eas_sid=l1Z5p5o070c4w4e5p5g8r442i8; pgv_info=ssid=s7501435844; _qpsvr_localtk=0.4417233822300368; pgv_si=s8031713280; ptisp=cnc; uin=o1183520426; skey=@J7r13Nua9; p_uin=o1183520426; pt4_token=isBE8Ublwkbas7nfux4mmCKE0OygTbD8UWzDBS0puX8_; p_skey=PzChP6ejrjXzdjkC4uFmOuPYQDl8l5RHwcjdkfZB-0I_' -H 'origin: https://qun.qq.com' -H 'accept-encoding: gzip, deflate, br' -H 'accept-language: zh-CN,zh;q=0.9' -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36' -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' -H 'accept: application/json, text/javascript, */*; q=0.01' -H 'referer: https://qun.qq.com/member.html' -H 'authority: qun.qq.com' -H 'x-requested-with: XMLHttpRequest' --data 'gc=%s&st=%s&end=%s&sort=0&bkn=1676871833' --compressed" \
     % (qq_qun, start, end)
    return curl_command

max_cnt = 2000
start, end = 0, 20
step = 20
qq_qun = '531229476'
#print('别名\tqq\t性别\t年龄\t加群时间\t最后发言时间')
while start < max_cnt:
    curl_command = get_cmd(qq_qun, start, end)
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

        nick = card['nick']
        if '老师' not in nick:
            print("%s\t%s\t%s\t%s\t%s\t%s" % (nick, card['uin'], sex, card['qage'], join_time, last_speak_time))


    start = end + 1
    end = start +  step
    max_cnt = dict_data['count']
    time.sleep(5) # 休眠

