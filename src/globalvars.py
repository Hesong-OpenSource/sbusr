# -*- coding: utf-8 -*-

''' 记录一些全局变量，特别是需要跨进程访问的全局变量

:date: 2013-12-20
:author: 刘雪彦 <lxy@hesong.net>
'''

prog_args = None
'''命令行参数'''

main_logging_queue = None
'''多进程的全局日志队列'''

main_logging_listener = None
'''多进程的全局日志监听器'''

startuptxt = ''

ipc_smartbusclient = None
'''IPC客户端

.. note:: 只能有一个
'''

net_smartbusclients = []
'''NET客户端列表
'''

ipsc_set = set()
'''IPSC节点集合

一个 ``set`` 类型全局变量
进程池模式中，它仅在主进程有效

将Smartbus上的IPSC客户端记录在这个集合中，其中每个元素表示一个IPSC客户端连接，其格式是::

    (unitid, clientid)
'''