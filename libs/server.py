# -*- coding: utf-8 -*-

""" 查询和设置机器的信息.

"""

import requests
import re
import sys
import os

import ujson as json

from libs import assetapi, log
from web.const import ASSET_SERVER_QUERY, ASSET_SERVER_MODIFY


def get(srckey, value, dstkey=None):
    data_dict = {srckey: value}
    _object = assetapi.Ldapapi()
    ret = _object.get_wrapper(ASSET_SERVER_QUERY, data_dict)

    if dstkey is None:
        return ret

    if dstkey not in ret:
        return {}
    return ret[dstkey]


def set(sn, key, value):
    data_dict = {
        "sn": sn,
        key: value
    }
    _object = assetapi.Ldapapi()
    ret = _object.post_wrapper(ASSET_SERVER_MODIFY, data_dict)

    if ret["message"] == "success":
        return True
    else:
        return False


if __name__ == "__main__":
    sn = get("hostname", "stg10.hy01", "sn")
    print sn
    print set(sn, "product", "SA")
