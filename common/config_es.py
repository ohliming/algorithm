#!/usr/bin/env python
# -*- coding: utf8 -*-

mysql_slave_host = "[[[DB_HOST_SLAVE]]]"

mysql_offline = {
    "host":"[[[DB_HOST]]]",
    "user":"[[[DB_CRM_USER]]]",
    "pwd":"[[[DB_CRM_PASSWD]]]",
    "db":"[[[DB_CRM_NAME]]]",
}

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

es = {
    "host":"[[[ES_HOST]]]",
    "port":"9200",
    "type":"info",
    "index_com":"36kr_company",
    "index_org":"36kr_organization",
    "index_user":"36kr_user",
    "index_city":"city",
    "index_school":"school",
    "index_tag":"tag",
    "index_tag_crm":"tag_crm",
    "index_article":"36kr_article",
    "index_newsflash":"36kr_newsflash",
    "index_writer":"36kr_writer",
    "index_ad": "ad_mobile",
    "index_qyservice": "qy_service",
    "index_qyword": "qy_word",
    "index_qytag": "qy_tag",
    "index_keyword": "36kr_keyword",
    "index_position": "position",
    "index_com_crm": "company_crm",
    #"index_log_pre":"36kr_log_",
    #"index_log_statistic":"log_statistic",
}

es_w = {
    "index_com":"current_company_w",
    "index_org":"current_organization_w",
    "index_user":"current_user_w",
}

es_r = {
    "index_com":"current_company_r",
    "index_org":"current_organization_r",
    "index_user":"current_user_r",
}

webapi = {
    #"log":"http://localhost:20521",
    #"log":"http://data-internal.corp.36tr.com/log-statistic",
    #"article": "http://36kr.com",
    #"article": "http://staging.api.36kr.com",
    "article": "[[[ARTICLE_API_HOST]]]",
    "article_api_key": "[[[ARTICLE_API_KEY]]]",
}

