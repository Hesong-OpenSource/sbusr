#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''sbsur_run 命令行

运行 sbusr 服务程序

:author:     刘雪彦 <lxy@hesong.net>
:copyright:  2013 Hesong Info-Tech. All rights reserved.
:license:    commercial
:contact:    lxy@hesong.net

.. program:: sbusr_run.py

在当前终端/命令行窗口中运行该程序

直接运行：

    POSIX（需要权限）::

        ./sbusr_run.py <option> {run}

    Windows（需要权限与文件关联）::

        sbusr_run.py <option> {run}               

使用 `Python <https://www.python.org>`_ 运行::

    python sbusr_run.py <option> {run}

.. option:: -V, --version

   显示版本信息。

.. option:: -m, --more-detailed-logging

   输出更详细的日志。默认为 ``False`` 。

.. option:: -h, --help

    输出帮助信息
'''

from __future__ import print_function, unicode_literals, absolute_import

import sys
import os
import signal

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2013-12-13'
__updated__ = '2015-01-16'

DEBUG = 0
TESTRUN = 0
PROFILE = 0

import globalvars
import server

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None):  # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_license = '''SmartBus Remote Method Provider for IPSC CTI server.

  Created by lxy@hesong.net on %s.
  Copyright 2014 Hesong(GuangZhou) Info-Tech. All rights reserved.

USAGE
''' % (str(__date__))
    program_runtime_message = '''
runtime:
  executable: {}
  version: {}
  platform: {}
  path:
    {}
'''.format(sys.executable, sys.version, sys.platform, (os.linesep + '    ').join(sys.path))

    globalvars.startuptxt = '''
    {}
    {}
    version : {}
    date    : {}
    update  : {}
    '''.format(program_version_message, program_runtime_message, __version__, __date__, __updated__)

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument("-v", "--verbose", action="store_true", help="output verbose logging text.")

        # Process arguments
        args = parser.parse_args()

        # set INTERRUPT signal handler
        def handle_sigint(signum, frame):
            print('SIGINT handled!')
            server.stop()

        signal.signal(signal.SIGINT, handle_sigint)

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help" + "\n")
        return 2

    # startup server
    print('startup server')
    server.run(args)
    print('program terminated')

    return 0

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-m")
#         sys.argv.append("-v")
#         sys.argv.append("-r")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        print('start in PROFILE mode!')
        import cProfile as profile
        import pstats
        profile_filename = 'start_profile.txt'
        profile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "w")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
