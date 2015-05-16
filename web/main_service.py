#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os
import socket

import ujson as json

import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.escape
import tornado.netutil

from libs import ldapauth, decorator, redisoj
from web.const import BIND_IP, BIND_PORT

from pm.web import service as pm_service


class LdapauthapiHandler(tornado.web.RequestHandler):

    def post(self):
        username = self.get_argument('username')
        if username.endswith("@nosa.me"):
            username = username.strip("@nosa.me")
        password = self.get_argument("password")

        ret_dict = {}
        demo = ldapauth.Auth()
        if demo.auth(username, password):
            email = username + "@nosa.me"
            self.set_secure_cookie("nosa_user", email, expires_days=30)
            ret_dict["result"] = "success"
        else:
            ret_dict["result"] = "error"
        self.write(json.dumps(ret_dict))


class PostCustomHandler(tornado.web.RequestHandler):

    def get(self):
        key = self.get_argument('key')

        from libs import redisoj
        from web.const import REDIS_DB_COMMON

        # REDIS_DB_COMMON 专门用于存储 user_data 信息
        client = redisoj.generate(REDIS_DB_COMMON)
        if client.exists(key):
            self.write(client.get(key))
        else:
            self.write("")       


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/api/v1/ldapauth", LdapauthapiHandler), 
            # 物理机装机 API, 不是 RESTful API.
            (r"/api/v1/pm/check/?", pm_service.CheckHandler), 
            (r"/api/v1/pm/create/?", pm_service.CreateHandler),
            (r"/api/v1/pm/create_man/?", pm_service.CreateManHandler),
            (r"/api/v1/pm/message/?", pm_service.MessageHandler),
            (r"/api/v1/pm/tasks/([^/]+)/?", pm_service.TasksHandler),                                   
            # 用于获取装机之后的自定义脚本.
            (r"/api/v1/postcustom/?", PostCustomHandler),
        ]

        settings = {
            "debug": False, 
            "cookie_secret": "z1DAVh+WTvy23pWGmO1tJCQLETQYUznEuYskSF062J0To", 
            #"xsrf_cookies":True, 
        }

        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    sockets = tornado.netutil.bind_sockets(
        BIND_PORT, address=BIND_IP, family=socket.AF_INET)
    tornado.process.fork_processes(0)

    application = Application()
    http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
    http_server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()