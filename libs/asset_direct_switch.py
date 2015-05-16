# -*- coding: utf-8 -*-

""" 查询一个机器直连的交换机

"""


import ujson as json

from libs import assetapi
from web.const import ASSET_SERVER_QUERY, ASSET_IPBLOCK_QUERY, \
    ASSET_NETWORKDEVICE_QUERY


def get(hostname):
    """ 根据机器获取它的直连交换机.

    """

    data_dict = {
        "hostname": hostname
    }
    try:
        _object = assetapi.Ldapapi()
        detail = _object.get_wrapper(ASSET_SERVER_QUERY, data_dict)
    except Exception,e:
        message = "get asset detail of %s failed, exception:%s" % (hostname, e)
        return (False, message)

    if detail["type"] == "vm":
        vmh = detail["vm_relation"]["vmh"]["hostname"]
        data_dict = {
            "hostname": vmh
        }
        detail = _object.get_wrapper(ASSET_SERVER_QUERY, data_dict)

    try:
        ip = detail["ips"]["intra"][0]
        networkdevices = detail["networkdevice"]
        data_dict = {
            "ip": ip
        }
        ip_block = _object.get_wrapper(ASSET_IPBLOCK_QUERY, data_dict)
        ipblock = ip_block["ipblock"]
        for networkdevice in networkdevices:
            asset_networkdevice_query_url = ASSET_NETWORKDEVICE_QUERY + \
                networkdevice
            data_dict = {}
            networkdevice_detail = _object.get_wrapper(asset_networkdevice_query_url, data_dict)
            intraipblocks = networkdevice_detail["data"][0]["intraipblocks"]
            for intraipblock in intraipblocks:
                if intraipblock == ipblock:
                    return (True, networkdevice)
        return (False,)                   
    except Exception, e:
        message = "get direct switch of %s failed, exception:%s" % (hostname, e)        
        return (False, message)


if __name__ == "__main__":
    print get("vmh166.hy01")
    print get("app100.hy01")