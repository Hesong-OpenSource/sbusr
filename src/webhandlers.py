# -*- coding: utf-8 -*-

''' Web Request Handlers

:date: 2014-12-29
:author: 刘雪彦 <lxy@hesong.net>
'''

__updated__ = '2015-01-15'

import json
import time
import random
import logging
import threading

from tornado import ioloop
from tornado.web import RequestHandler
from tornado.gen import coroutine, with_timeout, Task
from tornado.concurrent import Future

from jsonrpc import to_str
import globalvars
import settings


class FlowInvokeAck:
    def __init__(self, packinfo, project, invokeid, ack, msg):
        self.packinfo = packinfo
        self.project = project
        self.invokeid = invokeid
        self.ack = ack
        self.msg = msg


class FlowHandler(RequestHandler):
    '''POST启动流程
    '''

    _invoking_futures = {}

    @coroutine
    def post(self, *args, **kwargs):
        try:
            # 获取JSONRPC数据
            data = json.loads(to_str(self.request.body, 'utf-8'))
            server = data.get('server')
            process = data.get('process')
            project = str(data['project'])
            flow = str(data['flow'])
            params = data.get('params')
            # 确定用于启动该流程的IPSC
            if (server is None) and (process is None):
                server, process = random.sample(globalvars.ipsc_set, 1)[0]
            elif (server is not None) and (process is None):
                _lst = []
                server = int(server)
                for ipsc in globalvars.ipsc_set:
                    if ipsc[0] == server:
                        _lst.append(ipsc)
                server, process = random.choice(_lst)
            elif (server is None) and (process is not None):
                _lst = []
                process = int(process)
                for ipsc in globalvars.ipsc_set:
                    if ipsc[1] == process:
                        _lst.append(ipsc)
                server, process = random.choice(_lst)
            else:
                server = int(server)
                process = int(process)
            #
            # 确定用于发送该请求的客户端
            if globalvars.ipc_smartbusclient:
                # 总是优先使用 IPC 客户端
                _sbc = globalvars.ipc_smartbusclient
            else:
                _sbc = random.choice(globalvars.net_smartbusclients)
            ret = _sbc.invokeFlow(server, process, project, flow, params, False)
            self._invoke_id = '{:d}:{:d}:{:s}:{:d}'.format(server, process, project, ret)
            #
            self._invoking_futures[self._invoke_id] = self._invoke_future = with_timeout(time.time() + settings.FLOW_ACK_TIMEOUT, Future())
            # 开始异步等流程回执
            fres = yield self._invoke_future
            # 流程回执了
            if isinstance(fres, FlowInvokeAck):
                if fres.ack == 1:  # 调用成功！
                    self.finish(fres.msg)
                else:  # 调用错误！
                    errtxt = 'Flow invoking error response. packinfo={}, project={}, id={}, ack={}, msg={}'\
                        .format(fres.packinfo, fres.project, fres.invokeid, fres.ack, fres.msg)
                    logging.getLogger(self.__class__.__name__).error(errtxt)
                    raise RuntimeError('{}'.format(errtxt))
            elif isinstance(fres, Exception):
                logging.getLogger(self.__class__.__name__).error('yiled result of flow-invoke-ack error: %s %s', type(fres), fres)
                raise fres
            else:
                errtxt = 'Unknown future result {} {}'.format(type(fres), fres)
                logging.getLogger(self.__class__.__name__).error(errtxt)
                raise RuntimeError(errtxt)
        except:
            logging.getLogger(self.__class__.__name__).exception('post')
            raise

    def on_connection_close(self):
        super().on_connection_close()
        # set to end the future
        self._invoke_future.set_result()
        # POP
        self._invoking_futures.pop(self._invoke_id)

    @classmethod
    def set_flow_ack(cls, ack):
        '''设置流程启动执行回执

        :param webhandlers.FlowInvokeAck ack: 回执信息
        '''

        # 该方法从IOLoop之外被调用，所以需要将执行体加入到IOLoop的回调
        def callback():
            _invoke_id = '{:d}:{:d}:{:s}:{:d}'.format(ack.packinfo.srcUnitId, ack.packinfo.srcUnitClientId, ack.project, ack.invokeid)
            # POP
            fut = cls._invoking_futures.pop(_invoke_id)
            # end the future
            fut.set_result(ack)

        ioloop.IOLoop.instance().add_callback(callback)


class ResetHandler(RequestHandler):

    @coroutine
    def get(self):
        logging.getLogger(self.__class__.__name__).warn('ResetHandler!')
        try:
            yield Task(self.reset_executor)
            self.set_header('Content-Type', 'text/plain')
            self.finish('reset succeed')
        except:
            logging.getLogger(self.__class__.__name__).exception('get')
            raise

    @coroutine
    def reset_executor(self):

        def thread_func():
            try:
                logging.getLogger(self.__class__.__name__).warn('globalvars.executor.stop() >>>')
                globalvars.executor.stop()
                logging.getLogger(self.__class__.__name__).warn('globalvars.executor.stop() <<<')
                logging.getLogger(self.__class__.__name__).warn('globalvars.executor.start() >>>')
                globalvars.executor.start()
                logging.getLogger(self.__class__.__name__).warn('globalvars.executor.start() <<<')
                ioloop.IOLoop.instance().add_callback(lambda: f.set_result(True))
            except Exception as exc:
                logging.getLogger(self.__class__.__name__).exception('reset_executor thread_func')
                ioloop.IOLoop.instance().add_callback(lambda: f.set_exception(exc))
                raise

        try:
            f = Future()
            t = threading.Thread(target=thread_func)
            t.setDaemon(True)
            t.start()
            yield f
        except:
            logging.getLogger(self.__class__.__name__).exception('reset_executor')
            raise
