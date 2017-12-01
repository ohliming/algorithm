# -*- coding: utf-8 -*-
from __future__ import division
import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))
import json,math,MySQLdb
from common.db_fetcher import DataBaseFetcher

fetcher = DataBaseFetcher()
print math.log(1+0.25*1)
print math.log(1+0.25*2)
print math.log(1+0.25*3)
print math.log(1+0.25*4)
print math.log(1+0.25*5)
print math.log(1+0.25*6)

a = [4,5,2,6]
a  = [4,5]
print a