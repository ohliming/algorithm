#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Date    :  2015-02-04 15:09:31

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import json
from db_crud import DbCrud
import traceback

def main():
    try:
        db = DbCrud("rds60i0820sk46jfsiv0.mysql.rds.aliyuncs.com", "stat", "JTRQ6pNlnqdBV3ox", "stat")
        report_date = sys.argv[1]
        stat_file = sys.argv[2]
        with open(stat_file) as f:
            j = json.load(f)
            j["stat_date"] = report_date
            db.replace_data("insight_report", j)
    except:
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    '''
    python ./prog [2015-06-23]
    '''
    sys.exit(main())

