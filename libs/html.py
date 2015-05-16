#-*- coding: utf-8 -*-

""" 发邮件的html格式.

"""

"""
>>> def print_everything(*args):
        for count, thing in enumerate(args):
...         print '{0}. {1}'.format(count, thing)
...
>>> print_everything('apple', 'banana', 'cabbage')
0. apple
1. banana
2. cabbage

>>> def table_things(**kwargs):
...     for name, value in kwargs.items():
...         print '{0} = {1}'.format(name, value)
...
>>> table_things(apple = 'fruit', cabbage = 'vegetable')
cabbage = vegetable
apple = fruit
"""


def get(mylist):
    """ mylist 里面是 dict, dict 元素需要是一样.

    """
    if not mylist:
        return ""

    keys = [
        "idc", 
        "type", 
        "version",
        "device",
        "num",
        "usage", 
        "sn", 
        "cabinet",
        "hostname",
        "ip", 
        "product", 
        "status",
        "result", 
        "message"
    ]

    _list = []   # 临时 _list, 存放 mylist 里面的 dict 的 key.
    _dict = mylist[0]

    for key in keys:
        if key in _dict:
            _list.append(key)

    context = "%s<br/>" % "     ".join(_list)

    for _dict in mylist:
        for key in _list:
            context += "%s     " % _dict[key]
        context += "<br/>"

    return context