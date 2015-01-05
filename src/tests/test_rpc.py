# encoding: utf-8

'''
:date: 2015-01-04

:author: 刘雪彦
'''
from __future__ import absolute_import

import unittest
from unittest.mock import patch, MagicMock

import uuid
import json
import logging
import threading
import time

import jsonrpc
import executor
import globalvars
import settings
import server
import random

logging_fmt = logging.Formatter(fmt='%(asctime)s <%(processName)-10s,%(threadName)-10s> %(levelname)-8s %(name)s - %(message)s')
logging_handler = logging.StreamHandler()
logging_handler.setFormatter(logging_fmt)
del logging.root.handlers[:]
logging.root.handlers.append(logging_handler)
logging.root.setLevel(logging.DEBUG)

class Object: pass


class PackInfo:
    def __init__(self, srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType):
        self.srcUnitId = srcUnitId
        self.srcUnitClientId = srcUnitClientId
        self.srcUnitClientType = srcUnitClientType
        self.dstUnitId = dstUnitId
        self.dstUnitClientId = dstUnitClientId
        self.dstUnitClientType = dstUnitClientType
        

settings.SMARTBUS_CONFIG = {
    "type": "ipc",
    "initialize": {
        "clientid": 19,
        "clienttype": 19
    },
    "instance":  {
        "username": None,
        "password": None,
        "extInfo": None,
    }
}

prog_args = Object
prog_args.more_detailed_logging = True

class TestRpc(unittest.TestCase):

    def setUp(self):
        settings.WEBSERVER_LISTEN = (random.randint(60000, 65535), '127.0.0.1')
        
        def server_thread_rountine():
            self._thread_started_cond.acquire()
            self._thread_started_cond.notify()
            self._thread_started_cond.release()
            with patch('smartbus.ipcclient.Client') as mock_smbipc_cls:
                mock_smbipc_cls.__lib = True
                mock_smbipc_cls.initialize = MagicMock(return_value=True)
                server.startup(prog_args)
        
        self._thread_started_cond = threading.Condition()
        self._thread = threading.Thread(target=server_thread_rountine)
        self._thread.daemon = True
        self._thread_started_cond.acquire()
        self._thread.start()
        self._thread_started_cond.wait()
        self._thread_started_cond.release()
        # sleep awhile to ensure the IOLOOP startup
        time.sleep(1)

    def tearDown(self):
        server.stop()


    def test_echo(self):
        with patch('smartbus.ipcclient.Client') as mock_smbipc_cls:
            smbclt = mock_smbipc_cls.return_value
            smbclt.send = MagicMock()
            #
            id_ = uuid.uuid1().hex
            req = {
                "jsonrpc": jsonrpc.jsonrpc_version,
                "id": id_,
                "method": "echo",
                "params": ["this is a testing text"],
            }
            #
            packinfo_args = 1, 2, 3, 4, 5, 6  # srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType
            pack = PackInfo(*packinfo_args)
            server._smartbus_receive_text(smbclt, pack, json.dumps(req))
            # sleep to wait the result
            time.sleep(0.1)
            # check the result
            call_args = smbclt.sendNotify.call_args[0]
            self.assertEqual(call_args[0], pack.srcUnitId)
            self.assertEqual(call_args[1], pack.srcUnitClientId)
            self.assertEqual(call_args[3], id_)
            res = json.loads(call_args[6])
            self.assertEqual(res["id"], req["id"])
            self.assertEqual(res["result"], req["params"][0])
            
            
    def test_classmethod_1(self):
        with patch('smartbus.ipcclient.Client') as mock_smbipc_cls:
            smbclt = mock_smbipc_cls.return_value
            smbclt.send = MagicMock()
            #
            id_ = uuid.uuid1().hex
            req = {
                "jsonrpc": jsonrpc.jsonrpc_version,
                "id": id_,
                "method": "BuildIn.sum",
                "params": [1, 2, 3],
            }
            #
            packinfo_args = 1, 2, 3, 4, 5, 6  # srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType
            pack = PackInfo(*packinfo_args)
            server._smartbus_receive_text(smbclt, pack, json.dumps(req))
            # sleep to wait the result
            time.sleep(0.1)
            # check the result
            call_args = smbclt.sendNotify.call_args[0]
            self.assertEqual(call_args[0], pack.srcUnitId)
            self.assertEqual(call_args[1], pack.srcUnitClientId)
            self.assertEqual(call_args[3], id_)
            res = json.loads(call_args[6])
            self.assertEqual(res["id"], req["id"])
            self.assertEqual(res["result"], sum(req["params"]))
            
            
    def test_classmethod_2(self):
        with patch('smartbus.ipcclient.Client') as mock_smbipc_cls:
            smbclt = mock_smbipc_cls.return_value
            smbclt.send = MagicMock()
            #
            id_ = uuid.uuid1().hex
            req = {
                "jsonrpc": jsonrpc.jsonrpc_version,
                "id": id_,
                "method": "bar.boo.loo.Loo.dec",
                "params": [42, 23],
            }
            #
            packinfo_args = 1, 2, 3, 4, 5, 6  # srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType
            pack = PackInfo(*packinfo_args)
            server._smartbus_receive_text(smbclt, pack, json.dumps(req))
            # sleep to wait the result
            time.sleep(0.1)
            # check the result
            call_args = smbclt.sendNotify.call_args[0]
            self.assertEqual(call_args[0], pack.srcUnitId)
            self.assertEqual(call_args[1], pack.srcUnitClientId)
            self.assertEqual(call_args[3], id_)
            res = json.loads(call_args[6])
            self.assertEqual(res["id"], req["id"])
            self.assertEqual(res["result"], req["params"][0] - req["params"][1])
            
            
    def test_submodfunc(self):
        with patch('smartbus.ipcclient.Client') as mock_smbipc_cls:
            smbclt = mock_smbipc_cls.return_value
            smbclt.send = MagicMock()
            #
            id_ = uuid.uuid1().hex
            req = {
                "jsonrpc": jsonrpc.jsonrpc_version,
                "id": id_,
                "method": "bar.boo.boo_echo",
                "params": ['boo'],
            }
            #
            packinfo_args = 1, 2, 3, 4, 5, 6  # srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType
            pack = PackInfo(*packinfo_args)
            server._smartbus_receive_text(smbclt, pack, json.dumps(req))
            # sleep to wait the result
            time.sleep(0.1)
            # check the result
            call_args = smbclt.sendNotify.call_args[0]
            self.assertEqual(call_args[0], pack.srcUnitId)
            self.assertEqual(call_args[1], pack.srcUnitClientId)
            self.assertEqual(call_args[3], id_)
            res = json.loads(call_args[6])
            self.assertEqual(res["id"], req["id"])
            self.assertEqual(res["result"], 'boo' + req["params"][0])
            
            
    def test_nonexistfunc1(self):
        with patch('smartbus.ipcclient.Client') as mock_smbipc_cls:
            smbclt = mock_smbipc_cls.return_value
            smbclt.send = MagicMock()
            #
            id_ = uuid.uuid1().hex
            req = {
                "jsonrpc": jsonrpc.jsonrpc_version,
                "id": id_,
                "method": "xxx",
                "params": [],
            }
            #
            packinfo_args = 1, 2, 3, 4, 5, 6  # srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType
            pack = PackInfo(*packinfo_args)
            server._smartbus_receive_text(smbclt, pack, json.dumps(req))
            # sleep to wait the result
            time.sleep(0.1)
            # check the result
            call_args = smbclt.sendNotify.call_args[0]
            self.assertEqual(call_args[0], pack.srcUnitId)
            self.assertEqual(call_args[1], pack.srcUnitClientId)
            self.assertEqual(call_args[3], id_)
            res = json.loads(call_args[6])
            self.assertEqual(res["id"], req["id"])
            print(res)
            self.assertIn('error', res)
            
    def test_nonexistfunc2(self):
        with patch('smartbus.ipcclient.Client') as mock_smbipc_cls:
            smbclt = mock_smbipc_cls.return_value
            smbclt.send = MagicMock()
            #
            id_ = uuid.uuid1().hex
            req = {
                "jsonrpc": jsonrpc.jsonrpc_version,
                "id": id_,
                "method": "BuildIn.abc",
                "params": [],
            }
            #
            packinfo_args = 1, 2, 3, 4, 5, 6  # srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType
            pack = PackInfo(*packinfo_args)
            server._smartbus_receive_text(smbclt, pack, json.dumps(req))
            # sleep to wait the result
            time.sleep(0.1)
            # check the result
            call_args = smbclt.sendNotify.call_args[0]
            self.assertEqual(call_args[0], pack.srcUnitId)
            self.assertEqual(call_args[1], pack.srcUnitClientId)
            self.assertEqual(call_args[3], id_)
            res = json.loads(call_args[6])
            self.assertEqual(res["id"], req["id"])
            print(res)
            self.assertIn('error', res)
            
    def test_wrongparams(self):
        with patch('smartbus.ipcclient.Client') as mock_smbipc_cls:
            smbclt = mock_smbipc_cls.return_value
            smbclt.send = MagicMock()
            #
            id_ = uuid.uuid1().hex
            req = {
                "jsonrpc": jsonrpc.jsonrpc_version,
                "id": id_,
                "method": "echo",
                "params": [1, 2, 3],
            }
            #
            packinfo_args = 1, 2, 3, 4, 5, 6  # srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType
            pack = PackInfo(*packinfo_args)
            server._smartbus_receive_text(smbclt, pack, json.dumps(req))
            # sleep to wait the result
            time.sleep(0.1)
            # check the result
            call_args = smbclt.sendNotify.call_args[0]
            self.assertEqual(call_args[0], pack.srcUnitId)
            self.assertEqual(call_args[1], pack.srcUnitClientId)
            self.assertEqual(call_args[3], id_)
            res = json.loads(call_args[6])
            self.assertEqual(res["id"], req["id"])
            print(res)
            self.assertIn('error', res)
            

#     def test_invokeflow(self):
#         logging.info('begin of test_invokeflow')
#          
#         import http.client
#          
#         with patch('smartbus.ipcclient.Client') as mock_smbipc_cls:
#             smbclt = mock_smbipc_cls.return_value
#             invokeid = random.randint(1, 65536)
# #             smbclt.invokeFlow.return_value = invokeid
#             
#             def invokeFlow(server, process, project, flow, params, *args):
#                 self.assertEqual(server, body['server'])
#                 self.assertEqual(process, body['process'])
#                 self.assertEqual(project, body['project'])
#                 self.assertEqual(flow, body['flow'])
#                 self.assertEqual(params, body['params'])
#                 return invokeid
#              
#             smbclt.invokeFlow = invokeFlow
#             
#             
#             
#             #
#             #
#             body = {'server':0,
#                     'process':0,
#                     'project':'project1',
#                     'flow':'flow1',
#                     'params':[1, 2, 3]
#                     }
#             def http_thread_routine():
#                 http_thread_started_cond.acquire()
#                 http_thread_started_cond.notify()
#                 http_thread_started_cond.release()
#                 hc = http.client.HTTPConnection(settings.WEBSERVER_LISTEN[1], settings.WEBSERVER_LISTEN[0])
#                 hc.connect()
#                 hc.request('POST', '/api/flow', body=json.dumps(body))
#                 hresp = hc.getresponse()
#                 self.assertEqual(hresp.status, 200)
#                 hresp_body = hresp.read()
#                 print(hresp_body)                
#                 http_thread_stopped_cond.acquire()
#                 http_thread_stopped_cond.notify()
#                 http_thread_stopped_cond.release()
#             
#             http_thread_started_cond = threading.Condition()
#             http_thread_stopped_cond = threading.Condition()
#             http_thread = threading.Thread(target=http_thread_routine)
#             http_thread.daemon = True
#             http_thread_started_cond.acquire()
#             http_thread.start()
#             http_thread_started_cond.wait()
#             http_thread_started_cond.release()
#             # #
#             time.sleep(1)
# #             _args = smbclt.invokeFlow.call_args[0]
# #             self.assertEqual(_args[0], body['server'])
# #             self.assertEqual(_args[1], body['process'])
# #             self.assertEqual(_args[2], body['project'])
# #             self.assertEqual(_args[3], body['flow'])
# #             self.assertEqual(_args[4], body['params'])
#             # #
#             packinfo_args = body['server'], 2, 3, 4, 5, 6  # srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType
#             pack = PackInfo(*packinfo_args)
#             server._smartbus_invoke_flow_ack(pack, body['project'], invokeid, 1, 'tesing: OK')
#             # #
#             http_thread_stopped_cond.acquire()
#             http_thread_stopped_cond.wait()
#             http_thread_stopped_cond.release()

            


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
