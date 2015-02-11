# -*- coding: utf-8 -*-

''' 该模块定义了 RPC 任务执行器

服务器模块 :mod:`server` 将来自 smartbus 的请求传递给执行器类 :class:`Executor` 的实例，
执行器解析请求的 JSON RPC 格式，并分配执行体，在线程池中执行，
然后返回结果。

:date: 2013-12-14
:author: 刘雪彦 <lxy@hesong.net>
'''

from __future__ import print_function, unicode_literals, absolute_import

__updated__ = '2015-02-11'

import sys
PY3K = sys.version_info[0] > 2
import logging
import time
import json
from multiprocessing.pool import Pool
import threading
try:
    import queue
except ImportError:
    import Queue as queue
try:
    from logging.handlers import QueueListener
except ImportError:
    from loggingqueue import QueueListener
try:
    from logging.handlers import QueueHandler
except ImportError:
    from loggingqueue import QueueHandler
from functools import partial
import importlib
import inspect

import jsonrpc
import globalvars
import settings


class Executor(QueueListener):
    '''smarbus JSON RPC 请求执行器

    使用进程池执行 RPC 请求

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

    def __init__(self, queue_maxsize=0, pool_processes=None, pool_maxtasksperchild=None):
        self._pool_kdargs = dict(
            processes=pool_processes,
            initializer=_subproc_init,
            initargs=(
                globalvars.prog_args,
                globalvars.main_logging_queue,
                logging.root.level
            ),
            maxtasksperchild=pool_maxtasksperchild
        )
        self._pool = None
        if PY3K:
            super().__init__(queue.Queue(queue_maxsize))
        else:
            super(Executor, self).__init__(queue.Queue(queue_maxsize))
        if PY3K:
            self._logger = logging.getLogger(self.__class__.__qualname__)
        else:
            self._logger = logging.getLogger(self.__class__.__name__)

    def put(self, client, pack_info, txt):
        self.queue.put((client, pack_info, txt, time.time()))

    def start(self):
        self._logger.info('start() >>>. pool arguments: %s', self._pool_kdargs)
        self._pool = Pool(**self._pool_kdargs)
        if PY3K:
            super().start()
        else:
            super(Executor, self).start()
        self._logger.info('start() <<<')

    def stop(self):
        self._logger.info('stop() >>>')
        super().stop()
        self._logger.debug('pool.terminate() ...')
        self._pool.terminate()
        self._logger.debug('pool.join() ...')
        self._pool.join()
        self._pool = None
        self._logger.info('stop() <<<')

    def handle(self, record):
        if globalvars.prog_args.verbose:
            self._logger.debug('handle(record=%s)', record)
        request = None
        try:
            client, pack_info, txt, begin_time = record
            try:
                request, _, _ = jsonrpc.parse(txt)
            except Exception as e:
                if globalvars.prog_args.verbose:
                    self._logger.error(
                        'JSONRPC parse error: %s %s', type(e), e)
            if request:
                _id = request.get('id')
                _method = request['method']
                _args = request['args']
                _kwargs = request['kwargs']

                def _callback(result):
                    try:
                        if isinstance(result, Exception):  # 如果返回结果是异常，就返回错误结果，并抛出异常
                            error = result
                            if _id:  # 如果有 RPC ID ，就需要返回错误结果
                                if isinstance(error, jsonrpc.Error):  # 处理 jsonrpc.Error 异常
                                    response = error.to_dict()
                                    response['id'] = _id
                                else:  # 处理其它异常
                                    response = {
                                        'jsonrpc': jsonrpc.jsonrpc_version,
                                        'id': _id,
                                        'error': {
                                            'code':-32500,
                                            'message': '{} {}'.format(type(error), error),
                                            'data': None,
                                        }
                                    }
                                data = json.dumps(response)
                                client.sendNotify(pack_info.srcUnitId, pack_info.srcUnitClientId, None, _id, 0, settings.SMARTBUS_NOTIFY_TTL, data)
                            raise error  # 抛出异常
                        if globalvars.prog_args.verbose:
                            self._logger.debug(
                                'call back:\n    result=%s %s\n    duration=%s\n    request=%s',
                                type(result), result, time.time() -
                                begin_time, record
                            )
                        if _id:  # 如果有 RPC ID ，就需要返回执行结果
                            response = {
                                'jsonrpc': jsonrpc.jsonrpc_version,
                                'id': _id,
                                'result': result,
                            }
                            data = json.dumps(response)
                            client.sendNotify(pack_info.srcUnitId, pack_info.srcUnitClientId, None, _id, 0, settings.SMARTBUS_NOTIFY_TTL, data)
                    except Exception as e:
                        if globalvars.prog_args.verbose:
                            self._logger.exception(
                                'error occurred in handle._callback():\n    request=%s', record)
                        else:
                            self._logger.error(
                                'error occurred in handle._callback():\n    error: %s %s', type(e), e)
                pass  # end of _callback

                def _error_callback(error):
                    try:
                        # Python3.4 issue20980: In multiprocessing.pool,
                        # ExceptionWithTraceback should derive from Exception
                        if not isinstance(error, Exception):
                            error = error.exc
                        if globalvars.prog_args.verbose:
                            self._logger.exception(
                                'error callback:\n    duration=%s\n    request=%s:\n  %s %s',
                                time.time() -
                                begin_time, record, type(error), error
                            )
                        else:
                            self._logger.error(
                                'error callback:\n    %s %s\n    duration=%s\n    request=%s\n  %s %s',
                                type(error), error, time.time() -
                                begin_time, record, type(error), error
                            )
                        if _id:  # 如果有 RPC ID ，就需要返回错误结果
                            if isinstance(error, jsonrpc.Error):  # JSONRPC 异常
                                response = error.to_dict()
                                response['id'] = _id
                            else:  # 其它异常
                                response = {
                                    'jsonrpc': jsonrpc.jsonrpc_version,
                                    'id': _id,
                                    'error': {
                                        'code':-32500,
                                        'message': '{} {}'.format(type(error), error),
                                        'data': None,
                                    }
                                }
                            data = json.dumps(response)
                            client.sendNotify(pack_info.srcUnitId, pack_info.srcUnitClientId, None, _id, 0, settings.SMARTBUS_NOTIFY_TTL, data)
                    except Exception as e:
                        if globalvars.prog_args.verbose:
                            self._logger.exception(
                                'error occurred in handle._error_callback():\n    request=%s', record)
                        else:
                            self._logger.error(
                                'error occurred in handle._error_callback():\n    error=%s', e)
                pass  # end of _error_callback

                if globalvars.prog_args.verbose:
                    self._logger.debug('pool.apply_async(%s, %s, %s)', _method, _args, _kwargs)
                if sys.version_info[0] < 3:
                    self._pool.apply_async(
                        func=partial(_poolfunc, _method),
                        args=(_args, _kwargs),
                        callback=_callback
                    )
                else:
                    self._pool.apply_async(
                        func=partial(_poolfunc, _method),
                        args=(_args, _kwargs),
                        callback=_callback,
                        error_callback=_error_callback
                    )

        except Exception as e:
            if globalvars.prog_args.verbose:
                self._logger.exception(
                    'error occurred in handle():\n    request=%s',
                    record)
            else:
                self._logger.error(
                    'error occurred in handle():\n    error: %s %s',
                    type(e), e)


mod_map_lock = threading.Lock()
mod_map = {}


def _poolfunc(method, args=(), kwds={}):
    '''该函数包装了个子进程池调用动态RPC方法
    
    :param str method: RPC 方法名。该方法对应了 :pack:`methods` 下的可调用对象
    '''
    _logger = logging.getLogger('executor.poolfunc')
    mothods_mod_name = 'methods'
    curr_obj = importlib.import_module(mothods_mod_name)
    loaded_parts = [mothods_mod_name]
    _method_parts = method.split('.')
    with mod_map_lock:
        for part in _method_parts:
            loaded_parts.append(part)
            try:
                curr_obj = getattr(curr_obj, part)
            except AttributeError:
                if inspect.ismodule(curr_obj):
                    curr_obj = importlib.import_module('.'.join(loaded_parts))
                else:
                    raise
    _logger.debug('>>> %s() <%s> args=%s kwds=%s', method, curr_obj, args, kwds)
    result = curr_obj(*args, **kwds)
    _logger.debug('<<< %s() -> ', method, result)
    return result


def _subproc_init(progargs, logging_queue, logging_root_level):
    try:
        logging.root.handlers.clear()
    except AttributeError:
        del logging.root.handlers[:]
    logging.root.addHandler(QueueHandler(logging_queue))
    logging.root.setLevel(logging_root_level)
    logging.info('subprocess initialize')
    globalvars.prog_args = progargs
