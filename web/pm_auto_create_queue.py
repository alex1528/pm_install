#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 自动安装队列.

"""

import sys
import os
import traceback

from libs import html, log, mail, redisoj
from pm.libs import create
from web.const import REDIS_DB_PM


logger = log.get_logger("pm auto create")
client = redisoj.generate(REDIS_DB_PM)


def main():
    while 1:
        try:
            m = client.brpop("queue:create")
            m = eval(m[1])
            install_lists = m["install_lists"]
            task_id = m["task_id"]            
            email = m["email"]
    
            logger.info(
                "install_lists-%s,email-%s" % (install_lists, email))
    
            install_results = create.multi(install_lists, task_id)
    
            subject = u"""[物理装机] 您提交的安装请求已经执行完毕"""
            context = "<br/>"
            logger.info("%s" % install_results)
            context += html.get(install_results)
            mail.mail(email, subject, context)
            logger.info("mail to %s, %s" % (email, context))

        except Exception, e:
            message = traceback.format_exc()
            logger.error(message)


if __name__ == "__main__":
    main()