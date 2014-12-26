# -*- coding: utf-8 -*-

''' 记录一些全局变量，特别是需要跨进程访问的全局变量
:date: 2013年12月20日

:author: tanbro
'''

prog_args = None
'''命令行参数'''

main_logging_queue = None
'''多进程的全局日志队列'''

main_logging_listener = None
'''多进程的全局日志监听器'''

startuptxt = ''
