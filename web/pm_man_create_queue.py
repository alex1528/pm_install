#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 手动安装队列.

手动安装机器需要用 idrac 或者机房人员帮忙操作:
1). 重启, 按 F12 进入 PXE 模式;
2). 如果遇到网卡选择界面, 选择第二块网卡(假设第二块网卡是内网);
3). 遇到 boot 界面, 直接回车.

"""

import sys
import os
import traceback

from libs import html, log, mail, redisoj
from pm.libs import create_man
from web.const import REDIS_DB_PM


logger = log.get_logger("pm manual create")
client = redisoj.generate(REDIS_DB_PM)


def main():
    while 1:
        try:
            m = client.brpop("queue:man")
            m = eval(m[1])
            install_lists = m["install_lists"]
            task_id = m["task_id"]            
            email = m["email"]
    
            logger.info(
                "install_lists-%s,email-%s" % (install_lists, email))
    
            install_results = create_man.multi(install_lists, task_id)
    
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