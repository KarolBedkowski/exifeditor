#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Startup application in debug mode.

Copyright (c) Karol Będkowski, 2013-2014

This file is part of exifeditor
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2014"
__version__ = "2014-11-09"

import sys
if '--profile' not in sys.argv:
    sys.argv.append('-d')


def _profile():
    """ profile app """
    import cProfile
    print 'Profiling....'
    cProfile.run('from exifeditor.main import run; run()', 'profile.tmp')
    import pstats
    import time
    with open('profile_result_%d.txt' % int(time.time()), 'w') as out:
        stat = pstats.Stats('profile.tmp', stream=out)
        stat.sort_stats('cumulative').print_stats('exifeditor', 50)
        out.write('\n\n----------------------------\n\n')
        stat.sort_stats('time').print_stats('exifeditor', 50)
        out.write('\n\n============================\n\n')
        stat.sort_stats('cumulative').print_stats('', 50)
        out.write('\n\n----------------------------\n\n')
        stat.sort_stats('time').print_stats('', 50)


def _memprofile():
    """ mem profile app """
    from exifeditor import main
    main.run()
    import gc
    gc.collect()
    while gc.collect() > 0:
        print 'collect'

    import objgraph
    objgraph.show_most_common_types(20)

    import pdb
    pdb.set_trace()


if __name__ == "__main__":
    if '--profile' in sys.argv:
        sys.argv.remove('--profile')
        _profile()
    elif '--memprofile' in sys.argv:
        sys.argv.remove('--memprofile')
        _memprofile()
    elif '--version' in sys.argv:
        from exifeditor import version
        print version.INFO
    else:
        from exifeditor.main import run
        run()
