#-*- coding: utf-8 -*-

""" 生成一个全局递增 id.

"""


import redis

from libs import redisoj
from web.const import REDIS_DB_PM


client = redisoj.generate(REDIS_DB_PM)


def get():
    """ 获取全局唯一 id.

    能够保证 id 不重复.

    """
    pipe = client.pipeline()

    while 1:
        try:
            pipe.watch('global_id')
            current_id = pipe.get('global_id')
            if current_id is None:
                next_id = 1
            else:
                next_id = int(current_id) + 1
            pipe.multi()
            pipe.set('global_id', next_id)
            pipe.execute()
            break
        except redis.exceptions.WatchError:
            continue
        finally:
            pipe.reset()

    return next_id


if __name__ == '__main__':
    get()