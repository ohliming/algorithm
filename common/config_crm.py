#!/usr/bin/env python
# -*- coding: utf8 -*-

mysql_slave_host = "[[[DB_HOST_SLAVE]]]"

mysql_offline = {
    "host":"[[[DB_HOST]]]",
    "user":"[[[DB_CRM_USER]]]",
    "pwd":"[[[DB_CRM_PASSWD]]]",
    "db":"[[[DB_CRM_NAME]]]",
}

#mysql_online_daily = {
#    "host":"dev09",
#    "user":"dev",
#    "pwd":"AxlLZoPxrysgpZjvh3yz",
#    "db_pre":"krplus2_",
#}

mysql_online = {
    "host":"[[[DB_HOST]]]",
    "user":"[[[DB_KRPLUS_USER]]]",
    "pwd":"[[[DB_KRPLUS_PASSWD]]]",
    "db":"[[[DB_KRPLUS_NAME]]]",
}

mysql_online_audit = {
    "host":"[[[DB_HOST]]]",
    "user":"[[[DB_AUDIT_USER]]]",
    "pwd":"[[[DB_AUDIT_PASSWD]]]",
    "db":"[[[DB_AUDIT_NAME]]]",
}

mysql_online_insight = {
    "host":"[[[DB_HOST]]]",
    "user":"[[[DB_INSIGHT_USER]]]",
    "pwd":"[[[DB_INSIGHT_PASSWD]]]",
    "db":"[[[DB_INSIGHT_NAME]]]",
}

mysql_statistic = {
    "host":"[[[DB_HOST]]]",
    "user":"[[[DB_STATISTIC_USER]]]",
    "pwd":"[[[DB_STATISTIC_PASSWD]]]",
    "db":"[[[DB_STATISTIC_NAME]]]",
}

es_com_offline = {
    "host":"[[[ES_HOST]]]",
    "port":"9200",
    "index":"prod_company_offline",
    "type":"com"
}

es_com_online = {
    "host":"[[[ES_HOST]]]",
    "port":"9200",
    "index":"prod_company_online",
    "type":"com"
}

es_com_crm = {
    "host":"[[[ES_HOST]]]",
    "port":"9200",
    "index":"company_crm",
    "type":"info"
}

redis_crm = {
    "host": "[[[DB_HOST_REDIS]]]",
    "port": 6379,
    "db": 5,
    "pwd": "[[[DB_REDIS_PASSWD]]]",
}

webapi = {
    "article": "[[[ARTICLE_API_HOST]]]",
    "article_api_key": "[[[ARTICLE_API_KEY]]]",
    #"rong_host": "http://rongtest01.36kr.com",
    "rong_host": "[[[RONG_API_HOST]]]",
}

