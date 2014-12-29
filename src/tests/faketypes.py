# encoding: utf-8
'''
:date: 2014-12-29

:author: 刘雪彦
'''

class FakePackInfo:
    def __init__(self, srcUnitId, srcUnitClientId, srcUnitClientType, dstUnitId, dstUnitClientId, dstUnitClientType):
        self.srcUnitId = srcUnitId
        self.srcUnitClientId = srcUnitClientId
        self.srcUnitClientType = srcUnitClientType
        self.dstUnitId = dstUnitId
        self.dstUnitClientId = dstUnitClientId
        self.dstUnitClientType = dstUnitClientType


class FakeSbClient:
    def __init__(self):
        pass
    
    def send(self, cmd, cmdType, dstUnitId, dstClientId, dstClientType, data, encoding=None):
        pass
