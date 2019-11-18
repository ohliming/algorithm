#!/usr/bin/env python
# -*- coding: utf8 -*-
import smtplib, sys, time
from email.mime.text import MIMEText
from email.header import Header  

class SendMail(object):
    """docstring for SendMail"""
    def __init__(self, sender, username ='15810509206@163.com', password = 'liming0916', smtpserver = 'smtp.163.com'):
        # init  password = 授权密码
        self.smtp = smtplib.SMTP()  
        self.smtp.connect(smtpserver, 25)  
        self.smtp.login(username, password)
        self.sender = sender

    def __del__(self): # del
        self.smtp.quit()

    def reConnect(self):
        self.smtp.connect(smtpserver, 25)

    def sendHtml(self, subject, html, receiver):
        msg = MIMEText('%s' % html,'html','utf-8')
        msg['From'] = self.sender
        msg['To'] = receiver
        msg['Subject'] = subject  
        self.smtp.sendmail(self.sender, receiver, msg.as_string())

    def sendText(self, subject, text, receiver):
        msg = MIMEText(text, _subtype='plain',_charset='utf-8')
        msg['From'] = self.sender
        msg['To'] = receiver
        msg['Subject'] = Header(subject, 'utf-8').encode()
        self.smtp.sendmail(self.sender, receiver, msg.as_string())


context1 = 'Python 实战就业课程： \n\
直播课程目录：https://ke.qq.com/course/373941?tuin=468b16aa  \n\
直播课程咨询：15810509206  \n \n\
免费Python 视频教程: \n\
Python 基础篇  \n\
Python 进阶篇  \n\
Python 项目篇  \n\
链接：https://pan.baidu.com/s/1YuWONPZDd-H0IQ1DgFJD2A  \n\
提取码：z2uw ' # 内容 

context2 = '你好！ 免费Pyhton 知识直播课来了：https://ke.qq.com/course/376678?tuin=468b16aa  &—_-& 15810509206'

if __name__=='__main__':
    sender = '15810509206@163.com'

    # receiver
    receivers = []
    with open('qq.txt') as qq_h:
        for line in qq_h:
            qq_mail = '%s@qq.com' % line.strip()
            receivers.append(qq_mail) # 

    # main 
    header = 'Python 就业学习课程等你免费拿!' # 标题

    send = SendMail(sender)
    for receiver in receivers:
        print receiver
        send.sendText(header, context1, receiver)
        time.sleep(10) # 




    