# -*- coding: utf-8 -*-

""" 把设置网卡支持PXE启动 放在 设置系统启动顺序 前面,
    是为了避免 网卡是None的时候 无法设置 启动顺序的奇葩问题.
    (因为网卡是None的时候,启动顺序里面可能看不到 这个网卡,也就无法设置!!!)

"""

import time
import random
from multiprocessing.dummy import Pool as ThreadPool

import ujson as json
import requests

from web.const import MAX_THREAD_NUM, REDIS_DB_PM
from libs import redisoj
from libs import log
from libs import utils
from pm.libs import ilo_info, ilo_oper


logger = log.get_logger("pm check")
client = redisoj.generate(REDIS_DB_PM)


def multi(check_lists, task_id):
    client.hset(task_id, "check_lists", check_lists)

    pool = ThreadPool(MAX_THREAD_NUM)
    check_results = pool.map(single, check_lists)
    pool.close()
    pool.join()

    client.hset(task_id, "check_results", check_results)
    return check_results


def single(check_list):
    """ 检查是否能够正常安装.

    """

    idc = check_list["idc"]
    sn = check_list["sn"]
    device = check_list["device"]

    # 查询控制卡 ip.    
    ip = ilo_info.ip(idc, sn)
    if ip == False or utils.is_valid_ip(ip) == False:
        result = "failed"
        message = "get ilo ip failed"
        check_list["result"] = result
        check_list["message"] = message
        return check_list

    # 拿到密码.
    passwd = ilo_info.passwd(idc, ip, sn)
    if passwd == False:
        result = "failed"
        message = "get ilo passwd failed"
        check_list["result"] = result
        check_list["message"] = message
        return check_list

    passwd = passwd.strip()

    # 获取 ilo 对象.
    oj = ilo_oper.generate(idc, ip, passwd)

    # 检查 SN 是否一致.
    curr_sn = oj.get_sn()
    if sn != curr_sn:
        result = "failed"
        message = "check sn failed"
        check_list["result"] = result
        check_list["message"] = message
        return check_list

    # 查询网卡名称.
    nic = oj.get_nic_name(device)
    if not nic:
        logger.error("cann't get nic name")
        result = "failed"
        message = "cann't get nic name"
        check_list["result"] = result
        check_list["message"] = message
        return check_list

    # 设置网卡支持 PXE 启动.
    if not oj.get_nic_pxeboot(nic):
        if not oj.setup_nic_pxeboot(nic):
            result = "failed"
            message = "setup network device to support pxe boot failed"
            check_list["result"] = result
            check_list["message"] = message
            return check_list

    # 设置启动顺序.
    nic_seq = oj.get_boot_order(nic)
    if not oj.check_boot_order(nic_seq):
        if not oj.setup_boot_order(nic_seq):
            result = "failed"
            message = "can't setup right bootseq - %s" % nic_seq
            check_list["result"] = result
            check_list["message"] = message
            return check_list

    logger.info("%s(%s) check install success ", sn, ip)

    result = "success"
    message = "check success"
    check_list["result"] = result
    check_list["message"] = message
    return check_list
