# -*- coding: utf-8 -*-

''' 记录一些全局变量，特别是需要跨进程访问的全局变量

:date: 2013-12-20
:author: 刘雪彦 <lxy@hesong.net>
'''

__updated__ = '2015-01-15'

prog_args = None
'''命令行参数

.. note:: 在主进程初始化进程池的时候，该变量在子进程中被赋值
'''

main_logging_queue = None
'''多进程的全局日志队列

.. attention:: 仅在主进程有效
'''

main_logging_listener = None
'''多进程的全局日志监听器

.. attention:: 仅在主进程有效
'''

startuptxt = ''

ipc_smartbusclient = None
'''IPC客户端

.. attention:: 仅在主进程有效
'''

net_smartbusclients = []
'''NET客户端列表

.. attention:: 仅在主进程有效
'''

ipsc_set = set()
'''IPSC节点集合

一个 ``set`` 类型全局变量
进程池模式中，它仅在主进程有效

将Smartbus上的IPSC客户端记录在这个集合中，其中每个元素表示一个IPSC客户端连接，其格式是::

    (unitid, clientid)

.. attention:: 仅在主进程有效
'''


executor = None
'''全局 RPC 执行器

类型是 :class:`executor.Executor`

.. attention:: 仅在主进程有效
'''
