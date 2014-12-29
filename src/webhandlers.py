# encoding: utf-8
''' Web Request Handlers

:date: 2014-12-29

:author: 刘雪彦
'''

import json
import random

from tornado.web import RequestHandler
from tornado.gen import coroutine
from tornado.concurrent import Future

from jsonrpc import to_str
import globalvars


class FlowInvokeAck:
    def __init__(self, packinfo, project, invokeid, ack, msg):
        self.packinfo = packinfo
        self.project = project
        self.invokeid = invokeid
        self.ack = ack
        self.msg = msg


class FlowInvokeErr:
    def __init__(self, packinfo, project, invokeid, errno):
        self.packinfo = packinfo
        self.project = project
        self.invokeid = invokeid
        self.errno = errno


class FlowHandler(RequestHandler):
    '''POST启动流程
    '''
    
    _invoking_futures = {}

    @coroutine
    def post(self, *args, **kwargs):
        # 获取JSONRPC数据
        data = json.loads(to_str(self.request.body, 'utf-8'))
        server = data.get('server')
        process = int(data.get('process', 0))
        project = str(data['project'])
        flow = str(data['flow'])
        params = data.get('params')
        # 确定用于启动该流程的IPSC
        if server is None:
            ipsc = random.choice(globalvars.ipsc_set)
            server = ipsc[0]
        else:
            server = int(server)
        # 确定用于发送该请求的客户端
        if globalvars.ipc_smartbusclient:
            # 总是优先使用 IPC 客户端
            _sbc = globalvars.ipc_smartbusclient
        else:
            _sbc = random.choice(globalvars.net_smartbusclients)
        self._invoke_id = _sbc.invokeFlow(server, process, project, flow, params, False)
        self._invoking_futures[self._invoke_id] = fut = Future()
        fres = yield fut
        if isinstance(fres, FlowInvokeAck):
            self.finish()
        elif isinstance(fres, FlowInvokeErr):
            self.send_error()
        else:
            self.send_error()

    def on_connection_close(self):
        super().on_connection_close()
        # POP
        fut = self._invoking_futures.pop(self._invoke_id)
        # set to end the future
        fut.set_result()

    @classmethod
    def set_flow_ack(cls, ack: FlowInvokeAck):
        '''设置流程启动执行回执
        
        :param webhandlers.FlowInvokeAck ack: 回执信息
        '''
        # POP
        fut = cls._invoking_futures.pop(ack.invokeid)
        # set to end the future
        fut.set_result(ack)

    @classmethod
    def set_flow_err(cls, err: FlowInvokeErr):
        '''设置流程启动错误
        
        :param webhandlers.FlowInvokeAck err: 错误信息
        '''
        # POP
        fut = cls._invoking_futures.pop(err.invokeid)
        # set to end the future
        fut.set_result(err)
