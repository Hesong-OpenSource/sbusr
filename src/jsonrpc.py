# -*- coding: utf-8 -*-

''' JSON-RPC 常用方法

:date: 2013-12-13
:author: 刘雪彦 <lxy@hesong.net>
'''

__updated__ = '2015-01-15'

import sys
import json
import datetime

PY3K = sys.version_info[0] > 2

if PY3K:
    unicode = str
    long = int
    def to_bytes(s, encoding=sys.getdefaultencoding()):
        if isinstance(s, (bytes, type(None))):
            return s
        elif isinstance(s, str):
            return s.encode(encoding)
        else:
            raise TypeError()
    pass
    def to_unicode(s, encoding=sys.getdefaultencoding()):
        if isinstance(s, (str, type(None))):
            return s
        elif isinstance(s, bytes):
            return s.decode(encoding)
        else:
            raise TypeError()
    pass
    to_str = to_unicode
else:
    def to_bytes(s, encoding=sys.getdefaultencoding()):
        if isinstance(s, (str, type(None))):
            return s
        elif isinstance(s, unicode):
            return s.encode(encoding)
        else:
            raise TypeError()

    def to_unicode(s, encoding=sys.getdefaultencoding()):
        if isinstance(s, (unicode, type(None))):
            return s
        elif isinstance(s, str):
            return s.decode(encoding)
        else:
            raise TypeError()

    to_str = to_bytes


jsonrpc_version = '2.0'


def parse(txt):
    '''解析 JSON RPC

    :param txt: 带解析的 JSON 字符串

    :return: request, result, error
        如果是request，第一个参数返回该请求的dict，格式是：

        .. code-block:: python

            {'id': 'id-of-the-request', 'method': 'your_method', params['what', 'ever', 'params']}

        其它两个参数是 ``None``

        如果是返回结果，第二个参数返回结果 dict，格式是：

        .. code-block:: python

            {'id': 'id-of-the-request', 'result': 'your_result'}

        其它两个参数是 ``None``

    '''
    obj = request = result = error = None
    try:
        obj = json.loads(txt)
    except Exception as e:
        raise FormatError(message='Invalid JSON was received by the server. An error occurred on the server while parsing the JSON text. %s' % (e))
    if not isinstance(obj, dict):
        raise FormatError(message='The JSON sent is not a valid Request object.')
    id_ = obj.get('id')
    if not isinstance(id_, (str, unicode, int, float, type(None))):
        raise FormatError(message='The JSON sent is not a valid Request object. The id is not a String, Number, or NULL value.')
    if ('method' in obj) + ('result' in obj) + ('error' in obj) != 1:
        raise FormatError(id_=id_, message='One of method member, result member and error member must be in the request or response object, and can not be included together.')
    if 'method' in obj:
        method = obj.get('method')
        if not isinstance(method, (str, unicode)):
            raise InvalidRequestError(id_=id_, message='The JSON sent is not a valid Request object. Method is not a String value or does not exists.')
        method = method.strip()
        if not method:
            raise InvalidRequestError(id_=id_, message='The JSON sent is not a valid Request object. Method is an empty String value.')
        obj['method'] = method
        params = obj.get('params')
        args = []
        kwargs = {}
        if params is None:
            pass
        elif isinstance(params, (tuple, list)):
            args = params
        elif isinstance(params, dict):
            kwargs = params
        else:
            raise InvalidParamsError(id_=id_)
        for k in [k for k in obj.keys() if k not in ['jsonrpc', 'id', 'method', 'params']]: obj.pop(k)
        request = obj
        request['args'] = args
        request['kwargs'] = kwargs
    elif 'result' in obj:
        for k in [k for k in obj.keys() if k not in ['jsonrpc', 'id', 'result']]: obj.pop(k)
        result = obj
    elif 'error' in obj:
        err_obj = obj['error']
        if not isinstance(err_obj.get('code'), int):
            raise InvalidErrorError(id_=id_, message='The JSON sent is not a valid Error object. The code MUST be an integer.')
        if not isinstance(err_obj.get('message'), (str, unicode)):
            raise InvalidErrorError(id_=id_, message='The JSON sent is not a valid Error object. The message SHOULD be limited to a concise single sentence.')
        for k in [k for k in err_obj.keys() if k not in ['code', 'message', 'data']]: err_obj.pop(k)
        for k in [k for k in obj.keys() if k not in ['jsonrpc', 'id', 'error']]: obj.pop(k)
        error = obj
    return request, result, error


def recursive_jsonable(obj, encoding='utf-8'):
    '''递归转为可JSON序列化数据类型

    :param obj: 要转化的对象，可以是基本数据类型，或者 dict, list, tuple, date, datetime
    :param encoding: 编码，默认是utf8
    :return: 转换后对象
    '''
    if obj is None:
        return obj
    elif isinstance(obj, (int, long, float, bool)):
        return obj
    elif isinstance(obj, unicode):
        if PY3K:
            return obj
        else:
            return obj.encode(encoding)
    elif isinstance(obj, bytes):
        if PY3K:
            return obj.decode(encoding)
        else:
            return obj
    elif isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, datetime.date):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, datetime.time):
        return obj.strftime('%H:%M:%S')
    elif isinstance(obj, datetime.timedelta):
        raise NotImplementedError()
    elif isinstance(obj, (tuple, list)):
        return [recursive_jsonable(i) for i in obj]
    elif isinstance(obj, dict):
        return dict((recursive_jsonable(k), recursive_jsonable(v)) for (k, v) in obj.items())
    else:
        return str(obj)


class Error(Exception):
    '''
    json rpc 的 Error Response 对象
    '''

    def __init__(self, id_=None, code=None, message=None, data=None):
        '''构造函数

        :param id_: 错误ID
        :type id_: str, int, float
        :param code: 错误码
        :type code: int
        :param message: 错误消息
        :type message: str
        :param data: 错误数据
        :type data: dict, None
        '''
        if not isinstance(id_, (str, unicode, int, float, type(None))):
            raise TypeError('The id attribute of the response object must be str, unicode, int, float or null')
        if code is None:
            code = -32500
        if not isinstance(code, int):
            raise TypeError('The code attribute of the response object must be int')
        if message is None:
            message = 'Unknown application error.'
        if not isinstance(message, (str, unicode)):
            raise TypeError('The message attribute of the response object must be str, unicode')
        super().__init__(self, message)
        self.id = id_
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self):
        '''转为 dict'''
        return {'jsonrpc':jsonrpc_version, 'id':self.id, 'error':{'code':self.code, 'message':self.message, 'data':self.data}}

    def to_json(self):
        '''转为 JSON 字符串'''
        return json.dumps(self.to_dict())

    def __str__(self):
        return '{}.{}(id={}, code={}, message={})'.format(
            self.__class__.__module__, self.__class__.__name__,
            self.id, self.code, self.message
        )

    def __repr__(self):
        return '<{}.{} object at {}. id={}, code={}, message={}>'.format(
            self.__class__.__module__, self.__class__.__name__, hex(id(self)),
            self.id, self.code, self.message
        )

class InvalidRequestError(Error):
    '''无效的JSON-RPC请求'''
    def __init__(self, id_=None, code=-32600, message='The JSON sent is not a valid Request object.', data=None):
        Error.__init__(self, id_=id_, code=code, message=message, data=data)

class InvalidParamsError(Error):
    '''无效的JSON-RPC请求参数'''
    def __init__(self, id_=None, code=-32602, message='Invalid method parameter(s).', data=None):
        Error.__init__(self, id_=id_, code=code, message=message, data=data)

class MethodNotFoundError(Error):
    '''JSON-RPC请求方法未找到'''
    def __init__(self, id_=None, code=-32601, message='The method does not exist / is not available.', data=None):
        Error.__init__(self, id_=id_, code=code, message=message, data=data)

class InvalidResponseError(Error):
    '''无效的JSON-RPC回复'''
    def __init__(self, id_=None, code=-32600, message='The JSON sent is not a valid Response object.', data=None):
        Error.__init__(self, id_=id_, code=code, message=message, data=data)

class InvalidErrorError(Error):
    '''无效的JSON-RPC错误回复'''
    def __init__(self, id_=None, code=-32600, message='The JSON sent is not a valid Error object.', data=None):
        Error.__init__(self, id_=id_, code=code, message=message, data=data)

class FormatError(Error):
    '''JSON-RPC格式错误'''
    def __init__(self, id_=None, code=-32700, message='Invalid JSON was received by the server. An error occurred on the server while parsing the JSON text.', data=None):
        Error.__init__(self, id_=id_, code=code, message=message, data=data)


class RpcTimeoutError(Exception):
    pass
