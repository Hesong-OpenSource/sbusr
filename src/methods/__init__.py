# -*- coding: utf-8 -*-

'''自定义RPC模块

开发者可在该名称空间下放置所需的远程方法

本模块下的几个函数是简单的远程方法示例
'''

import time
import logging

class BuildIn:
    @classmethod
    def sum(cls, *args):
        return sum(args)



def add(a, b):
    '''加法'''
    return a + b

def echo(txt: str) -> str:
    '''原样返回收到的内容

    :param txt: 字符串
    '''
    return txt


def plus(*args):
    '''求和'''
    return sum(args)


def sleep(seconds: float):
    '''睡眠

    :param seconds: 睡眠时间，时间为秒
    '''
    time.sleep(seconds)


def exception(*args):
    '''抛出异常
    '''
    raise Exception(*args)


def warnlog(msg):
    '''在 Logging 中输出警告信息

    :param str msg: 警告信息
    '''
    logging.warn('%s', msg)
