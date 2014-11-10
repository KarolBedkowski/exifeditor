# -*- coding: utf-8 -*-
""" Exif related functions.

Copyright (c) Karol Będkowski, 2014

This file is part of exifeditor
Licence: GPLv2+
"""

__author__ = u"Karol Będkowski"
__copyright__ = u"Copyright (c) Karol Będkowski, 2014"
__version__ = "2014-11-09"


import exifread


class Image(object):
    """Image file informations """
    def __init__(self, path):
        self.path = path
        self.exif = dict(load(path))

    def save(self):
        pass

    def update_exif(self, values):
        pass



def load(path):
    """ Load exif from `path` """
    with open(path, 'rb') as image:
        exif = exifread.process_file(image)
        for key, val in exif.iteritems():
            if not hasattr(val, 'printable'):
                continue
            val = val.printable.replace('\0', '').replace('\n', '; ').strip()
            val = val.decode('utf-8', errors='replace')
            yield key, val
