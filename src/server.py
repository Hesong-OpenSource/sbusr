# encoding: utf-8

''' smartbus-mysql-proxy 服务模块

该模块负责初始化服务程序，维持smartbus客户端的连接，分配来自smartbus的sql任务，并返回结果。

:date: 2013-12-13

:author: tanbro
'''

from __future__ import print_function, unicode_literals, absolute_import

import sys

PY3K = sys.version_info[0] > 2

import logging.config
import logging.handlers
import importlib
import multiprocessing
import sched
from functools import partial

import smartbus.netclient
import smartbus.ipcclient

import settings
import globalvars
import executor

_executor = None

def _smartbus_connect_success(client, unit_id):
    logging.getLogger('smartbusclient').info(
                'smartbus connect success. client=%s, unit_id=%s',
                client, unit_id)


def _smartbus_connect_fail(client, unit_id, errno):
    logging.getLogger('smartbusclient').error(
                'smartbus connect fail. client=%s, unit_id=%s, errno=%s',
                client, unit_id, errno)


def _smartbus_disconnected(client):
    logging.getLogger('smartbusclient').error(
                'smartbus disconnected. client=%s', client)


def _smartbus_receive_text(client, pack_info, txt):
    _executor.put(client, pack_info, txt)


def startup(args):
    '''启动服务

    :param args: 命令行参数
    '''
    globalvars.prog_args = args
    ###########################
    # 初始化logging设置
    try:
        # 使用设置模块中的设置
        logging.config.dictConfig(settings.LOGGING_CONFIG)
    except Exception as excp:
        # 使用默认的设置
        print('An exception occurred when perform '
              'logging.config.dictConfig(settings.LOGGING_CONFIG):'
              '\n{}\n'
              'using the default logging configuration'.format(excp),
              file=sys.stderr
            )
        logging_fmt = logging.Formatter(fmt='%(asctime)s <%(processName)-10s,%(threadName)-10s> %(levelname)-8s %(name)s - %(message)s')
        logging_handler = logging.StreamHandler()
        logging_handler.setFormatter(logging_fmt)
        logging.root.handlers.clear()
        logging.root.handlers.append(logging_handler)
    ################################################
    # 初始化 logging 监听器/队列
    print('initialize main logger')
    if not globalvars.main_logging_queue:
        print('create main_logging_queue')
        globalvars.main_logging_queue = multiprocessing.Queue()
    if not globalvars.main_logging_listener:
        print('create main_logging_listener')
        globalvars.main_logging_listener = logging.handlers.QueueListener(
                    globalvars.main_logging_queue, *logging.root.handlers)
    print('start main_logging_listener')
    globalvars.main_logging_listener.start()
    #
    print('startup')
    logging.info('--- startup ---')
    logging.info('%s', globalvars.startuptxt)
    # ##############################################
    # 启动 smartbus 监听器
    logging.info('new Executor()')
    global _executor
    _executor = executor.Executor(settings.EXECUTOR_CONFIG)
    logging.info('executor.start()')
    _executor.start()
    #####################################
    # 初始化 SmartBus 客户端
    smartbus_type = settings.SMARTBUS_CONFIG['type'].strip().upper()
    if smartbus_type == 'NET':
        logging.info('init smartbus net client')
        unitid = settings.SMARTBUS_CONFIG['initialize']['unitid']
        smartbus.netclient.Client.initialize(unitid)
        for kwd in settings.SMARTBUS_CONFIG['clients']:
            smartbus_client = smartbus.netclient.Client(**kwd)
            smartbus_client.onConnectSuccess = partial(_smartbus_connect_success, smartbus_client)
            smartbus_client.onConnectFail = partial(_smartbus_connect_fail, smartbus_client)
            smartbus_client.onDisconnect = partial(_smartbus_disconnected, smartbus_client)
            smartbus_client.onReceiveText = partial(_smartbus_receive_text, smartbus_client)
            smartbus_client.connect()
    elif smartbus_type == 'IPC':
        logging.info('init smartbus ipc client')
        clientid = settings.SMARTBUS_CONFIG['initialize']['clientid']
        clienttype = settings.SMARTBUS_CONFIG['initialize']['clienttype']
        smartbus.ipcclient.Client.initialize(clientid, clienttype)
        smartbus_client = smartbus.ipcclient.Client.instance(**settings.SMARTBUS_CONFIG.get('instance', {}))
        smartbus_client.onConnectSuccess = partial(_smartbus_connect_success, smartbus_client)
        smartbus_client.onConnectFail = partial(_smartbus_connect_fail, smartbus_client)
        smartbus_client.onDisconnect = partial(_smartbus_disconnected, smartbus_client)
        smartbus_client.onReceiveText = partial(_smartbus_receive_text, smartbus_client)
        smartbus_client.connect()

    #
    start_auto_reload_settings()

    #
    while True:
        if PY3K:
            input()
        else:
            raw_input()


def reload_settings():
    '''重新加载设置
    仅仅重加载那些不用重启就生效的设置
    '''
    logging.debug('reload settings')
    importlib.reload('settings')


def start_auto_reload_settings():
    logging.debug('start auto reload settings')

    def _action_func():
        try:
            reload_settings()
        finally:
            _enter_schd()

    def _get_delay():
        _default = 120
        _min = 30
        try:
            result = float(settings.RELOAD_INTERVAL)
            if result < _min:
                result = _default
        except:
            result = 120
        return result

    _enter_schd = lambda: schd.enter(_get_delay(), 0, _action_func)
    schd = sched.scheduler()
    _enter_schd()
    schd.run()
