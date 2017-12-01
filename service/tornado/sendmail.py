#!/usr/bin/env python
# -*- coding: utf8 -*-
import smtplib  
from email.mime.text import MIMEText
from email.header import Header  

class SendMail(object):
    """docstring for SendMail"""
    def __init__(self, sender, username ='15810509206@163.com', password = 'liming0916', smtpserver = 'smtp.163.com'):
        # init  password = 授权密码
        self.smtp = smtplib.SMTP()  
        self.smtp.connect(smtpserver)  
        self.smtp.login(username, password)

        self.sender = sender

    def __del__(self): # del
        self.smtp.quit()

    def sendHtml(self, subject, html, receiver):
        msg = MIMEText('%s' % html,'html','utf-8')
        msg['Subject'] = subject  
        self.smtp.sendmail(self.sender, receiver, msg.as_string())

    def sendText(self, subject, text, receiver):
        msg = MIMEText(text, _subtype='plain',_charset='utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        self.smtp.sendmail(self.sender, receiver, msg.as_string())

if __name__=='__main__':
    sender = '15810509206@163.com'
    receiver = ['15810509206@163.com']

    send = SendMail(sender)
    send.sendHtml('this is python send!','你好', receiver)
    
