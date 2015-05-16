# -*- coding: utf-8 -*-

""" 查询一台机器连接的机柜.

"""


import ujson as json

from libs import assetapi
from web.const import ASSET_SERVER_QUERY, ASSET_IPBLOCK_QUERY, \
    ASSET_NETWORKDEVICE_QUERY


def get(hostname):
    """ 查询一台机器连接的机柜.

    """
    data_dict = {
        "hostname": hostname
    }
    _object = assetapi.Ldapapi()
    detail = _object.get_wrapper(ASSET_SERVER_QUERY, data_dict)
    try:
        if detail["type"] != "vm":
            return detail["cabinet"]
        else:
            vmh = detail["vm_relation"]["vmh"]["hostname"]
            data_dict = {"hostname": vmh}
            detail = _object.get_wrapper(ASSET_SERVER_QUERY, data_dict)
            return detail["cabinet"]
    except Exception, e:
        message = "get cabinet of %s failed, exception:%s" % (hostname, e)        
        return (False, message)


if __name__ == "__main__":
    print get("vmh100.hy01")
    print get("app100.hy01")