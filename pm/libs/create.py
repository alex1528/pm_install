# -*- coding: utf-8 -*-

""" 把设置网卡支持PXE启动 放在 设置系统启动顺序 前面,
    是为了避免 网卡是None的时候 无法设置 启动顺序的奇葩问题.
    (因为网卡是 None 的时候,启动顺序里面可能看不到 这个网卡,也就无法设置!!!)

"""

import time
import random
import sys
import os
import traceback
from multiprocessing.dummy import Pool as ThreadPool

import requests
import ujson as json

from web.const import MAX_THREAD_NUM
from web.const import REDIS_DB_PM, REDIS_DB_COMMON
from libs import redisoj, log, utils, server, dnsapi
from pm.libs import ilo_info, ilo_oper


logger = log.get_logger("pm auto create")
client = redisoj.generate(REDIS_DB_PM)

client_user_data = redisoj.generate(REDIS_DB_COMMON)


def multi(install_lists, task_id):
    client.hset(task_id, "install_lists", install_lists)

    pool = ThreadPool(MAX_THREAD_NUM)
    install_results = pool.map(single, install_lists)
    pool.close()
    pool.join()

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
    device = install_list["device"]
    product = install_list["product"]
    cabinet = install_list["cabinet"]
    user_data = install_list["user_data"]

    message = "start to install %s." % sn
    logger.info(message)

    # 查询控制卡 ip.
    ip = ilo_info.ip(idc, sn)
    if not ip or not utils.is_valid_ip(ip):
        result = "failed"
        message = "get ilo ip failed"
        install_list["result"] = result
        install_list["message"] = message
        return install_list
    message = "get %s ilo ip: %s" % (sn, ip)
    logger.info(message)

    # 拿到密码.
    passwd = ilo_info.passwd(idc, ip, sn)
    if not passwd:
        result = "failed"
        message = "get ilo passwd failed"
        install_list["result"] = result
        install_list["message"] = message
        return install_list
    passwd = passwd.strip()
    message = "get %s ilo passwd: %s" % (sn, passwd)
    logger.info(message)

    # 获取 ilo 对象.
    oj = ilo_oper.generate(idc, ip, passwd)
    message = "get %s ilo object" % (sn)
    logger.info(message)

    # 检查 SN 是否一致.
    curr_sn = oj.get_sn()
    if sn != curr_sn:
        result = "failed"
        message = "check sn failed"
        install_list["result"] = result
        install_list["message"] = message
        return install_list
    message = "check %s sn consistency success" % (sn)
    logger.info(message)

    # 查询网卡名称.
    nic = oj.get_nic_name(device)
    if not nic:
        logger.error("cann't get nic name")
        result = "failed"
        message = "cann't get nic name"
        install_list["result"] = result
        install_list["message"] = message
        return install_list
    message = "get %s nic name: %s" % (sn, nic)
    logger.info(message)

    # 设置网卡支持 PXE 启动.
    if not oj.get_nic_pxeboot(nic):
        if not oj.setup_nic_pxeboot(nic):
            result = "failed"
            message = "setup network device to support pxe boot failed"
            install_list["result"] = result
            install_list["message"] = message
            return install_list
    message = "set %s nic pxe boot success" % sn
    logger.info(message)

    # 设置启动顺序.
    nic_seq = oj.get_boot_order(nic)
    if not oj.check_boot_order(nic_seq):
        if not oj.setup_boot_order(nic_seq):
            result = "failed"
            message = "can't setup right bootseq - %s" % nic_seq
            install_list["result"] = result
            install_list["message"] = message
            return install_list
    message = "set %s nic support pxe boot success" % sn
    logger.info(message)

    # 设置机器从 PXE 启动一次.
    if not oj.setup_pxeboot_once():
        result = "failed"
        message = "setup pxe once boot failed"
        install_list["result"] = result
        install_list["message"] = message
        return install_list
    message = "set %s nic pxe boot once success" % sn
    logger.info(message)

    # 拷贝 pxelinux 配置文件.
    mac = oj.get_mac(nic)
    if not oj.constract_tftp(_type, version, mac):
        result = "failed"
        message = "copy pxelinux cfg failed"
        install_list["result"] = result
        install_list["message"] = message
        return install_list
    message = "copy %s pxelinux cfg success" % sn
    logger.info(message)

    # 重启.
    if not oj.reboot():
        result = "failed"
        message = "restart server failed"
        install_list["result"] = result
        install_list["message"] = message
        return install_list
    message = "reboot %s success" % sn
    logger.info(message)

    # 安装信息进 redis.
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

    # 删除 pxelinux 配置文件.
    if oj.del_tftp(mac):
        message = "delete %s pxelinux cfg success" % sn
        logger.info(message)
    else:
        message = "delete %s pxelinux cfg failed" % sn
        logger.error(message)

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
