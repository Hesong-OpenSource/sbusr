# -*- coding: utf-8 -*-

'''配置

:date: 2014-12-26
:author: 刘雪彦 <lxy@hesong.net>
'''

SMARTBUS_CONFIG = {
    "type": "net",
    "initialize": {
        "unitid": 19
    },
    "clients": [
        {
            "localClientId": 0,
            "localClientType": 19,
            "masterHost": "10.4.62.45",
            "masterPort": 8089,
            "slaverHost": None,
            "slaverPort": 0,
            "authorUsr": None,
            "authorPwd": None,
            "extInfo": None,
            "encoding": "utf-8"
        }
    ]
}
'''SmartBus客户端配置

:param type: smartbus客户端类型，有效值：``"net"`` 或 ``"ipc"``

    * ``"net"`` : 使用smartbus网络通信客户端
    * ``"ipc"`` : 使用smartbus进程通信客户端

:param initialize: smartbus客户端模块初始化参数属性字段

    * 当 ``type`` 属性为 ``"net"`` 时，该属性必须设置一个属性 ``unitid``
    * 当 ``type`` 属性为 ``"ipc"`` 时，该属性必须设置两个属性 ``clientid`` 与 ``clienttype``

    具体含义请参考 smartbus　文档

:param instance: smartbus进程通信客户端地址参数属性字段

    该 dict 属性需要设置3个属性：

    * username
    * password
    * extInfo

    具体含义请参考 smartbus　文档

    .. attention:: 仅当 ``type`` 属性为 ``"ipc"`` 时有效

:param clients: smartbus网络通信客户端地址参数属性字段

    该 list 属性的每个成员表示一个smartbus网络通信客户端，每个客户端的参数都是：

    * localClientId
    * localClientType
    * masterHost
    * masterPort
    * slaverHost
    * slaverPort
    * authorUsr
    * authorPwd
    * extInfo

    具体含义请参考 smartbus　文档

    .. attention:: 仅当 ``type`` 属性为 ``"net"`` 时有效
'''

SMARTBUS_NOTIFY_TTL = 10000
'''通过smartbus发送给IPSC流程的notify消息的生存期（ms）
'''

WEBSERVER_LISTEN = (
    8080,  # 监听端口
    "",  # 监听地址
)
"""WEB 服务器监听地址与端口.

.. warning:: 不得删除该变量，不得修改该变量的结构。
"""

EXECUTOR_CONFIG = {
    "queue_maxsize": 1000,
    "pool_processes": None,
    "pool_maxtasksperchild": 1000
}
'''执行器设置

这个设置被用于 :class:`executor.Executor` 构造函数的传入参数。

:param queue_maxsize: 任务队列最大值。0，表示无限制。
:param pool_processes: 执行器池的最大数量。 ``None`` 表示使用 CPU 核心数量作为其最大值。
:param pool_maxtasksperchild: 进程池最大执行数量。 ``None`` 表示无限制。超过该值，则重启子进程。

.. warning:: 不得删除该变量，不得修改该变量的结构。
'''

RELOAD_INTERVAL = 120
'''配置文件重加载时间间隔（秒）

每隔一段时间重加载 :mod:`settings` 模块

默认值：120
'''

FLOW_ACK_TIMEOUT = 15
'''流程调用时等待调用结果的最大时间，单位是秒
'''

LOGGING_CONFIG = {
    "version": 1,
    "root": {
        "level": "INFO",
        "handlers": [
            "console",
            "file",
            "fileErr"
        ]
    },
    "loggers": {
        "smartbus.netclient.client.Client": {
            "level": "INFO",
            "handlers": [
                "smartbusFile"
            ]
        },
        "smartbus.ipcclient.client.Client": {
            "level": "INFO",
            "handlers": [
                "smartbusFile"
            ]
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "normal",
            "stream": "ext://sys.stdout"
        },
        "consoleErr": {
            "class": "logging.StreamHandler",
            "formatter": "normal",
            "level": "ERROR",
            "stream": "ext://sys.stderr"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "normal",
            "level": "DEBUG",
            "filename": "../logs/log",
            "maxBytes": 10485760,
            "backupCount": 1000
        },
        "fileErr": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "normal",
            "level": "ERROR",
            "filename": "../logs/err",
            "maxBytes": 10485760,
            "backupCount": 1000
        },
        "smartbusFile": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "normal",
            "filename": "../logs/smartbus",
            "maxBytes": 10485760,
            "backupCount": 1000
        }
    },
    "formatters": {
        "normal": {
            "format": "%(asctime)s <%(processName)-10s,%(threadName)-10s> %(levelname)-8s %(name)s - %(message)s"
        }
    }
}
'''日志设置

其格式请参考:
https://docs.python.org/2/library/logging.config.html#configuration-dictionary-schema
与
https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema
'''
