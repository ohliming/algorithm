#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys,os,json
import urllib, urllib2

class EsImporter():
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def import_datas(self, datas, index, estype, noid=False, action="index", version=""):
        if datas:
            url = "http://%s:%s/_bulk" % (self.host, self.port)
           # if version:
           #     url = "http://%s:%s/_bulk?version_type=external&version=%d" % (self.host, self.port, int(version))
            param = ""
            if not noid:
                for data in datas:
                    cid = data["id"]
                    del data["id"]
                    bulk_action = {action:{"_index":index, "_type":estype, "_id":cid}}
                    if version:
                        bulk_action[action]["_version_type"] = "external"
                        bulk_action[action]["_version"] = int(version)
                    param += json.dumps(bulk_action)+"\n"
                    param += json.dumps(data)+"\n"

                res = urllib.urlopen(url, data=param).read()
                #print "send to es data num : %d" % len(datas)
                #print res
            else:
                for data in datas:
                    bulk_action = {action:{"_index":index, "_type":estype}}
                    param += json.dumps(bulk_action)+"\n"
                    param += json.dumps(data)+"\n"

                res = urllib.urlopen(url, data=param).read()
        else:
            #print "no data to es"
            pass

    def update_datas(self, datas, index, estype, upsert=True):
        if datas:
            url = "http://%s:%s/_bulk" % (self.host, self.port)
            param = ""
            for data in datas:
                cid = data["id"]
                del data["id"]
                doc = {
                    "doc": data,
                    "doc_as_upsert" : upsert
                }
                bulk_action = {"update":{"_index":index, "_type":estype, "_id":cid}}
                param += json.dumps(bulk_action)+"\n"
                param += json.dumps(doc)+"\n"

            res = urllib.urlopen(url, data=param).read()
            #print "send to es data num : %d" % len(datas)
            #print res
        else:
            #print "no data to es"
            pass

    def update_data(self, data, index, estype):
        if data:
            cid = data["id"]
            del data["id"]
            url = "http://%s:%s/%s/%s/%s/_update" % (self.host, self.port, index, estype, str(cid))
            param = {
                "doc": data,
                "doc_as_upsert": True
            }
            res = urllib.urlopen(url, data=json.dumps(param)).read()
            #print res
        else:
            #print "no data to es"
            pass

    def delete_datas(self, ids, index, estype):
        if ids:
            url = "http://%s:%s/_bulk" % (self.host, self.port)
            param = ""
            for id in ids:
                bulk_action = {"delete":{"_index":index, "_type":estype, "_id": id}}
                param += json.dumps(bulk_action)+"\n"

            res = urllib.urlopen(url, data=param).read()
            #print "send to es data num : %d" % len(datas)
            #print res
        else:
            #print "no data to es"
            pass

    def get_deleted_ids(self, ids, index, estype):
        ids_del = []
        ct = 0
        url = "http://%s:%s/%s/_search?search_type=scan&scroll=1m" % (self.host, self.port, index)
        #print url
        param = {"size":200}
        res = urllib.urlopen(url, data=json.dumps(param)).read()
        jres = json.loads(res)
        scrollid=jres["_scroll_id"]
        total = jres["hits"]["total"]
        while(True):
            url2 = "http://%s:%s/_search/scroll?scroll=1m&scroll_id=%s" % (self.host, self.port, scrollid)
            #print url2
            res2 = urllib.urlopen(url2).read()
            #print res2
            jres2 = json.loads(res2)
            datas = jres2["hits"]["hits"]
            #total = jres2["hits"]["total"]
            ct += len(datas)
            for data in datas:
                esid = data["_id"]
                if esid not in ids:
                    ids_del.append(esid)
            # 所有数据都返回后，Search contexts会自动清掉，再访问log里会记报错
            if ct>=total:
                break
            if len(datas)==0:
                break
        #print ct
        return ids_del



