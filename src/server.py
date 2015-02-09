# -*- coding: utf-8 -*-

'''服务

:date: 2013-12-13
:author: 刘雪彦 <lxy@hesong.net>

该模块负责:

* 维持smartbus客户端的连接
* 分配及执行来自smartbus的任务，并返回结果。
* 启动Web程序

'''

from __future__ import print_function, unicode_literals, absolute_import

__updated__ = '2015-02-09'

import sys
PY3K = sys.version_info[0] > 2

import logging.config
import logging.handlers
import multiprocessing
from functools import partial

import smartbus.netclient
import smartbus.ipcclient
from smartbus._c_smartbus import SMARTBUS_NODECLI_TYPE_IPSC

from tornado import ioloop, web, httpserver

import settings
import globalvars
import executor
import webhandlers


def _smartbus_global_connect(unitid, clientid, clienttype, accessunit, status, ext_info):
    logging.getLogger('smartbusclient').debug(
        'smartbus global connect. '
        'unitid=%s, clientid=%s, clienttype=%s, accessunit=%s, status=%s, ext_info=%s',
        unitid, clientid, clienttype, accessunit, status, ext_info
    )
    if clienttype == SMARTBUS_NODECLI_TYPE_IPSC:
        if status == 0:  # 丢失连接
            logging.getLogger('smartbusclient').warning(
                'IPSC<%s:%s> connection lost',
                unitid, clientid, clienttype
            )
            try:
                globalvars.ipsc_set.remove((unitid, clientid))
            except KeyError:
                logging.getLogger('smartbusclient').warning(
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
    globalvars.executor.put(client, pack_info, txt)


def _smartbus_invoke_flow_ack(packInfo, project, invokeId, ack, msg):
    if ack == 1:
        logging.getLogger('smartbusclient').debug(
            '_smartbus_invoke_flow_ack(packInfo=%s, project=%s, invokeId=%s, ack=%s, msg=%s)',
            packInfo, project, invokeId, ack, msg
        )
    else:
        logging.getLogger('smartbusclient').error(
            '_smartbus_invoke_flow_ack(packInfo=%s, project=%s, invokeId=%s, ack=%s, msg=%s)',
            packInfo, project, invokeId, ack, msg
        )
    try:
        ack = webhandlers.FlowInvokeAck(packInfo, project, invokeId, ack, msg)
        webhandlers.FlowHandler.set_flow_ack(ack)
    except:
        logging.getLogger('smartbusclient').exception(
            '_smartbus_invoke_flow_ack')

def run(args):
    '''运行服务

    :param args: 命令行参数
    
    .. attention:: 该函数将“阻塞”，直到服务结束才会返回
    '''

    # 程序启动参数赋值到全局变量
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
        logging_fmt = logging.Formatter(
            fmt='%(asctime)s <%(processName)-10s,%(threadName)-10s> %(levelname)-8s %(name)s - %(message)s')
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
    # 启动 smartbus 执行器
    logging.info('new Executor()')
    globalvars.executor = executor.Executor(**settings.EXECUTOR_CONFIG)
    logging.info('executor.start()')
    globalvars.executor.start()
    #####################################
    # 初始化 SmartBus 客户端
    smartbus_type = settings.SMARTBUS_CONFIG['type'].strip().upper()
    if smartbus_type == 'NET':
        unitid = settings.SMARTBUS_CONFIG['initialize']['unitid']
        logging.info('init smartbus net client <%s>', unitid)
        smartbus.netclient.Client.initialize(unitid, _smartbus_global_connect)
        for kwd in settings.SMARTBUS_CONFIG['clients']:
            logging.info('create smartbus net client (%s)', kwd)
            _sbc = smartbus.netclient.Client(**kwd)
            _sbc.onConnectSuccess = partial(_smartbus_connect_success, _sbc)
            _sbc.onConnectFail = partial(_smartbus_connect_fail, _sbc)
            _sbc.onDisconnect = partial(_smartbus_disconnected, _sbc)
            _sbc.onReceiveText = partial(_smartbus_receive_text, _sbc)
            _sbc.onInvokeFlowAcknowledge = partial(
                _smartbus_invoke_flow_ack, _sbc)
            _sbc.connect()
            globalvars.net_smartbusclients.append(_sbc)
    elif smartbus_type == 'IPC':
        clientid = settings.SMARTBUS_CONFIG['initialize']['clientid']
        clienttype = settings.SMARTBUS_CONFIG['initialize']['clienttype']
        logging.info('init smartbus ipc client<%s(%s)>', clientid, clienttype)
        smartbus.ipcclient.Client.initialize(clientid, clienttype, _smartbus_global_connect)
        _sbc = smartbus.ipcclient.Client.instance(
            **settings.SMARTBUS_CONFIG.get('instance', {}))
        _sbc.onConnectSuccess = partial(_smartbus_connect_success, _sbc)
        _sbc.onConnectFail = partial(_smartbus_connect_fail, _sbc)
        _sbc.onDisconnect = partial(_smartbus_disconnected, _sbc)
        _sbc.onReceiveText = partial(_smartbus_receive_text, _sbc)
        _sbc.onInvokeFlowAcknowledge = partial(_smartbus_invoke_flow_ack, _sbc)
        _sbc.connect()
        globalvars.ipc_smartbusclient = _sbc

    # setup tornado-web server
    application = web.Application([
        (r"/sys/reset", webhandlers.ResetHandler),
        (r"/api/flow", webhandlers.FlowHandler),
    ])
    webserver = httpserver.HTTPServer(application)
    webserver.listen(*settings.WEBSERVER_LISTEN)
    logging.info('http server listening at %s ...', settings.WEBSERVER_LISTEN)
    logging.info('ioloop.IOLoop.instance().start() >>>')
    ioloop.IOLoop.instance().start()
    logging.warning('ioloop.IOLoop.instance().start() <<<')

    # stop
    # stop executor
    logging.warning('stopping...')
    logging.warning('stopping executor...')
    globalvars.executor.stop()
    logging.warning('executor stopped!')
    # stop main_logging_listener
    logging.warning('stopping main logging listener...')
    globalvars.main_logging_listener.stop()
    logging.warning('main logging listener stopped!')


def stop():
    '''停止服务
    
    .. attention:: 该函数是异步的，在它执行后， :func:`server.run` 将会退出 IOLoop ，但是 `stop` 的返回与之无关。
    '''
    logging.warning('stop()')
    ioloop.IOLoop.instance().stop()
