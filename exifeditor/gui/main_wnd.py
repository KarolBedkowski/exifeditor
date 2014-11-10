# -*- coding: utf-8 -*-
""" Main application window.

Copyright (c) Karol Będkowski, 2014

This file is part of exifeditor
Licence: GPLv2+
"""

__author__ = u"Karol Będkowski"
__copyright__ = u"Copyright (c) Karol Będkowski, 2014"
__version__ = "2013-04-28"

import gettext
import logging
import os.path

from PyQt4 import QtGui, uic, QtCore

from exifeditor.gui import _models
from exifeditor.gui import _resources_rc
from exifeditor.lib.appconfig import AppConfig
from exifeditor.logic import exif

_ = gettext.gettext
_LOG = logging.getLogger(__name__)

assert _resources_rc


class MainWnd(QtGui.QMainWindow):
    """ Main Window class. """

    def __init__(self, _parent=None):
        super(MainWnd, self).__init__()
        self._appconfig = AppConfig()
        uic.loadUi(self._appconfig.get_data_file("main.ui"), self)

        self._current_path = None
        self._current_image = None

        # setup dirs tree
        self._tv_dirs_model = model = QtGui.QFileSystemModel()
        model.setRootPath(QtCore.QDir.rootPath())
        model.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)
        self.tv_dirs.setModel(model)
        self.tv_dirs.setRootIndex(model.index(QtCore.QDir.homePath()))

        # setup files list
        self._lv_files_model = model = _models.ImagesListModel()
        self.lv_files.setModel(model)

        # exif list
        self._tv_info_model = _models.ExifTreeModel()
        self.tv_info.setModel(self._tv_info_model)

        self._bind()

    def _bind(self):
        self.tv_dirs.clicked.connect(self._on_tv_dirs_activated)
        self.b_save.pressed.connect(self._on_save_pressed)
        # file list model
        sel_model = self.lv_files.selectionModel()
        sel_model.currentChanged.connect(self._on_lv_files_selection)
#        sel_model.selectionChanged.connect(self._on_lv_files_selection)

    def _on_tv_dirs_activated(self, index):
        node = self._tv_dirs_model.filePath(index)
        self._current_path = str(node)
        self.lv_files.clearSelection()
        self._lv_files_model.update(str(node))
        self._show_image(None)

    def _on_lv_files_selection(self, _index):
        if not self._current_path:
            return
        index = self.lv_files.selectionModel().currentIndex()
        if index >= 0:
            item = self._lv_files_model.node_from_index(index)
            if item:
                self._show_image(os.path.join(self._current_path,
                                              str(item.name)))
                return
        self._show_image(None)

    def _on_save_pressed(self):
        if not self._current_image:
            return
        if self._current_image.save():
            self._show_image(self._current_image.path)

    def _show_image(self, path):
        self.tv_info.reset()
        if path:
            self._current_image = exif.Image(path)
            image = QtGui.QImage(path)
            image = image.scaled(self.g_view.size(), QtCore.Qt.KeepAspectRatio)
            self.g_view.setPixmap(QtGui.QPixmap.fromImage(image))
            self._tv_info_model.update(self._current_image)
        else:
            self._current_image = None
            self.g_view.setPixmap(QtGui.QPixmap())
            self._tv_info_model.update(None)
#        pitem = QtGui.QGraphicsPixmapItem(QtGui.QPixmap.fromImage(image))
#        scene = QtGui.QGraphicsScene()
#        scene.addItem(pitem)
#        self.g_view.setScene(scene)
#        self.g_view.fitInView(scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
#        self.g_view.show()
