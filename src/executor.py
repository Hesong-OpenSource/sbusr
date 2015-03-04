# -*- coding: utf-8 -*-

''' 该模块定义了 RPC 任务执行器

服务器模块 :mod:`server` 将来自 smartbus 的请求传递给执行器类 :class:`Executor` 的实例，
执行器解析请求的 JSON RPC 格式，并分配执行体，在线程池中执行，
然后返回结果。

:date: 2013-12-14
:author: 刘雪彦 <lxy@hesong.net>
'''

from __future__ import print_function, unicode_literals, absolute_import

__updated__ = '2015-03-04'

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
        if globalvars.prog_args.verbose:
            self._logger.debug('put() >>>. qsize=%s\n    client=%s\n    pack_info=%s\n    txt=%s', self.queue.qsize(), client, pack_info, txt)
        try:
            recv_time = time.time()
            _id = None
            # 解析 JSON RPC
            req, _, _ = jsonrpc.parse(txt)
            if req:
                _id = req.get('id')
                _method = req['method']
                _args = req['args']
                _kwargs = req['kwargs']
                self.queue.put_nowait((recv_time, client, pack_info, _id, _method, _args, _kwargs))
        except Exception as e:
            if globalvars.prog_args.verbose:
                self._logger.exception('put')
            else:
                self._logger.error('put() error: %s %s', type(e), e)
            if isinstance(e, jsonrpc.Error):  # 处理 jsonrpc.Error 异常
                _id = e.id
                res = e.to_dict()
            else:  # 处理其它异常
                res = {
                    'jsonrpc': jsonrpc.jsonrpc_version,
                    'error': {
                        'code':-32500,
                        'message': '{} {}'.format(type(e), e),
                        'data': None,
                    }
                }
                if _id:
                    res['id'] = _id
            if _id:
                data = json.dumps(res)
                client.sendNotify(pack_info.srcUnitId, pack_info.srcUnitClientId, None, _id, 0, settings.SMARTBUS_NOTIFY_TTL, data)
            # 重新抛出异常
            raise

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
        try:
            begin_time, client, pack_info, _id, _method, _args, _kwargs = record
            if globalvars.prog_args.verbose:
                self._logger.debug('handled: qsize=%s. [%s] %s %s %s', self.queue.qsize(), _id, _method, _args, _kwargs)
            else:
                self._logger.debug('handled: [%s] %s', _id, _method)

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
                            '[%s]: call back:\n    result=%s %s\n    duration=%s\n    request=%s\n    qsize=%s',
                            _id, type(result), result, time.time() - begin_time, record,
                            self.queue.qsize()
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
                            '[%s]: error occurred in handle._callback():\n    request=%s', _id, record)
                    else:
                        self._logger.error(
                            '[%s]: error occurred in handle._callback():\n    error: %s %s', _id, type(e), e)
            pass  # end of _callback

            def _error_callback(error):
                try:
                    # Python3.4 issue20980: In multiprocessing.pool,
                    # ExceptionWithTraceback should derive from Exception
                    if not isinstance(error, Exception):
                        error = error.exc
                    self._logger.error(
                        '[%s]: error callback:\n    %s %s\n    duration=%s\n    request=%s\n  %s %s\n    qsize=%s',
                        _id, type(error), error, time.time() - begin_time, record, type(error), error,
                        self.queue.qsize()
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
                            '[%s]: error occurred in handle._error_callback():\n    request=%s', _id, record)
                    else:
                        self._logger.error(
                            '[%s]: error occurred in handle._error_callback():\n    error=%s', _id, e)
                    raise
            pass  # end of _error_callback

            if globalvars.prog_args.verbose:
                self._logger.debug('handle: [%s] pool.apply_async(%s, %s, %s)', _id, _method, _args, _kwargs)
            if sys.version_info[0] < 3:
                self._pool.apply_async(
                    func=partial(_poolfunc, _id, _method, time.time()),
                    args=(_args, _kwargs),
                    callback=_callback
                )
            else:
                self._pool.apply_async(
                    func=partial(_poolfunc, _id, _method, time.time()),
                    args=(_args, _kwargs),
                    callback=_callback,
                    error_callback=_error_callback
                )
            if globalvars.prog_args.verbose:
                self._logger.debug('handle [%s] pool.apply_async OK. qsize=%s', _id, self.queue.qsize())

        except Exception as e:
            if globalvars.prog_args.verbose:
                self._logger.exception(
                    'error occurred in handle():\n    request=%s', record)
            else:
                self._logger.error(
                    'handle:\n    error: %s %s',
                    type(e), e)


def _poolfunc(id_, method, apply_time, args=(), kwds={}):
    '''该函数包装了个子进程池调用动态RPC方法
    
    :param id_: RPC的ID，仅仅用于日志记录
    :int apply_time: 任务加入队列的时间，由 ``time.time()`` 生成
    :param str method: RPC 方法名。该方法对应了 :pack:`methods` 下的可调用对象
    
    .. warning:: 该方法在子进程中执行！
    '''
    _logger = logging.getLogger('executor.poolfunc')
    _logger.debug('>>> [%s]: %s(). applying duration=%s', id_, method, time.time() - apply_time)
    try:
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
        if globalvars.prog_args.verbose:
            _logger.debug('>>> [%s]: %s() %s args=%s kwds=%s', id_, method, curr_obj, args, kwds)
        result = curr_obj(*args, **kwds)
        if globalvars.prog_args.verbose:
            _logger.debug('<<< [%s]: %s() -> %s', id_, method, result)
        return result
    except Exception as exc:
        if globalvars.prog_args.verbose:
            _logger.exception('[%s]: %s() %s args=%s kwds=%s', id_, method, curr_obj, args, kwds)
        else:
            _logger.error('[%s]: exception occurred in method(): %s %s', id_, type(exc), exc)
        raise
    _logger.debug('<<< [%s]: %s()', id_, method)


def _subproc_init(progargs, logging_queue, logging_root_level):
    try:
        logging.root.handlers.clear()
    except AttributeError:
        del logging.root.handlers[:]
    logging.root.addHandler(QueueHandler(logging_queue))
    logging.root.setLevel(logging_root_level)
    logging.info('subprocess initialize')
    globalvars.prog_args = progargs


mod_map_lock = threading.Lock()

