# -*- coding: utf-8 -*-

''' Web Request Handlers

:date: 2014-12-29
:author: 刘雪彦 <lxy@hesong.net>
'''

import json
import time
import random

from tornado import ioloop
from tornado.web import RequestHandler
from tornado.gen import coroutine
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
        self._invoking_futures[self._invoke_id] = self._invoke_future = Future()

        # 超时处理
        def _invoke_timeout():
            self._invoke_timeout = None
            self._invoke_future.set_result(TimeoutError('yield future timeout'))
            self._invoking_futures.pop(self._invoke_id)

        self._invoke_timeout = ioloop.IOLoop.instance().add_timeout(
             time.time() + settings.FLOW_ACK_TIMEOUT,
             _invoke_timeout
        )
        # 开始异步等流程回执
        fres = yield self._invoke_future
        # 流程回执了！
        if self._invoke_timeout:
            ioloop.IOLoop.instance().remove_timeout(self._invoke_timeout)
            self._invoke_timeout = None
        if isinstance(fres, FlowInvokeAck):
            if fres.ack == 1:  # 调用成功！
                self.finish(fres.msg)
            else:  # 调用错误！
                errtxt = 'Flow invoking failed. packinfo={}, project={}, id={}, ack={}, msg={}'\
                    .format(fres.packinfo, fres.project, fres.invokeid, fres.ack, fres.msg)
                raise RuntimeError('{}'.format(errtxt))
        elif isinstance(fres, Exception):
            raise fres
        else:
            raise RuntimeError('Unknown future result {} {}'.format(type(fres), fres))

    def on_connection_close(self):
        super().on_connection_close()
        # set to end the future
        self._invoke_future.set_result()
        # POP
        self._invoking_futures.pop(self._invoke_id)

    @classmethod
    def set_flow_ack(cls, ack: FlowInvokeAck):
        '''设置流程启动执行回执
        
        :param webhandlers.FlowInvokeAck ack: 回执信息
        '''
        _invoke_id = '{:d}:{:d}:{:s}:{:d}'.format(ack.packinfo.srcUnitId, ack.packinfo.srcUnitClientId, ack.project, ack.invokeid)
        # POP
        fut = cls._invoking_futures.pop(_invoke_id)
        # set to end the future
        fut.set_result(ack)

