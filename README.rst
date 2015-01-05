########
自述
########

CI 状态
#######

`master` :

  .. image:: https://travis-ci.org/Hesong-OpenSource/sbusr.svg?branch=master
      :target: https://travis-ci.org/Hesong-OpenSource/sbusr

`develop` :
	.. image:: https://travis-ci.org/Hesong-OpenSource/sbusr.svg?branch=develop
	    :target: https://travis-ci.org/Hesong-OpenSource/sbusr

介绍
######

``sbusr`` 读作 ``s-bus-ser`` (IPA: ``sbʌsə``)，是 `和声 <http://www.hesong.net>`_ IPSC 的远程方法提供程序。

``sbusr`` 使用 IPSC 的 smartbus 与之进行通信，为其提供可扩展的 `JSON PRC <www.jsonrpc.org/specification>`_ 远程方法，以实现诸如执行SQL语句、存储过程，进行 WebService 访问等在流程中难以实现的功能。

开发者可自行编写 ``sbusr`` 的 RPC 方法，为 IPSC 提供各种不同的扩展功能。

IPSC 流程需要特殊的节点或者自定义函数，通过SmartBus以及相应的插件访问 ``sbusr`` 。

代码库
#######

http://github.com/Hesong-OpenSource/sbusr

文档
#####

http://hesong-ipsc-sbusr.readthedocs.org/

如何运行 sbusr
#################

1 准备运行环境
*****************

1.1 支持的操作系统
===================

* Linux
* Windows

1.2 安装 Python
=================

``sbusr`` 使用 `Python <https://www.python.org>`_ 语言实现的，因此我们首先需要安装 ``Python``。
如果您的操作系统已经配备了版本足够高的 ``Python`` ，请忽略本步骤。

访问 https://www.python.org/downloads/ 下载并安装合适的版本。建议使用最新的 Python3 发布版。

由于我们在接下来的步骤中，需要使用 `PyPI <https://pypi.python.org/pypi>`_ 包管理器安装 ``sbusr`` 所依赖的第三方包，所以在安装Python之后，请安装支持 `PyPI <https://pypi.python.org/pypi>`_ 的包管理器。推荐使用 `pip <https://pypi.python.org/pypi/pip>`_ 。

Python3.4以及以上版本已经在标准库中包含了 ``pip`` ，不用另行安装。

``sbusr`` 在 python3.4+ 下可以成功运行。

应该可以在 Python2.7+，以及 Python3.x 环境下运行，不过未经测试。

据信可以在 PyPy/Jython/IronPython 下运行，不过未经测试。

1.3 安装Python虚拟环境
======================

这是一个可选步骤。

本文中，我们倾向于在一个Python虚拟环境中安装该程序的依赖包。如果您希望将该程序的依赖包安装到系统全局的Python包集合中，可忽略该步骤。

Python3.4 以及以上版本已经在标准库中包含了虚拟环境 `venv <https://docs.python.org/3/library/venv.html>`_ ，低版本的 Python 则需要另行安装 `virtualenv <https://pypi.python.org/pypi/virtualenv>`_ 。如果已经配置好了 ``pip`` ，可使用以下命名安装 ``virtualenv`` ::

    pip install virtualenv

2 获取源代码
*************

可通过以下途径获取源代码：

2.1.1 GIT 克隆
==================
可访问GIT仓库直接克隆代码库::

    git clone git@github.com:Hesong-OpenSource/sbusr.git

2.1.2 直接使用项目代码
======================

访问 https://github.com/Hesong-OpenSource/sbusr ，从页面下载所需要的版本

也可联系作者索取项目代码

2.2 修改目录结构
=================

下载之后，将源代码放在一个新建的目录，如 ``/your/dir/sbusr``
该项目的目录结构是::

    sbusr\┐
          └ src\┐
                ├ methods\
                ├ xxx.py
                ├ xxx.py
                ├ xxx.py
                └ ...py

将 ``src`` 目录中的所有文件移动到项目的根目录中，使得该项目的目录结构变为::

    sbusr\┐
          ├ methods\
          ├ xxx.py
          ├ xxx.py
          ├ xxx.py
          └ ...py    

3 安装依赖包
*************

我们建议在 Python 虚拟环境中安装依赖包。如果您准备将本项目的依赖包安装到系统全局的Python包集合，忽略本节中有关虚拟环境的步骤。

首先，在命令行中进入项目所在目录::

    cd /your/dir/sbusr

如果准备将本项目的依赖包安装到 **虚拟环境** 中，请首先建立一个名为 ``_env`` 虚拟环境目录（该目录名称可任意指定）：

    Python3.4以及以上版本执行::

        python -m venv _env

    否则执行::

        virtualenv _env

然后进入虚拟环境：

    POSIX 下执行::

        source _env/bin/activate

    Windows 下执行::

        _env/Scripts/activate

现在，可以使用 ``pip`` 安装所有的依赖包::

    python -m pip install -r requirments.txt

.. hint::
  
  本程序除 Python stdlib 外唯一的依赖包是 `smartbus-client-python <https://pypi.python.org/pypi/smartbus-client-python>`_ 。
  可访问其主页，获取下载与安装方法。

  .. attention::

    `smartbus-client-python <https://pypi.python.org/pypi/smartbus-client-python>`_  在安装之后，还需要相应的C语言共享/动态文件，请仔细阅读 `smartbus-client-python api doc <https://readthedocs.org/projects/smartbus-client-python>`_ 。

    smartbus客户端的共享/动态文件可以在 https://github.com/Hesong-OpenSource/smartbus-client-sdk 下载。

.. attention::

    由第三方提供的各个 RPC 模块可能有各自不同的包依赖。
    如：提供 HTTP Restful API 访问的 RPC 模块可能依赖于 `requests <https://pypi.python.org/pypi/requests>`_ ；
    提供 MySQL 访问的 RPC 模块可能依赖于 `mysql-connector-python <dev.mysql.com/doc/connector-python/en/>`_ 。
    请酌情处理。

4 启动程序
**************

执行::

    python run_sbusr.py

启动这个程序

执行::

    python run_sbusr.py --help

查看其具体的命令行参数
