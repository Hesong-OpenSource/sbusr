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

用于 :class:`executor.Executor` 的构造函数

不得删除该变量；不得修改该变量的结构
'''


SMARTBUS_CONFIG = {
    "type": "net",
    "initialize": {
        "unitid": 19
    },
    "clients": [
        {
            "localClientId":0,
            "localClientType":19,
            "masterHost":"10.4.62.45",
            "masterPort":8089,
            "slaverHost":None,
            "slaverPort":0,
            "authorUsr":None,
            "authorPwd":None,
            "extInfo":None,
            "encoding":"utf-8"
        }
    ]
}
'''SmartBus客户端配置
'''


METHODS_RELOAD_INTERVAL = 180
'''自定义方法模块的重加载时间间隔（秒）

当上次调用自定义方法与本次调用的时间间隔大于该值时，将重新加载方法所在模块

* < 0 表示永远不重新加载
* = 0 表示每次都重新加载
* 默认值是 -1
''' 


LOGGING_CONFIG = {
    "version":1,
    "root":{
        "level":"INFO",
        "handlers":[
            "console",
            "file",
            "fileErr"
        ]
    },
    "loggers":{
        "smartbus.netclient.client.Client":{
            "level":"INFO",
            "handlers":[
                "smartbusFile"
            ]
        },
        "smartbus.ipcclient.client.Client":{
            "level":"INFO",
            "handlers":[
                "smartbusFile"
            ]
        }
    },
    "handlers":{
        "console":{
            "class":"logging.StreamHandler",
            "formatter":"normal",
            "stream":"ext://sys.stdout"
        },
        "consoleErr":{
            "class":"logging.StreamHandler",
            "formatter":"normal",
            "level":"ERROR",
            "stream":"ext://sys.stderr"
        },
        "file":{
            "class":"logging.handlers.RotatingFileHandler",
            "formatter":"normal",
            "level":"DEBUG",
            "filename":"../logs/log",
            "maxBytes":10485760,
            "backupCount":1000
        },
        "fileErr":{
            "class":"logging.handlers.RotatingFileHandler",
            "formatter":"normal",
            "level":"ERROR",
            "filename":"../logs/err",
            "maxBytes":10485760,
            "backupCount":1000
        },
        "smartbusFile":{
            "class":"logging.handlers.RotatingFileHandler",
            "formatter":"normal",
            "filename":"../logs/smartbus",
            "maxBytes":10485760,
            "backupCount":1000
        }
    },
    "formatters":{
        "normal":{
            "format":"%(asctime)s <%(processName)-10s,%(threadName)-10s> %(levelname)-8s %(name)s - %(message)s"
        }
    }
}
'''日志设置
'''
