# -*- coding: utf-8 -*-
""" File list.

Copyright (c) Karol Będkowski, 2014

This file is part of exifeditor
Licence: GPLv2+
"""

__author__ = u"Karol Będkowski"
__copyright__ = u"Copyright (c) Karol Będkowski, 2014"
__version__ = "2014-11-09"


import logging

_LOG = logging.getLogger(__name__)

from exifeditor.logic import exif


class FileList(object):
    def __init__(self):
        self.reset()

    @property
    def updated(self):
        """ Number of unsaved, changed files """
        return sum(1 for fexif in self._exif.itervalues() if fexif.updated)

    def reset(self):
        self._exif = {}  # filename -> exif object

    def get_exif(self, filename):
        fexif = self._exif.get(filename)
        if not fexif:
            fexif = self._exif[filename] = exif.Image(filename)
        return fexif

    def is_updated(self, filename):
        """ Is given `filename` updated? """
        fexif = self._exif.get(filename)
        return fexif and fexif.updated

    def copy_exif_tag(self, src, files, tags):
        src_exif = self.get_exif(src)
        for filename in files:
            dst_exif = self.get_exif(filename)
            for tag in tags:
                value = src_exif.get_value(tag)
                if value is not None:
                    dst_exif.set_value(tag, value[0])
                else:
                    dst_exif.del_value(tag)

    def save(self):
        for fexif in self._exif.itervalues():
            if fexif.updated:
                fexif.save()
