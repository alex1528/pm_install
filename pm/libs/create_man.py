# -*- coding: utf-8 -*-

""" 手动装机工具, 适合没有控制卡的机器安装, 需要机房帮忙重启进入PXE模式
    这里采用 ks 的 default 文件来默认安装, 所以可以同时装很多批同一 
    type 的机器;

    不能同时安装不同 type 和 version 的机器, 如果安装, 请求会退出.
    
"""

import time
import random
import sys
import os
import traceback
from multiprocessing.dummy import Pool as ThreadPool

import requests
import ujson as json

from web.const import MAX_THREAD_NUM, PXELINUX_CFGS
from web.const import REDIS_DB_PM, REDIS_DB_COMMON
from libs import redisoj, log, utils, server, dnsapi


logger = log.get_logger("pm manual create")
client = redisoj.generate(REDIS_DB_PM)

client_user_data = redisoj.generate(REDIS_DB_COMMON)


def multi(install_lists, task_id):
    client.hset(task_id, "install_lists", install_lists)
    
    # 取一个列表的 type和version, 一批机器的type 和 version 相同.
    _type = install_lists[0]["type"]
    version = install_lists[0]["version"]

    # 因为手动安装是使用一个默认的配置文件, 如果多组机器同时安装, 配置文件需要在
    # 所有的机器都安装完成之后删除, 所以用一个队列来保存正在安装的任务.
    default_key = "default:%s:%s" % (_type, version)
    client.lpush(default_key, "")

    # 拷贝默认配置文件.
    # 不能同时安装两种类型的机器;
    # 而且还只能是一个版本.
    cmd = r"sudo /bin/cp -f %s /var/lib/tftpboot/pxelinux.cfg/default" % \
        PXELINUX_CFGS[_type][version]
    rc, so, se = utils.shell(cmd)

    # 执行安装任务.
    pool = ThreadPool(MAX_THREAD_NUM)
    install_results = pool.map(single, install_lists)
    pool.close()
    pool.join()

    # 安装完成出队列.
    client.rpop(default_key)

    # 队列为空时, 说明没有任务要执行了, 删除配置文件.
    if len(client.lrange(default_key, 0, -1)) == 0:
        cmd = r"sudo /bin/rm -f /var/lib/tftpboot/pxelinux.cfg/default"
        rc, so, se = utils.shell(cmd)

    client.hset(task_id, "install_results", install_results)
    return install_results


def single(install_list):
    """ 单台机器安装.

    """

    idc = install_list["idc"]
    sn = install_list["sn"]
    _type = install_list["type"]
    version = install_list["version"]
    usage = install_list["usage"]
    product = install_list["product"]
    cabinet = install_list["cabinet"]
    user_data = install_list["user_data"]

    message = "start to install %s." % sn
    logger.info(message)

    # 安装系统进入 redis.
    client.hset(sn, "idc", idc)
    client.hset(sn, "usage", usage)

    client.hset(sn, "hostname", "")
    client.hset(sn, "ip", "")

    message = "set %s's idc, usage, hostname, ip to redis success" % sn
    logger.info(message)

    # 设置 user_data, 装机之后机器会获取并执行 user_data 中的内容.
    if user_data is None:
        client_user_data.exists(sn) and client_user_data.delete(sn) 
    else:
        client_user_data.set(sn, user_data)

    # 循环等待安装完成.
    timeout = 2700
    interval = 30
    timetotal = 0

    installed = False
    inasset = False

    while timetotal < timeout:
        if not installed:
            hostname = client.hget(sn, "hostname")
            ip = client.hget(sn, "ip")

            if "" in [hostname, ip]:
                time.sleep(interval)
                timetotal += interval
            else:
                installed = True
        elif installed and not inasset:
            try:            
                ret = server.get("sn", sn)
                if not isinstance(ret, dict):
                    time.sleep(interval)
                    timetotal += interval
                elif "hostname" not in ret:
                    time.sleep(interval)
                    timetotal += interval
                elif ret["hostname"] != hostname:               
                    time.sleep(interval)
                    timetotal += interval
                else:
                    inasset = True
            except Exception, e:
                message = traceback.format_exc()
                logger.error(message)  
                time.sleep(interval)
                timetotal += interval                    
        else:
            break

    message = "sn:%s, hostname:%s, ip:%s, installed:%s, inasset:%s" % (
        sn, hostname, ip, installed, inasset)
    logger.info(message)            

    # 存储 hostname 和 ip.
    try:
        install_list["hostname"] = hostname
    except Exception, e:
        install_list["hostname"] = "<hostname>"
    try:
        install_list["ip"] = ip
    except Exception, e:
        install_list["ip"] = "<ip>"

    # 检查安装完成情况.
    if not installed:
        result = "failed"
        message = "install timeout"
        install_list["result"] = result
        install_list["message"] = message
        logger.error("%s - %s" % (sn, message))
        return install_list
    elif installed and not inasset:
        result = "failed"
        message = "install success,but not uploaded to asset sys"
        install_list["result"] = result
        install_list["message"] = message
        logger.error("%s - %s" % (sn, message))
        return install_list
    else:
        try:
            if "vmh" in hostname:
                server.set(sn, "status", "production")
            else:
                server.set(sn, "status", "pre-production")
            server.set(sn, "product", product)
            server.set(sn, "cabinet", cabinet)
    
            # 检查 hostname 是否已经成功添加 DNS.
            recordred = dnsapi.dns_record_exist(hostname)
            if recordred:
                result = "success"
                message = "install success"
                install_list["result"] = result
                install_list["message"] = message
                logger.info("%s - %s" % (sn, message))
                return install_list
            else:
                result = "failed"
                message = "dns added failed"
                install_list["result"] = result
                install_list["message"] = message
                logger.error("%s - %s" % (sn, message))
                return install_list            
        except Exception, e:
            result = "failed"
            message = "%s" % e
            install_list["result"] = result
            install_list["message"] = message
            logger.error("%s - %s" % (sn, message))
            return install_list