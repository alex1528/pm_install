#-*- coding: utf-8 -*-


import requests
import ujson as json
import re

from libs import assetapi

from web.const import ASSET_IP_APPLY, ASSET_SERVER_QUERY, \
    ASSET_NETWORKDEVICE_QUERY


def get_from_ipblock(network):
    """ 根据 IP 端来获取IP.

    """
    data_dict = {
        "ipblock": network
    }
    _object = assetapi.Ldapapi()
    ret = _object.get_wrapper(ASSET_IP_APPLY, data_dict)

    return (True, ret)


def get_from_hostname(hostname):
    """ 根据一台机器来获取 IP.

    """
    data_dict = {
        "hostname": hostname
    }
    _object = assetapi.Ldapapi()
    detail = _object.get_wrapper(ASSET_SERVER_QUERY, data_dict)
    try:
        if detail["type"] == "vm":
            host = detail["vm_relation"]["vmh"]["hostname"]
            data_dict = {"hostname": host}
            detail = _object.get_wrapper(ASSET_SERVER_QUERY, data_dict)
        networkdevices = detail["networkdevice"]

        F = False
        for networkdevice in networkdevices:
            asset_networkdvice_query_url = ASSET_NETWORKDEVICE_QUERY + \
                networkdevice
            networkdevice_detail = _object.get_wrapper(\
                asset_networkdvice_query_url, data_dict)
            role = networkdevice_detail["data"][0]["role"]
            if role == u"内网边缘":
                ipblock = networkdevice_detail["data"][0]["intraipblocks"]
                # libs.log.logger.info("获取网段-%s" % ipblock)
                F = True
                break
        if F == False:
            message = "No internal edge switch."
            return (False, message)

        for network in ipblock:
            data_dict = {
                "ipblock": network
            }
            ret = _object.get_wrapper(ASSET_IP_APPLY, data_dict)
            if ret["result"] == "success":
                return (True, ret["msg"])
        message = "Get ip failed, ipblock:%s" % ipblock
        return (False, message)
    except Exception, e:
        message = "Get new ip exception, hostname:%s, "\
                    "exception:%s" % (hostname, e)
        return (False, message)