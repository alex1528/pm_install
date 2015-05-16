#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 检查队列.

"""

import sys
import os
import traceback

from libs import html, log, mail, redisoj
from pm.libs import check
from web.const import REDIS_DB_PM


logger = log.get_logger("pm check")
client = redisoj.generate(REDIS_DB_PM)


def main():
    while 1:
        try:
            m = client.brpop("queue:check")
            m = eval(m[1])
            check_lists = m["check_lists"]
            task_id = m["task_id"]
            email = m["email"]
    
            logger.info(
                "check_lists-%s,email-%s" % (check_lists, email))
    
            check_results = check.multi(check_lists, task_id)
    
            subject = u"""[物理装机] 您提交的检查请求已经执行完毕"""
            context = "<br/>"
            logger.info("%s" % check_results)
            context += html.get(check_results)
            mail.mail(email, subject, context)
            logger.info("mail to %s, %s" % (email, context))

        except Exception, e:
            message = traceback.format_exc()
            logger.error(message)


if __name__ == "__main__":
    main()