# encoding: utf-8
''' Web Request Handlers

:date: 2014-12-29

:author: 刘雪彦
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
        #        
        self._invoking_futures[self._invoke_id] = fut = Future()
        
        # 超时处理
        def _invoke_timeout():
            _fut = self._invoking_futures.pop(self._invoke_id)
            _fut.set_result(TimeoutError('yield future timeout'))
        
        ioloop.IOLoop.instance().add_timeout(
             time.time() + settings.FLOW_ACK_TIMEOUT,
             _invoke_timeout
        )
        # 开始异步等流程回执
        fres = yield fut
        # 流程回执了！
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

