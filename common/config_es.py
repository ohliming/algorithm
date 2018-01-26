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
    "article": "[[[ARTICLE_API_HOST]]]",
    "article_api_key": "[[[ARTICLE_API_KEY]]]",
}

