###########
自动重加载
###########

``sbusr`` 的 :mod:`methods` 包可以重新加载。重加载特性使得动态修改自定义RPC成为可能。


以下几种方式可以实现 ``sbusr`` 的 :mod:`methods` 包重加载：

* 向 ``sbusr`` 发送重加载命令
* ``sbusr`` 子进程执行任务数到达最大值后自动重加载
* 杀死子进程后，父进程自动重启子进程达到重加载的目的

.. attention::
    
    无论哪种方式， ``sbusr`` 都是通过重启子进程来完成 :mod:`methods` 包的重加载的。

设置子进程最大任务数
====================

如果设置了 :data:`settings.EXECUTOR_CONFIG` 的 ``pool_maxtasksperchild`` 属性为正整数，执行RPC的子进程会在该属性定义的最大执行次数后重启。此时， ``methods`` 模块上也会因重启而被重加载。

发送重加载命令
==============

``sbusr`` 通过其内置 Web 服务器接收重加载命令。

重启命令是发送到 ``http://host[:port]/sys/reset`` 的 HTTP GET 请求。可使用任何 HTTP 客户端来发送该命令，如：

.. code-block:: sh

    curl http://localhost:8080/sys/reset


.. note::

    Web 服务器的监听端口通过变量 :data:`settings.WEBSERVER_LISTEN` 设置

杀死子进程
===========

杀死子进程后，父进程自动重启子进程达到重加载的目的。

在 ``sbusr`` 运行期间，输入 ``ctrl-c`` 可杀死子进程。
