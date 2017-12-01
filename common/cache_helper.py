#!/usr/bin/env python
# -*- coding: utf8 -*-

import redis

class CacheHelper():
    def __init__(self, host, port, db, pw):
        self.host = host
        self.port = port
        self.db = db
        self.password = pw
        self.conn =  redis.Redis(host=host, port=port, db=db, password=pw)

    def has(self, key):
        return self.conn.exists(key)

    def exists(self, key):
        return self.conn.exists(key)

    def get(self, key):
        return self.conn.get(key)

    def set(self, key, value=1, ttl=3600):
        if ttl > 0:
            return self.conn.setex(key, value, ttl)
        return self.conn.set(key, value)

    def delete(self, key):
        return self.conn.delete(key)

    def mset(self, dict_res):
        return self.conn.mset(dict_res)

    def mget(self, keys):
        return self.conn.mget(keys)

    # 集合
    def sadd(self, key, value):
        return self.conn.sadd(key, value)

    #  返回集合中的所有的成员
    def sinter(self, key):
        return self.conn.sinter(key)

    def scard(self, key):
        return self.conn.scard(key)

    # 集合之间的差集 : first - second
    def sdiff(self, first, second):
        return self.conn.sdiff(first, second)

    # first = second - third 差集覆盖
    def sdiffstore(self, first, second, third):
        return self.conn.sdiffstore(first, second, third)

    # 集合的交集
    def set_sinter(self, first, second):
        return self.conn.sinter(first, second)

    # 判断成员元素是否是集合的成员
    def sismember(self, key, value):
        return self.conn.sismember(key, value)

    # 返回集合中的所有的成员 不存在的集合 key 被视为空集合
    def smembers(self, key):
        return self.conn.smembers(key)

    # 将指定成员 member 元素从 source 集合移动到 destination 集合
    def smove(self,source,  destination, value):
        return self.conn.smove(source, destination, value)

    # 用于移除并返回集合中的一个随机元素
    def spop(self, key):
        return self.conn.spop(key)

    # 用于返回集合中的一个随机元素
    def srandmember(self, key, count):
        return self.conn.srandmember(key, count)

    # 移除集合中的一个或多个成员元素，不存在的成员元素会被忽略
    def srem(self, key, value):
        return self.conn.srem(key , value)

    # 返回给定集合的并集。不存在的集合 key 被视为空集
    def sunion(self, first, second):
        return self.conn.sunion(first, second)






