# -*- coding: utf-8 -*-

""" 查询和设置 hostname 和 ip.

"""


import ujson as json

from libs import redisoj
from web.const import REDIS_DB_PM


client = redisoj.generate(REDIS_DB_PM)


def query(sn):
    idc = client.hget(sn, "idc")
    usage = client.hget(sn, "usage")

    data = {
        "idc": idc, 
        "usage": usage
    }
    return data


def setup(sn, hostname, ip):
    client.hset(sn, "hostname", hostname)
    client.hset(sn, "ip", ip)

    return True