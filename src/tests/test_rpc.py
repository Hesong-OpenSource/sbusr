# -*- coding: utf-8 -*-

'''
:date: 2015-01-04

:author: 刘雪彦 <lxy@hesong.net>
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
prog_args.verbose = True

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
                server.run(prog_args)

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
            smbclt.sendNotify = MagicMock()
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
            smbclt.sendNotify = MagicMock()
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
            smbclt.sendNotify = MagicMock()
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
            smbclt.sendNotify = MagicMock()
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
            smbclt.sendNotify = MagicMock()
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
            smbclt.sendNotify = MagicMock()
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
            smbclt.sendNotify = MagicMock()
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


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
