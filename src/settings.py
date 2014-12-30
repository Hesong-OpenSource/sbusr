# encoding: utf-8

'''配置

:date: 2014-12-26

:author: 刘雪彦
'''


RELOAD_INTERVAL = 120
'''重加载 :mod:`settings` 模块的时间间隔，单位是秒。默认值120秒，不得小于30秒。
'''


EXECUTOR_CONFIG = {
    "pool_model": "ProcessPool",
    "queue_maxsize": 10000,
    "pool_processes": 4,
    "pool_maxtasksperchild": 10000
}
'''执行器设置

这个设置被用于 :class:`executor.Executor` 构造函数的传入参数。

:param pool_model: 执行器的并发模式 ``"ProcessPool"`` 或 ``"ThreadPool"``

    * ``"ProcessPool"`` : 进程池模式。sbusr使用Python标准库的 ``multipleprocessing.pool.Pool`` 并发执行RPC
    * ``"ThreadPool"`` : 线程池模式。sbusr使用Python标准库的 ``multipleprocessing.pool.ThreadPool`` 并发执行RPC

:param queue_maxsize: 任务队列最大值。0，表示无限制。

:param pool_processes: 执行器池的最大数量。 ``None`` 表示使用 CPU 核心数量作为其最大值。

:param pool_maxtasksperchild: 进程池最大执行数量。 ``None`` 表示无限制。超过该值，则重启子进程。仅对进程池模式有效。

.. warning:: 不得删除该变量，不得修改该变量的结构。
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


METHODS_RELOAD_INTERVAL = 180
'''自定义方法模块的重加载时间间隔（秒）

当上次调用自定义方法与本次调用的时间间隔大于该值时，将重新加载方法所在模块

* < 0 表示永远不重新加载
* = 0 表示每次都重新加载
* 默认值是 -1

一旦开启了重加载，开发者就可以随时修改、新建自定义RPC模块，待重加载时间间隔到，这些模块会被sbusr自动重新加载。

.. attention::

    如果模块有语法错误，或者在加载时全局代码执行错误，则不会被重加载
'''


WEBSERVER_LISTEN = (
    8080,  # 监听端口
    "",    # 监听地址
)
"""WEB 服务器监听地址与端口.

.. warning:: 不得删除该变量，不得修改该变量的结构。
"""

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

https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema



'''
