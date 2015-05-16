#-*- coding: utf-8 -*-


import redis

from web.const import REDIS_HOST, REDIS_PORT, REDIS_PASSWD


def generate(redis_db):
    # pool = redis.connection.BlockingConnectionPool(
    #    host=REDIS_HOST, port=REDIS_PORT, db=redis_db, \
    #    password=REDIS_PASSWD, timeout=60)
    # client = redis.client.Redis(connection_pool=pool)
    # return client

     return redis.Redis(
         host=REDIS_HOST, port=REDIS_PORT, db=redis_db, \
         password=REDIS_PASSWD)