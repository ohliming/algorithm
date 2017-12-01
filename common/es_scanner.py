#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys,os,json
import urllib, urllib2

class EsScanner():
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_scrollid(self, index, size=200):
        url = "http://%s:%s/%s/_search?search_type=scan&scroll=1m" % (self.host, self.port, index)
        param = {"size": size}
        res = urllib.urlopen(url, data=json.dumps(param)).read()
        # print res
        jres = json.loads(res)
        total = jres["hits"]["total"]
        return (jres["_scroll_id"], total)

    def get_scan_datas(self, scrollid):
        url = "http://%s:%s/_search/scroll?scroll=1m&scroll_id=%s" % (self.host, self.port, scrollid)
        res = urllib.urlopen(url).read()
        jres = json.loads(res)
        return jres["hits"]["hits"]

    def delete_datas(self, ids, index, estype):
        if ids:
            url = "http://%s:%s/_bulk" % (self.host, self.port)
            param = ""
            for id in ids:
                bulk_action = {"delete":{"_index":index, "_type":estype, "_id":id}}
                param += json.dumps(bulk_action)+"\n"
            res = urllib.urlopen(url, data=param).read()
        else:
            #print "no data to es"
            pass
