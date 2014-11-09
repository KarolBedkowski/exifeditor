# -*- coding: utf-8 -*-
""" Qt models

Copyright (c) Karol Będkowski, 2014

This file is part of mna
Licence: GPLv2+
"""

__author__ = u"Karol Będkowski"
__copyright__ = u"Copyright (c) Karol Będkowski, 2014"
__version__ = "2013-04-28"


import logging
import os.path
import time

from PyQt4 import QtCore, QtGui
import exifread

_LOG = logging.getLogger(__name__)


class ImagesListItem(object):
    def __init__(self, name, size, date):
        self.name = name
        self.size = size
        self.date = date

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<ImagesListItem %r>" % (self.name)


def _is_image(fname):
    ext = os.path.splitext(fname)[1]
    return ext.lower() in ('.jpg', '.png', '.tif', '.nef')


class ImagesListModel(QtCore.QAbstractTableModel):

    _HEADERS = ("Name", "Size", "Date")

    def __init__(self, parent=None):
        super(ImagesListModel, self).__init__(parent)
        self.items = []

    def update(self, path):
        _LOG.debug("ListModel.update(%s)", path)
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        items = ((fname, os.path.join(path, fname))
                 for fname in os.listdir(path))
        images = sorted(fname_fpath
                  for fname_fpath in items
                  if os.path.isfile(fname_fpath[1])
                  and _is_image(fname_fpath[0]))

        self.items = [ImagesListItem(fname,
                                     os.path.getsize(fpath),
                                     os.path.getmtime(fpath))
                      for fname, fpath in images]
        self.emit(QtCore.SIGNAL("layoutChanged()"))


    def rowCount(self, _parent=QtCore.QModelIndex()):
        return len(self.items)

    def columnCount(self, _parent):
        return 3

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and \
                role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self._HEADERS[col])
        return QtCore.QVariant()

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        if role == QtCore.Qt.DisplayRole:
            row = self.items[index.row()]
            col = index.column()
            if col == 0:
                return QtCore.QVariant(row.name)
            elif col == 1:
                return QtCore.QVariant(row.size)
            elif col == 2:
                return QtCore.QVariant(time.strftime("%X %x",
                                                     time.localtime(row.date)))
        return QtCore.QVariant()

    def node_from_index(self, index):
        if index.row() < len(self.items):
            return self.items[index.row()]
        return None


class ExifListItem(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return "<ExifListItem %r=%r>" % (self.key, self.value)


def _load_exif(path):
    with open(path, 'rb') as image:
        exif = exifread.process_file(image)
        for key, val in exif.iteritems():
            if not hasattr(val, 'printable'):
                continue
            val = val.printable.replace('\0', '').replace('\n', '; ') \
                    .strip()
            val = val.decode('utf-8', errors='replace')
            yield key, val


class ExifListModel(QtCore.QAbstractTableModel):

    _HEADERS = ("Key", "Value")

    def __init__(self, parent=None):
        super(ExifListModel, self).__init__(parent)
        self.items = []

    def update(self, path):
        _LOG.debug("ExifListModel.update(%s)", path)
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        if path:
            self.items = [ExifListItem(key, val)
                          for key, val in sorted(_load_exif(path))]
        else:
            self.items = []
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def rowCount(self, _parent=QtCore.QModelIndex()):
        return len(self.items)

    def columnCount(self, _parent):
        return 2

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and \
                role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self._HEADERS[col])
        return QtCore.QVariant()

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        if role == QtCore.Qt.DisplayRole:
            row = self.items[index.row()]
            col = index.column()
            if col == 0:
                return QtCore.QVariant(row.key)
            elif col == 1:
                return QtCore.QVariant(row.value)
        return QtCore.QVariant()

    def node_from_index(self, index):
        if index.row() < len(self.items):
            return self.items[index.row()]
        return None
