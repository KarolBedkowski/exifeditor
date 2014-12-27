# -*- coding: utf-8 -*-
""" Main module.

Copyright (c) Karol Będkowski, 2014

This file is part of exifeditor
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2014"
__version__ = "2014-06-14"

import sys
import optparse
import logging

_LOG = logging.getLogger(__name__)


from exifeditor import version


def _parse_opt():
    """ Parse cli options. """
    optp = optparse.OptionParser(usage="%prog [options] [startup dir]",
                                 version=version.NAME + version.VERSION,
                                 description="Simple exif editor")
    group = optparse.OptionGroup(optp, "Debug options")
    group.add_option("--debug", "-d", action="store_true", default=False,
                     help="enable debug messages")
    group.add_option("--debug-qt", action="store_true", default=False,
                     help="enable debug messages in PyQt4 namespace")
    group.add_option("--shell", action="store_true", default=False,
                     help="start shell")
    optp.add_option_group(group)
    return optp.parse_args()


def run():
    """ Run application. """
    # parse options
    options, args = _parse_opt()

    # logowanie
    from exifeditor.lib.logging_setup import logging_setup
    logging_setup("exifeditor.log", options.debug)
    logging.getLogger('PyQt4').setLevel(logging.DEBUG if options.debug_qt
                                        else logging.WARN)

    # app config
    from exifeditor.lib import appconfig
    config = appconfig.AppConfig("exifeditor.cfg", "exifeditor")
    config.load_defaults(config.get_data_file("defaults.cfg"))
    config.load()
    config.debug = options.debug

    # locale
    from exifeditor.lib import locales
    locales.setup_locale(config)

    if options.shell:
        # starting interactive shell
        from IPython.terminal import ipapp
        app = ipapp.TerminalIPythonApp.instance()
        app.initialize(argv=[])
        app.start()
        return

    from PyQt4 import QtGui
    app = QtGui.QApplication(sys.argv)

    from exifeditor.gui import main_wnd

    window = main_wnd.MainWnd(args)
    window.show()
    app.exec_()

    config.save()
