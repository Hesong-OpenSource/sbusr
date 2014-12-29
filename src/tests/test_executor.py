# encoding: utf-8
'''
:date: 2014-12-29

:author: 刘雪彦
'''

from __future__ import absolute_import

import unittest

import uuid
import json
import logging
import threading

import jsonrpc
import executor
import globalvars


class Object:
    pass


class PackInfo:
    def __init__(self, srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType):
        self.srcUnitId = srcUnitId
        self.srcUnitClientId = srcUnitClientId
        self.srcUnitClientType = srcUnitClientType
        self.dstUnitId = dstUnitId
        self.dstUnitClientId = dstUnitClientId
        self.dstUnitClientType = dstUnitClientType

logging_fmt = logging.Formatter(fmt='%(asctime)s <%(processName)-10s,%(threadName)-10s> %(levelname)-8s %(name)s - %(message)s')
logging_handler = logging.StreamHandler()
logging_handler.setFormatter(logging_fmt)
del logging.root.handlers[:]
logging.root.handlers.append(logging_handler)


class TestProcessPoolExecutor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass


    @classmethod
    def tearDownClass(cls):
        pass
    
    def setUp(self):
        globalvars.prog_args = Object()
        globalvars.prog_args.more_detailed_logging = False
        #
        self.executor = executor.Executor(pool_model='Process')
        self.executor.start()
    
    def tearDown(self):
        self.executor.stop()
    
    
    def test_echo(self):
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
        #
        client = Object()        
        def _send(cmd, cmdType, dstUnitId, dstClientId, dstClientType, data, encoding=None):
            try:
                self.assertEqual(cmdType, executor.CMDTYPE_JSONRPC_RES)
                self.assertEqual(dstUnitId, packinfo_args[0])
                self.assertEqual(dstClientId, packinfo_args[1])
                res = json.loads(data)
                expect_res = {
                    "jsonrpc": jsonrpc.jsonrpc_version,
                    "id": id_,
                    "result": "this is a testing text",
                }
                self.assertDictEqual(res, expect_res)
            finally:
                _cond.acquire()
                _cond.notify()
                _cond.release()
        #
        client.send = _send
        #
        _cond = threading.Condition()
        _cond.acquire()
        self.executor.put(client, pack, json.dumps(req))
        waited = _cond.wait(timeout=1)
        _cond.release()
        if waited is not None:
            self.assertTrue(waited)
        #
        
    def test_sleep(self):
        #
        id_ = uuid.uuid1().hex
        req = {
            "jsonrpc": jsonrpc.jsonrpc_version,
            "id": id_,
            "method": "sleep",
            "params": [1],
        }
        #
        packinfo_args = 1, 2, 3, 4, 5, 6  # srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType
        pack = PackInfo(*packinfo_args)
        #
        client = Object()        
        def _send(cmd, cmdType, dstUnitId, dstClientId, dstClientType, data, encoding=None):
            try:
                self.assertEqual(cmdType, executor.CMDTYPE_JSONRPC_RES)
                self.assertEqual(dstUnitId, packinfo_args[0])
                self.assertEqual(dstClientId, packinfo_args[1])
                res = json.loads(data)
                expect_res = {
                    "jsonrpc": jsonrpc.jsonrpc_version,
                    "id": id_,
                    "result": None,
                }
                self.assertDictEqual(res, expect_res)
            finally:
                _cond.acquire()
                _cond.notify()
                _cond.release()
        #
        client.send = _send
        #
        _cond = threading.Condition()
        _cond.acquire()
        self.executor.put(client, pack, json.dumps(req))
        waited = _cond.wait(timeout=1.5)
        _cond.release()
        if waited is not None:
            self.assertTrue(waited)
        #
        
    def test_sleep_timeout(self):
        #
        id_ = uuid.uuid1().hex
        req = {
            "jsonrpc": jsonrpc.jsonrpc_version,
            "id": id_,
            "method": "sleep",
            "params": [1],
        }
        #
        packinfo_args = 1, 2, 3, 4, 5, 6  # srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType
        pack = PackInfo(*packinfo_args)
        #
        client = Object()        
        def _send(cmd, cmdType, dstUnitId, dstClientId, dstClientType, data, encoding=None):
            try:
                self.assertEqual(cmdType, executor.CMDTYPE_JSONRPC_RES)
                self.assertEqual(dstUnitId, packinfo_args[0])
                self.assertEqual(dstClientId, packinfo_args[1])
                res = json.loads(data)
                expect_res = {
                    "jsonrpc": jsonrpc.jsonrpc_version,
                    "id": id_,
                    "result": None,
                }
                self.assertDictEqual(res, expect_res)
            finally:
                _cond.acquire()
                _cond.notify()
                _cond.release()
        #
        client.send = _send
        #
        _cond = threading.Condition()
        _cond.acquire()
        self.executor.put(client, pack, json.dumps(req))
        waited = _cond.wait(timeout=0.5)
        _cond.release()
        if waited is not None:
            self.assertFalse(waited)
        #
        
    def test_exception(self):
        #
        id_ = uuid.uuid1().hex
        req = {
            "jsonrpc": jsonrpc.jsonrpc_version,
            "id": id_,
            "method": "exception",
            "params": [],
        }
        #
        packinfo_args = 1, 2, 3, 4, 5, 6  # srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType
        pack = PackInfo(*packinfo_args)
        #
        client = Object()        
        def _send(cmd, cmdType, dstUnitId, dstClientId, dstClientType, data, encoding=None):
            try:
                self.assertEqual(cmdType, executor.CMDTYPE_JSONRPC_RES)
                self.assertEqual(dstUnitId, packinfo_args[0])
                self.assertEqual(dstClientId, packinfo_args[1])
                res = json.loads(data)
                self.assertEqual(res['id'], id_)
                self.assertIn('error', res)
                errobj = res['error']
                self.assertIn('code', errobj)
                self.assertIn('message', errobj)
            finally:
                _cond.acquire()
                _cond.notify()
                _cond.release()
        #
        client.send = _send
        #
        _cond = threading.Condition()
        _cond.acquire()
        self.executor.put(client, pack, json.dumps(req))
        waited = _cond.wait(timeout=1)
        _cond.release()
        if waited is not None:
            self.assertTrue(waited)
        #


    def test_nonexists_method(self):
        #
        id_ = uuid.uuid1().hex
        req = {
            "jsonrpc": jsonrpc.jsonrpc_version,
            "id": id_,
            "method": "nonexists",
            "params": [],
        }
        #
        packinfo_args = 1, 2, 3, 4, 5, 6  # srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType
        pack = PackInfo(*packinfo_args)
        #
        client = Object()        
        def _send(cmd, cmdType, dstUnitId, dstClientId, dstClientType, data, encoding=None):
            try:
                self.assertEqual(cmdType, executor.CMDTYPE_JSONRPC_RES)
                self.assertEqual(dstUnitId, packinfo_args[0])
                self.assertEqual(dstClientId, packinfo_args[1])
                res = json.loads(data)
                self.assertEqual(res['id'], id_)
                self.assertIn('error', res)
                errobj = res['error']
                self.assertIn('code', errobj)
                self.assertIn('message', errobj)
            finally:
                _cond.acquire()
                _cond.notify()
                _cond.release()
        #
        client.send = _send
        #
        _cond = threading.Condition()
        _cond.acquire()
        self.executor.put(client, pack, json.dumps(req))
        waited = _cond.wait(timeout=1)
        _cond.release()
        if waited is not None:
            self.assertTrue(waited)
        

    def test_wrong_args(self):
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
        #
        client = Object()        
        def _send(cmd, cmdType, dstUnitId, dstClientId, dstClientType, data, encoding=None):
            try:
                self.assertEqual(cmdType, executor.CMDTYPE_JSONRPC_RES)
                self.assertEqual(dstUnitId, packinfo_args[0])
                self.assertEqual(dstClientId, packinfo_args[1])
                res = json.loads(data)
                self.assertEqual(res['id'], id_)
                self.assertIn('error', res)
                errobj = res['error']
                self.assertIn('code', errobj)
                self.assertIn('message', errobj)
            finally:
                _cond.acquire()
                _cond.notify()
                _cond.release()
        #
        client.send = _send
        #
        _cond = threading.Condition()
        _cond.acquire()
        self.executor.put(client, pack, json.dumps(req))
        waited = _cond.wait(timeout=1)
        _cond.release()
        if waited is not None:
            self.assertTrue(waited)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
