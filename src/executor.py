# -*- coding: utf-8 -*-

''' 该模块定义了 MySQL 任务执行器，以及执行体

服务器模块 :mod:`server` 将来自 smartbus 的请求传递给执行器类 :class:`Executor` 的实例，
执行器解析请求的 JSON RPC 格式，并分配执行体，在线程池中执行，
然后返回结果。

:date: 2013-12-14

:author: tanbro
'''

import sys
import logging.handlers
import time
import json
import importlib
from multiprocessing.pool import ThreadPool, Pool
import threading
try:
    import queue
except ImportError:
    import Queue as queue
try:
    from logging.handlers import QueueListener
except ImportError:
    from queuelistener import QueueListener
from functools import partial

import jsonrpc
import settings
import globalvars

CMDTYPE_JSONRPC_REQ = 211
'''JSONRPC 请求. 用于 smartbus 客户端 send 函数的 cmd_type 参数.'''

CMDTYPE_JSONRPC_RES = 212
'''JSONRPC 回复. 用于 smartbus 客户端 send 函数的 cmd_type 参数.'''


class Executor(QueueListener):

    '''smarbus JSON RPC 请求执行器

    :param pool_model: 执行器池模型
        默认值为 ``None`` ，表示使用线程池。
        ``"ThreadPool"`` 表示使用线程池。
        ``"ProcessPool"`` 表示使用进程池。

    :param queue_maxsize: 任务队列最大值
        默认为0，表示无限制。

    :param pool_processes: 执行器池的最大数量
        默认为 none，表示使用 CPU 核心数量作为其最大值

    :param pool_maxtasksperchild: 进程池最大执行数量
        默认为 None，表示无限制。超过该值，则重启子进程。仅对进程池模型有效。

    在接收到 smartbus 请求后，需要向这个队列放置数据，数据的格式是： ``client, pack_info, txt``
    分别是：收到数据的 smartbus 客户端的实例，数据包附加信息，数据文本。

    收到数据后，本类型的实例将按照 JSON-RPC 格式解析数据，并执行 JSON RPC 请求，最后将执行结果通过 smartbus 客户端进行返回。
    返回数据格式是符合 JSON RPC 标准的字符串。
    '''

    def __init__(self, pool_model=None, queue_maxsize=0, pool_processes=None, pool_maxtasksperchild=None):
        if not pool_model:
            pool_model_name = 'ThreadPool'
        elif pool_model.strip().upper() in ('PROCESS', 'PROCESSES', 'PROCESSING', 'PROCESSPOOL', 'POOL', 'P'):
            pool_model_name = 'ProcessPool'
        elif pool_model.strip().upper() in ('THREAD', 'THREADS', 'THREADING', 'THREADINGPOOL', 'T'):
            pool_model_name = 'ThreadPool'
        else:
            raise ValueError('Unknown pool_model {}'.format(pool_model))

        if pool_model_name == 'ProcessPool':
            self._pool = Pool(
                pool_processes,
                _subproc_init,
                (globalvars.prog_args,
                 globalvars.main_logging_queue, logging.root.level),
                pool_maxtasksperchild
            )
        elif pool_model_name == 'ThreadPool':
            self._pool = ThreadPool(pool_processes)
        else:
            raise NotImplementedError()

        QueueListener.__init__(self, queue.Queue(queue_maxsize))

        logging.getLogger('Executor').info(
            'construct: pool_model=%s, queue_maxsize=%s, pool_processes=%s',
            pool_model_name, queue_maxsize, pool_processes)

    def put(self, client, pack_info, txt):
        self.queue.put((client, pack_info, txt, time.time()))

    def stop(self):
        logging.getLogger('Executor').info('stopping')
        QueueListener.stop(self)
        self._pool.terminate()
        self._pool.join()
        logging.getLogger('Executor').info('stopped')

    def handle(self, record):
        if globalvars.prog_args.more_detailed_logging:
            logging.getLogger('Executor').debug('handle(record=%s)', record)
        request = None
        try:
            client, pack_info, txt, begin_time = record
            try:
                request, _, _ = jsonrpc.parse(txt)
            except Exception as e:
                logging.getLogger('Executor').error(
                    'jsonrpc parse error: %s %s', type(e), e)
            if request:
                _id = request.get('id')
                _method = request['method']
                _args = request['args']
                _kwargs = request['kwargs']

                def _callback(result):
                    try:
                        if isinstance(result, Exception):
                            error = result
                            response = {
                                'jsonrpc': jsonrpc.jsonrpc_version,
                                'id': _id,
                                'error': {
                                    'code': -32500,
                                    'message': '{} {}'.format(type(error), error),
                                    'data': None,
                                }
                            }
                            data = json.dumps(response)
                            client.send(
                                0, CMDTYPE_JSONRPC_RES, pack_info.srcUnitId, pack_info.srcUnitClientId, -1, data, 'utf-8')
                            raise error
                        if globalvars.prog_args.more_detailed_logging:
                            logging.getLogger('Executor').debug(
                                'call back:\n    result=%s %s\n    duration=%s\n    request=%s',
                                type(result), result, time.time() -
                                begin_time, record
                            )
                        if _id:
                            response = {
                                'jsonrpc': jsonrpc.jsonrpc_version,
                                'id': _id,
                                'result': result,
                            }
                            data = json.dumps(response)
                            client.send(
                                0, CMDTYPE_JSONRPC_RES, pack_info.srcUnitId, pack_info.srcUnitClientId, -1, data, 'utf-8')
                    except Exception as e:
                        if globalvars.prog_args.more_detailed_logging:
                            logging.getLogger('Executor').exception(
                                'error occured in _callback():\n    request=%s', record)
                        else:
                            logging.getLogger('Executor').exception(
                                'error occured in _callback():\n    error=%s', e)
                pass  # end of _callback

                def _error_callback(error):
                    try:
                        # Python3.4 issue20980: In multiprocessing.pool,
                        # ExceptionWithTraceback should derive from Exception
                        if not isinstance(error, Exception):
                            error = error.exc
                        if globalvars.prog_args.more_detailed_logging:
                            logging.getLogger('Executor').exception(
                                'error callback:\n    duration=%s\n    request=%s:\n  %s %s',
                                time.time() -
                                begin_time, record, type(error), error
                            )
                        else:
                            logging.getLogger('Executor').error(
                                'error callback:\n    %s %s\n    duration=%s\n    request=%s\n  %s %s',
                                type(error), error, time.time() -
                                begin_time, record, type(error), error
                            )
                        if _id:
                            if isinstance(error, jsonrpc.Error):
                                response = error.to_dict()
                                response['id'] = _id
                            else:
                                response = {
                                    'jsonrpc': jsonrpc.jsonrpc_version,
                                    'id': _id,
                                    'error': {
                                        'code': -32500,
                                        'message': '{} {}'.format(type(error), error),
                                        'data': None,
                                    }
                                }
                            data = json.dumps(response)
                            client.send(
                                0, CMDTYPE_JSONRPC_RES, pack_info.srcUnitId, pack_info.srcUnitClientId, -1, data, 'utf-8')
                    except Exception as e:
                        if globalvars.prog_args.more_detailed_logging:
                            logging.getLogger('Executor').exception(
                                'error occured in _error_callback():\n    request=%s', record)
                        else:
                            logging.getLogger('Executor').error(
                                'error occured in _error_callback():\n    error=%s', e)
                pass  # end of _error_callback

                if globalvars.prog_args.more_detailed_logging:
                    logging.getLogger('Executor').debug(
                        'apply_async to %s', _poolfunc)
                if sys.version_info[0] < 3:
                    self._pool.apply_async(
                        partial(_poolfunc, _method),
                        _args, _kwargs, _callback
                    )
                else:
                    self._pool.apply_async(
                        partial(_poolfunc, _method),
                        _args, _kwargs, _callback, _error_callback
                    )

        except Exception as e:
            if globalvars.prog_args.more_detailed_logging:
                logging.getLogger('Executor').exception(
                    'error occured in handle():\n    request=%s',
                    record)
            else:
                logging.getLogger('Executor').error(
                    'error occured in handle():\n    error=%s',
                    e)


mod_map_lock = threading.Lock()
mod_map = {}


def _poolfunc(method, *args, **kwargs):
    _method_parts = method.split('.')
    if len(_method_parts) == 1:
        _module_name = 'methods'
        _func_name = method
    else:
        _module_name = 'methods.{}'.format('.'.join(_method_parts[:-1]))
        _func_name = _method_parts[-1]
    with mod_map_lock:
        _modobj = importlib.import_module(_module_name)
        mod_info = mod_map[_module_name] = mod_map.get(_module_name, {})
        if not mod_info:
            mod_info['load_time'] = time.time()
    last_load_time = mod_info.get('load_time', 0)
    try:
        reloadinterval = float(settings.METHODS_RELOAD_INTERVAL)
    except Exception:
        reloadinterval = -1
    if reloadinterval >= 0 and time.time() - last_load_time > reloadinterval:
        try:
            logging.getLogger('Executor').info(
                'reload module %s when processing method %s',
                _module_name, method)
            with mod_map_lock:
                _modobj = importlib.reload(_modobj)
                mod_info['load_time'] = time.time()
        except Exception as e:
            if globalvars.prog_args.more_detailed_logging:
                logging.getLogger('Executor').exception(
                    'reload module error when processing method %s',
                    method)
            else:
                logging.getLogger('Executor').error(
                    'reload module error when processing method %s: %s',
                    method, e)
    _callobj = getattr(_modobj, _func_name)
    return _callobj(*args, **kwargs)


def _subproc_init(progargs, logging_queue, logging_root_level):
    try:
        logging.root.handlers.clear()
    except AttributeError:
        del logging.root.handlers[:]
    logging.root.addHandler(logging.handlers.QueueHandler(logging_queue))
    logging.root.setLevel(logging_root_level)
    logging.info('subproc init')
    globalvars.prog_args = progargs
