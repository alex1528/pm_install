# -*- coding: utf-8 -*-


import sys
import os

import ujson as json

import tornado.web

from libs import decorator, ldapauth, redisoj, server
from web.const import REDIS_DB_PM, PM_TASK_BASE_URL
from pm.libs import global_id, check, create, create_man, tmessage


redis_client_pm = redisoj.generate(REDIS_DB_PM)


class CheckHandler(tornado.web.RequestHandler):
    @decorator.authenticate_decorator
    def post(self):
        """ 检查物理机是否可以正常装机.

        检查项包括:
        1). 是否可以根据 SN 获取到 ILO IP.
        2). 是否能够 获取到 ILO 的密码.
        3). 是否能够设置第二块网卡支持 PXE 启动.
        4). 是否能够设置启动顺序.

        """
        idc = _get_argument_json(self, "idc", False, loads=True)
        device = _get_argument_json(self, "device", False, loads=True)
        sns = _get_argument_json(self, "sns", False, loads=True)
        email = _get_argument_json(self, "email", True, None, loads=True)

        check_lists = list()
        for i in sns:
            item = {
                "idc": idc, 
                "device": device, 
                "sn": i["sn"]
            }
            check_lists.append(item)

        # 生成创建任务 id.
        task_key = "physical:check"
        task_id = "%s:%s" % (task_key, global_id.get())

        queue_dict = {
            "check_lists": check_lists, 
            "task_id": task_id,
            "email": email
        }
        redis_client_pm.lpush("queue:check", queue_dict)

        _url = "%s/%s" % (PM_TASK_BASE_URL, task_id)
        ret = {
            "status": "checking", 
            "message": _url
        }
        self.write(json.dumps(ret))


class CreateHandler(tornado.web.RequestHandler):
    @decorator.authenticate_decorator
    def post(self):
        """ 安装物理机.

        步骤包括:
        1). 根据 SN 获取到 ILO IP.
        2). 获取到 ILO 的密码.
        3). 设置第二块网卡支持 PXE 启动.
        4). 设置系统启动顺序.
        5). 设置系统 PXE 启动一次.
        6). 拷贝 pxelinux 配置文件.
        7). 重启.
        8). 等待安装完成.
        9). 删除 pxelinux 配置文件.
        10). 在资产系统里设置 product 和 cabinet 等.

        type 表示支持安装的物理机类型, 目前支持三种, 分别是:
        raw, kvm, docker;

        version 表示支持的操作系统版本, 目前有:
        centos6, centos7

        """
        idc = _get_argument_json(self, "idc", False, loads=True)
        _type = _get_argument_json(self, "type", False, loads=True)
        version = _get_argument_json(self, "version", True, "centos6", loads=True)
        usage = _get_argument_json(self, "usage", False, loads=True)
        product = _get_argument_json(self, "product", False, loads=True)
        device = _get_argument_json(self, "device", False, loads=True)
        force = _get_argument_json(self, "force", True, False, loads=True)
        sns = _get_argument_json(self, "sns", False, loads=True)
        user_data = _get_argument_json(self, "user_data", True, None, loads=True)
        email = _get_argument_json(self, "email", True, None, loads=True)

        install_lists = list()
        for i in sns:
            item = {
                "idc": idc, 
                "type": _type,
                "version": version,                    
                "usage": usage, 
                "product": product, 
                "device": device, 
                "sn": i["sn"], 
                "cabinet": i["cabinet"],
                "user_data": user_data
            }
            install_lists.append(item)

        # 是否强制安装.
        inasset_lists = list()
        if force != True:
            for item in install_lists:
                sn = item["sn"]
                if server.get("sn", sn, "hostname"):
                    inasset_lists.append(sn)
            if inasset_lists != []:
                message = "servers have in asset, can't install:{0}".format(
                    inasset_lists)
                ret = {
                    "status": "failed", 
                    "message": message
                }
                self.write(json.dumps(ret))
                self.finish()

        # 生成创建任务 id.
        task_key = "physical:create"
        task_id = "%s:%s" % (task_key, global_id.get())

        queue_dict = {
            "install_lists": install_lists, 
            "task_id": task_id,
            "email": email
        }
        redis_client_pm.lpush("queue:create", queue_dict)

        _url = "%s/%s" % (PM_TASK_BASE_URL, task_id)
        ret = {
            "status": "creating", 
            "message": _url
        }
        self.write(json.dumps(ret))


class CreateManHandler(tornado.web.RequestHandler):
    @decorator.authenticate_decorator
    def post(self):
        """ 手动安装物理机, 需要部分手动操作.

        步骤包括:
        1). 拷贝默认 pxelinux 配置文件.
        2). 手动重启机器, 按 F12 进入 PXE 模式, 
            并选择第二块网卡, 看到 boot 界面直接回车.
        3). 等待安装完成.
        4). 删除默认 pxelinux 配置文件.
        5). 在资产系统里设置 product 和 cabinet 等.

        """  
        idc = _get_argument_json(self, "idc", False, loads=True)
        _type = _get_argument_json(self, "type", False, loads=True)
        version = _get_argument_json(self, "version", True, "centos6", loads=True)
        usage = _get_argument_json(self, "usage", False, loads=True)
        product = _get_argument_json(self, "product", False, loads=True)
        sns = _get_argument_json(self, "sns", False, loads=True)
        user_data = _get_argument_json(self, "user_data", True, None, loads=True)       
        email = _get_argument_json(self, "email", True, None, loads=True)

        install_lists = list()
        for i in sns:
            item = {
                "idc": idc, 
                "type": _type, 
                "version": version,
                "usage": usage, 
                "product": product, 
                "sn": i["sn"], 
                "cabinet": i["cabinet"],
                "user_data": user_data
            }
            install_lists.append(item)

        # 首先检查是否有其他 _type 和 version 的机器正在安装, 如果有,
        # 退出; 如果没有, 才继续.
        running_tasks = redis_client_pm.keys("default*")
        if len(running_tasks) > 1:
            message = "has other different task is running:%s" % running_tasks
            ret = {
                "status": "failed", 
                "message": message
            }
            self.write(json.dumps(ret))
            self.finish()

        # 生成创建任务 id.
        task_key = "physical:create_man"
        task_id = "%s:%s" % (task_key, global_id.get())

        queue_dict = {
            "install_lists": install_lists, 
            "task_id": task_id,
            "email": email
        }
        redis_client_pm.lpush("queue:create_man", queue_dict)

        _url = "%s/%s" % (PM_TASK_BASE_URL, task_id)
        ret = {
            "status": "creating", 
            "message": _url
        }
        self.write(json.dumps(ret))


class MessageHandler(tornado.web.RequestHandler):
    @decorator.authenticate_decorator
    def get(self):
        """ 装机%post 阶段脚本来请求 sn 的 usage 以申请 hostname.

        """
        sn = self.get_argument("sn")
        ret = {
            "status": "success",
            "message": tmessage.query(sn)
        }
        self.write(json.dumps(ret))

    @decorator.authenticate_decorator
    def post(self):
        """ 机器申请 hostname 和 ip 后传回本系统.

        """        
        sn = self.get_argument("sn")
        hostname = self.get_argument("hostname")
        ip = self.get_argument("ip")

        if tmessage.setup(sn, hostname, ip):
            ret = {
                "status": "success", 
                "message": "hostname and ip have been set to redis."
            }
            self.write(json.dumps(ret))


class TasksHandler(tornado.web.RequestHandler):
    def get(self, task_id):
        """ 查看任务的执行状况.        

        """
        # 由于 redis hash 结构取出来的值是字符串,
        # 这里处理一下, 还原 list 和 dict.
        ret = redis_client_pm.hgetall(task_id)
        _ret = dict()
        for i in ret:
            try:
                if isinstance(eval(ret[i]), list) or \
                    isinstance(eval(ret[i]), dict):
                    _ret[i] = eval(ret[i])
            except Exception, e:
                _ret[i] = ret[i]
        self.write(json.dumps(_ret))


def _get_argument_json(oj, arg, has_default=False, default=None, loads=True):
    """ 获取参数.

    """
    if has_default:
        value = getattr(oj, "get_argument")(arg, default)
    else:
        value = getattr(oj, "get_argument")(arg)
    if value != default and loads:
        return json.loads(value)
    return value
