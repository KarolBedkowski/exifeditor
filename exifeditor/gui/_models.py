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
import textwrap

from PyQt4 import QtCore, QtGui


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


class ExifTreeNode(object):
    def __init__(self, parent, image, key, label):
        self.children = []
        self.parent = parent
        self.image = image
        self.key = key
        self.label = label
        self.value = None
        self.tooltip = QtCore.QVariant(key)

    def __len__(self):
        return len(self.children)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<%s %s; %r; clen=%d>" % (self.__class__.__name__,
                                self.key, self.label, len(self))

    def get_tooltip(self):
        return self.tooltip

    def clear(self):
        for child in self.children:
            child.clear()
        self.children = []

    def child_at_row(self, row):
        """The row-th child of this node."""
        if row < 0 or row >= len(self.children):
            return None
        return self.children[row]

    def row(self):
        """The position of this node in the parent's list of children."""
        return self.parent.children.index(self) if self.parent else 0

    def setData(self, _column, _value):
        return False


class ExifGroupTreeNode(ExifTreeNode):
    """ Group node """
    pass


class ExifValueTreeNode(ExifTreeNode):
    """ Group node """
    def __init__(self, parent, image, key):
        super(ExifValueTreeNode, self).__init__(parent, image, key, None)
        self.modified = False
        self.exif_val = None
        self.label = image.get_tag_label(key)
        self.tooltip = None
        self.update()

    def get_tooltip(self):
        if not self.tooltip:
            self.tooltip = self.key + '\n' + \
                    textwrap.fill(self.image.get_tag_descr(self.key), 100)
        return self.tooltip

    def update(self):
        self.exif_val, self.value = self.image.get_value(self.key)

    def setData(self, column, value):
        value = unicode(value)
        if column == 1 and self.value != value:
            if self.image.set_value(self.key, value):
                self.modified = True
                self.update()
                return True
        return False


class ExifTreeModel(QtCore.QAbstractItemModel):
    """ Groups & sources tree model.    """
    def __init__(self, parent=None):
        super(ExifTreeModel, self).__init__(parent)
        self.root = ExifTreeNode(None, None, 'root', None)
        self.update(None)

    def update(self, image):
        """ Refresh whole tree model from database. """
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.root.clear()
        if image:
            for tag, tag_label in image.get_groups():
                group = ExifGroupTreeNode(self.root, image, tag, tag_label)
                group.children = [ExifValueTreeNode(group, image, itag)
                                for itag
                                in sorted(image.get_tags_by_group(tag))]
                self.root.children.append(group)
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def data(self, index, role):
        """Returns the data stored under the given role for the item referred
           to by the index."""
        if not index.isValid():
            pass
        elif role == QtCore.Qt.DisplayRole:
            node = self.node_from_index(index)
            return QtCore.QVariant((node.value if index.column() == 1
                                    else node.label) or "")
        elif role == QtCore.Qt.EditRole:
            if index.column() == 1:
                node = self.node_from_index(index)
                return QtCore.QVariant(node.exif_val or "")
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
        elif role == QtCore.Qt.ToolTipRole:
            return self.node_from_index(index).get_tooltip()

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
