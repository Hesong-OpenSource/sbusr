##########
IPSC 集成
##########

``sbusr`` 通过 smartbus 与 IPSC 流程进行通信。

``sbusr`` 提供了两种通信方式：

* 在流程中使用脚本远程调用 ``sbusr`` 中方法
* 通过 HTTP Request 命令 ``sbusr`` 启动流程

*********
RPC 调用
*********

========
基本原理
========

如果要在流程中调用 ``sbusr`` 的方法，需要通过在“脚本节点”中运行脚本实现：

    * 在流程中，通过脚本函数 ``smartbusSendData`` 向 ``sbusr`` 异步发送RPC的请求数据。
    * ``sbusr`` 根据RPC请求执行其内部的某个函数或方法，并将结果通过smartbus返回给流程
    * 流程发送RPC请求后，通过脚本函数 ``SmartbusWaitNotify`` 异步等待等待并收取 ``sbusr`` 返回的执行结果

========
格式定义
========

RPC请求-回复的格式请参考 `JSON-RPC 2.0 specification <www.jsonrpc.org/specification>`_

---------
请求格式
---------

RPC请求一律由流程通过 ``smartbusSendData`` 向 ``sbusr`` 异步发送

调用者应使用该函数的 ``data`` 参数传入RPC请求的JSON字符串。

例如，要将 ``echo()`` RPC请求发送到 ``unitid=19, clientid=1`` 的 ``sbusr`` 实例，应该这样在流程的脚本节点中执行：

.. code::

    smartbusSendData(19, 1, -1, 1, 211, json.dumps({
                "jsonrpc": "2.0",
                "id": "123456",
                "method": "echo",
                "params": ["Hello"]
            })
        )

.. attention:: ``cmdtype`` 参数的值必须是 ``211``

``sbusr`` 收到该请求后，将执行函数：

.. code::

    methods.echo("Hello")

--------
回复格式
--------

流程在发送请求之后，使用异步等待函数 ``SmartbusWaitNotify`` 等待RPC返回。

``sbusr`` 将 RPC的 ``id`` 作为 ``title`` 参数传入，返回结果以JSON格式通过该函数返回。

例如，我们需要接收上例中 ``id`` 为 ``"123456"`` 的RPC执行结果，就在流程的脚本节点中执行：

.. code::

    res = AsynchInvoke(SmartbusWaitNotify("123456", 0, 1000))
    resobj = json.loads(res)
    if 'result' in resobj:
        Trace('返回值是：%s'%(res['result']))
    elif 'error' in resobj:
        TraceErr('返回错误：%s : %s'%(res['error']['code'], res['error']['message']))

.. attention:: 由于IPSC脚本引擎的限制， ``AsynchInvoke`` 所在行不能换行书写！

--------------------
sbusr 自定义脚本
--------------------

为了简化调用步骤，我们提供了封装上述“请求-回复”过程的自定义脚本，请参见 http://github.com/Hesong-OpenSource/sbusr-flow-scripts

*********
启动流程
*********

``sbusr`` 提供一个迷你型的 HTTP 服务器，并在 ``/api/flow`` 这个路径上接受 ``POST`` 请求。调用方可向该HTTP地址发送POST请求启动流程。

=============
流程参数格式
=============

流程启动参数一律使用编码为UTF-8的JSON对象在POST请求的BODY中定义。这个JSON对象的属性有：

:server: 要启动流程的IPSC服务在Smartbus体系中的 ``unitid``

    如果不提供该参数，则 ``sbusr`` 会随机的从它所能连接到的IPSC中选择一个

    :数据类型: Number (非负整数)

:process: 要启动流程的IPSC服务在Smartbus体系中的 ``clientid``

    如果不提供该参数，则 ``sbusr`` 会随机的从它所能连接到的IPSC中选择一个

    :数据类型: Number (非负整数)

:project: 流程所项目的ID

    :数据类型: String

:flow: 流程的ID

    :数据类型: String

:params: 传入流程“子流程开始”节点的参数列表

    :数据类型: Array

举例：

.. code-block:: http

    POST /api/flow HTTP/1.1
    Content-Type: application/json

    {
        "project": "Project1",
        "flow": "Flow1",
        "params": ["Hello", "Flow"]
    }           

收到该请求后， ``sbusr`` 将从它连接到的IPSC实例中随机选择一个，并让该IPSC启动项目ID为“Project1”，流程ID为“Flow1”的流程，流程启动后，其“子项目开始节点”可以接收到两个参数，分别是“Hello”
与“Flow”。

如果流程启动成功， ``sbusr`` 返回 HTTP 200 OK，否则返回错误码。
