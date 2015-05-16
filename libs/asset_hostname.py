#-*- coding: utf-8 -*-


import requests
import ujson as json
import re

from libs import assetapi

from web.const import ASSET_HOSTNAME_APPLY


def get(idc, usage):
    data_dict = {
    	"operation": "create", 
    	"idc": idc, 
    	"usage": usage
    }

    _object = assetapi.Ldapapi()
    ret = _object.post_wrapper(ASSET_HOSTNAME_APPLY, data_dict)
    return ret


if __name__ == "__main__":
    print get("hy", "test")