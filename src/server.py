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
from smartbus._c_smartbus import SMARTBUS_NODECLI_TYPE_IPSC

from tornado import ioloop, web, httpserver

import settings
import globalvars
import executor
import webhandlers

_executor = None
'''全局 RPC 执行器

进程池模式中，它仅在主进程有效

类型是 :class:`executor.Executor`
'''


def _smartbus_global_connect(unitid, clientid, clienttype, accessunit, status, ext_info):
    logging.getLogger('smartbusclient').debug(
            'smartbus global connect. '
            'unitid=%s, clientid=%s, clienttype=%s, accessunit=%s, status=%s, ext_info=%s',
            unitid, clientid, clienttype, accessunit, status, ext_info
    )
    if clienttype == SMARTBUS_NODECLI_TYPE_IPSC:
        if status == 0:  # 丢失连接
            logging.getLogger('smartbusclient').warn(
                    'IPSC<%s:%s> connection lost',
                    unitid, clientid, clienttype
            )
            try:
                globalvars.ipsc_set.remove((unitid, clientid))
            except KeyError:
                logging.getLogger('smartbusclient').warn(
                         'IPSC<%s:%s> not found in the list',
                         unitid, clientid
                )
        elif status == 1:  # 新建连接
            logging.getLogger('smartbusclient').info(
                     'IPSC<%s:%s> connection created',
                     unitid, clientid
            )
            globalvars.ipsc_set.add((unitid, clientid))
        else:  # 存在连接
            logging.getLogger('smartbusclient').debug(
                      'IPSC<%s:%s> connection confirmed',
                      unitid, clientid
            )
            globalvars.ipsc_set.add((unitid, clientid))


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
    

def _smartbus_invoke_flow_err(packInfo, project, invokeId, errno):
    try:
        err = webhandlers.FlowInvokeErr(packInfo, project, invokeId, errno)
        webhandlers.FlowHandler.set_flow_err(err)
    except:
        logging.getLogger('smartbusclient').exception('_smartbus_invoke_flow_err')


def _smartbus_invoke_flow_ack(packInfo, project, invokeId, ack, msg):
    try:
        ack = webhandlers.FlowInvokeAck(packInfo, project, invokeId, ack, msg)
        webhandlers.FlowHandler.set_flow_ack(ack)
    except:
        logging.getLogger('smartbusclient').exception('_smartbus_invoke_flow_ack')


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
        globalvars.main_logging_queue = multiprocessing.queues.Queue()
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
        unitid = settings.SMARTBUS_CONFIG['initialize']['unitid']
        logging.info('init smartbus net client <%s>', unitid)
        smartbus.netclient.Client.initialize(unitid)
        for kwd in settings.SMARTBUS_CONFIG['clients']:
            logging.info('create smartbus net client (%s)', kwd)
            _sbc = smartbus.netclient.Client(**kwd)
            _sbc.onConnectSuccess = partial(_smartbus_connect_success, _sbc)
            _sbc.onConnectFail = partial(_smartbus_connect_fail, _sbc)
            _sbc.onDisconnect = partial(_smartbus_disconnected, _sbc)
            _sbc.onReceiveText = partial(_smartbus_receive_text, _sbc)
            _sbc.onInvokeFlowError = partial(_smartbus_invoke_flow_err, _sbc)
            _sbc.onInvokeFlowAcknowledge = partial(_smartbus_invoke_flow_ack, _sbc)
            _sbc.connect()
            globalvars.net_smartbusclients.append(_sbc)
    elif smartbus_type == 'IPC':
        clientid = settings.SMARTBUS_CONFIG['initialize']['clientid']
        clienttype = settings.SMARTBUS_CONFIG['initialize']['clienttype']
        logging.info('init smartbus ipc client<%s(%s)>', clientid, clienttype)
        smartbus.ipcclient.Client.initialize(clientid, clienttype)
        _sbc = smartbus.ipcclient.Client.instance(**settings.SMARTBUS_CONFIG.get('instance', {}))
        _sbc.onConnectSuccess = partial(_smartbus_connect_success, _sbc)
        _sbc.onConnectFail = partial(_smartbus_connect_fail, _sbc)
        _sbc.onDisconnect = partial(_smartbus_disconnected, _sbc)
        _sbc.onReceiveText = partial(_smartbus_receive_text, _sbc)
        _sbc.onInvokeFlowError = partial(_smartbus_invoke_flow_err, _sbc)
        _sbc.onInvokeFlowAcknowledge = partial(_smartbus_invoke_flow_ack, _sbc)
        _sbc.connect()
        globalvars.ipc_smartbusclient = _sbc

    # startup settings' auto-reload
    start_auto_reload_settings()

    # setup tornado-web server
    application = web.Application([
        (r"/flow", webhandlers.FlowHandler),
    ])
    http_server = httpserver.HTTPServer(application)
    http_server.listen(*settings.WEBSERVER_LISTEN)
    ioloop.IOLoop.instance().start()



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
