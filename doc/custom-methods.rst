###############
编写自定义 RPC
###############

扩展 methods 包
===============

``sbusr`` 将 ``methods`` 包中的模块视作 RPC 模块，并执行与将来自 IPSC 到的 RPC 请求向对应的可调用对象。

RPC 作者应将扩展模块放在 ``methods`` 包中。

名为 ``a.b`` 的 RPC 方法对应的 ``sbusr`` 函数将是 ``methods.a.b``

自定义 RPC 例子
===============

以下举例说明：

在包的“根”编写RPC函数
------------------------

在 ``methods/__init__.py`` 文件中定义一个名为 ``add()`` 的函数:

.. code::

    def add(a, b):
        return a + b

该函数的完整路径名是 ``methods.add()`` ，当接收到 RPC 请求后，``sbusr`` 会将 RPC 中的 method 名称加上 `methods` 作为要调用的函数。
本例中，IPSC如果要调用 ``add()`` ，其 RPC 的 method 属性就应该是 ``add`` 。这个过程是：

#. IPSC发出RPC请求::

    {"method": "add", "params": [1, 2]}

#. sbusr执行::

    methods.add(1, 2)

#. sbusr返回RPC结果::

    {"result": 3}

在子模块编写RPC函数
---------------------

新建模块文件 ``methods/weather.py`` 文件中定义一个名为 ``sk()`` 的函数，用这个函数来获取某地的当前天气信息:

.. code::

    def sk(code):
        import requests
        return requests.get('http://www.weather.com.cn/data/sk/{0}.html'.format(code)).json()

其过程是：

#. IPSC发出RPC请求::
    
    {"method": "weather.sk", "params": ["101010100"]}

#. sbusr执行::

    methods.weather.sk("101010100")

#. sbusr返回RPC结果::

    {"result": {"weatherinfo":{"city":"北京","cityid":"101010100","temp":"-1","WD":"北风","WS":"1级","SD":"56%","WSE":"1","time":"09:40","isRadar":"1","Radar":"JC_RADAR_AZ9010_JB","njd":"暂无实况","qy":"1027"}}}

使用类方法作为RPC函数
---------------------

类方法也可以作为RPC函数

新建一个模块文件 ``methods/mymodule.py``

.. code::

    class MyClass:

        @classmethod
        def mymethod(cls):
            # codes here ....
            pass

那么， ``methods.mymodule.MyClass.mymethod()`` 所对应的 RPC 方法就是 ``mymodule.MyClass.mymethod()``

其过程是：

#. IPSC发出RPC请求::

    {"method": "mymodule.MyClass.mymethod", "params": []}

#. sbusr执行::
    
    methods.mymodule.MyClass.mymethod()

#. sbusr将方法的返回值作为RPC返回结果

限制与注意事项
==============

自动重加载
----------

配置参数 :data:`settings.RELOAD_INTERVAL` 定义了重加载时间间隔。

如果开启了重加载，开发者可以随时修改、新建自定义RPC模块，待重加载时间间隔到，这些模块会被sbusr自动重新加载。

.. attention::

    如果模块有语法错误，或者在加载时全局代码执行错误，则不会被重加载

.. warning::

    自动重加载使用了 Python标准库的 ``importlib.reload()`` 函数，该特性仅 Python 3.4 及以上版本支持。

并发
-----

配置参数 :data:`settings.EXECUTOR_CONFIG` 的参数 ``pool_model`` 决定了RPC函数的并发模式。

无论是进程池模式、还是线程池模式，RPC作者都必须在函数执行完毕后立即返回。

线程池模式下，应特别注意互斥资源的抢占问题。

全局变量
--------

一旦RPC模块被重加载，该模块的全局变量可能受到影响，具体请参考 https://docs.python.org/3/library/importlib.html#importlib.reload

在进程池模式下，注意每个RPC模块进程的全局变量分属各个进程，不可访问。

在进程池模式下，如果 :data:`settings.EXECUTOR_CONFIG` 的参数 ``pool_maxtasksperchild`` 是一个正整数，则RPC支持次数到达该数值时，进程池将重启子进程，该进程的全局变量、函数都会重新加载，原有的数据将全部丢失。

所以，如果RPC模块需要保留“会话”数据，那么这些数据只能保存在外部（如数据库、文件），而不能保存在内存变量中。


资源释放
---------

在进程池模式下，开发者不要在RPC模块中开启无法释放的资源（如HTTP服务），以便进程池释放资源。

所以，RPC模块只能扮演“客户端”的角色，而不能作为服务器。