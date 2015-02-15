#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
sbusr_reset -- 用于 reset sbusr

:author:     刘雪彦 <tanbro@163.com>
:contact:    刘雪彦 <lxy@hesong.net>
:date:       2015-02-11
'''

from __future__ import print_function, unicode_literals

import sys
import os
try:
    from http.client import HTTPConnection
except ImportError:
    from httplib import HTTPConnection

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__updated__ = '2015-02-15'

DEBUG = 0
TESTRUN = 0
PROFILE = 0

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

prog_args = None

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
    program_license = '''sbusr_reset -- use the CLI program to reset sbusr

  Created by Liu Xue Yan on %s.

USAGE
''' % (str(__updated__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument('-V', '--version', action='version', version=program_version_message)

        # Process arguments
        args = parser.parse_args()

        return 0
    except Exception as e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

    perform(args)
    return 0


def perform(args):
    import settings
    port = int(settings.WEBSERVER_LISTEN[0])
    host = str(settings.WEBSERVER_LISTEN[1]).strip()
    if host == "":
        host = "localhost"
    conn = HTTPConnection(host, port)
    conn.request("GET", "/sys/reset")
    res = conn.getresponse()
    data = res.read()
    if res.status == 200:
        print("reset Ok.")
    else:
        print('reset failed:\n {} {}. {}'.format(res.status, res.reason, data), file=sys.stderr)
    conn.close()


if __name__ == "__main__":
    if DEBUG:
        pass
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'sbusr_reset_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
