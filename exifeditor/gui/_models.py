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
import collections

from PyQt4 import QtCore, QtGui

from exifeditor.logic import exif

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
                          for key, val in sorted(exif.load(path))]
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


class ExifTreeNode(object):
    def __init__(self, parent, key, value):
        self.clear()
        self.parent = parent
        self.key = key
        self.value = value

    def __len__(self):
        return len(self.children)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<%s %s; %r>" % (self.__class__.__name__,
                                self.key, self.value) + \
            "\n".join(" - " + repr(child) for child in self.children) + "</>"

    def clear(self):
        self.children = []

    def get_child(self, oid):
        for child in self.children:
            if child.oid == oid:
                return child
        _LOG.error("TreeNode.get_child(oid=%r) not found in %r",
                   oid, self)
        return None

    def child_at_row(self, row):
        """The row-th child of this node."""
        return self.children[row]

    def row(self):
        """The position of this node in the parent's list of children."""
        return self.parent.children.index(self) if self.parent else 0

    def setData(self, _column, _value):
        return False


class ExifGroupTreeNode(ExifTreeNode):
    """ Group node """
    def __init__(self, parent, group):
        super(ExifGroupTreeNode, self).__init__(parent, group, None)


class ExifValueTreeNode(ExifTreeNode):
    """ Group node """
    def __init__(self, parent, key, value):
        display_key = key.split(' ', 1)[1]
        super(ExifValueTreeNode, self).__init__(parent, display_key, value)
        self.exif_key = key
        self.modified = False

    def setData(self, column, value):
        if column == 1 and self.value != value:
            self.value = value
            self.modified = True
            return True
        return False


class ExifTreeModel(QtCore.QAbstractItemModel):
    """ Groups & sources tree model.    """
    def __init__(self, parent=None):
        super(ExifTreeModel, self).__init__(parent)
        self.root = ExifTreeNode(None, 'root', None)
        self.update(None)

    def update(self, path):
        """ Refresh whole tree model from database. """
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.root.clear()
        if path:
            exif_data = collections.defaultdict(dict)
            # group by key prefix
            for key, val in exif.load(path):
                prefix = key.split(' ', 1)[0]
                exif_data[prefix][key] = val
            # create objects
            for key in sorted(exif_data.iterkeys()):
                group = ExifGroupTreeNode(self.root, key)
                group.children = [ExifValueTreeNode(group, ikey, ival)
                                  for ikey, ival
                                  in sorted(exif_data[key].iteritems())]
                self.root.children.append(group)
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def data(self, index, role):
        """Returns the data stored under the given role for the item referred
           to by the index."""
        if not index.isValid():
            return QtCore.QVariant()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            node = self.node_from_index(index)
            if index.column() == 0:
                return QtCore.QVariant(str(node.key))
            return QtCore.QVariant(str(node.value or ""))
        elif role == QtCore.Qt.FontRole:
            node = self.node_from_index(index)
            if isinstance(node, ExifGroupTreeNode):
                font = QtGui.QFont()
                font.setBold(True)
                return font
            # ExifValueTreeNode
            if node.modified:
                font = QtGui.QFont()
                font.setBold(True)
                return font
        return QtCore.QVariant()

    def headerData(self, section, orientation, role):
        """Returns the data for the given role and section in the header
           with the specified orientation."""
        if orientation == QtCore.Qt.Horizontal and \
                role == QtCore.Qt.DisplayRole:
            if section == 0:
                return QtCore.QVariant('Key')
            return QtCore.QVariant('Value')
        return QtCore.QVariant()

    def flags(self, index):
        """Returns the item flags for the given index. """
        if not index.isValid():
            return 0
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.column() == 1 and isinstance(index.internalPointer(),
                                              ExifValueTreeNode):
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def columnCount(self, parent):
        """The number of columns for the children of the given index."""
        return 2

    def rowCount(self, parent):
        """The number of rows of the given index."""
        return len(self.node_from_index(parent))

    def hasChildren(self, index):
        """Finds out if a node has children."""
        if not index.isValid():
            return True
        return len(self.node_from_index(index).children) > 0

    def index(self, row, column, parent):
        """Creates an index in the model for a given node and returns it."""
        branch = self.node_from_index(parent)
        return self.createIndex(row, column, branch.child_at_row(row))

    def node_from_index(self, index):
        """Retrieves the tree node with a given index."""
        if index.isValid():
            return index.internalPointer()
        return self.root

    def parent(self, child):
        """The parent index of a given index."""
        node = self.node_from_index(child)
        if node is None:
            return QtCore.QModelIndex()
        parent = node.parent
        if parent is None or parent == self.root:
            return QtCore.QModelIndex()
        return self.createIndex(parent.row(), 0, parent)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole:
            return False
        if not index.isValid() or index.column() != 1:
            return False

        item = self.node_from_index(index)
        result = item.setData(index.column(), value.toPyObject())

        if result:
            self.dataChanged.emit(index, index)

        return result
