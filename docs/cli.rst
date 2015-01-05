############
命令行
############

sbusr_cli.py
==============

.. program:: sbusr_cli.py

见 :mod:`sbusr_cli`

在当前终端/命令行窗口中运行

直接运行：

    POSIX（需要权限）::

        ./sbusr_cli.py <option> {run}

    Windows（需要权限与文件关联）::

        sbusr_cli.py <option> {run}               

使用 `Python <https://www.python.org>`_ 运行::

    python sbusr_cli.py <option> {run}

.. option:: run

	启动程序

.. option:: -V, --version

   显示版本信息。

.. option:: -m, --more-detailed-logging

   输出更详细的日志。默认为 ``False`` 。

.. option:: -h, --help

    输出帮助信息
