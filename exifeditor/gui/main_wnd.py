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
        self.tv_dirs.setRootIndex(model.index(QtCore.QDir.rootPath()))
        self.tv_dirs.setCurrentIndex(model.index(QtCore.QDir.currentPath()))
#        self.tv_dirs.selectionModel().select(
#               model.index(QtCore.QDir.currentPath()),
#               QtGui.QItemSelectionModel.ClearAndSelect)
        self.tv_dirs.setColumnWidth(0, 200)

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
        self.tabWidget.currentChanged.connect(self._on_tab_changed)
        # file list model
        sel_model = self.lv_files.selectionModel()
        sel_model.currentChanged.connect(self._on_lv_files_selection)
#        sel_model.selectionChanged.connect(self._on_lv_files_selection)
        # text fields
        self.te_description.textChanged.connect(self._on_te_description_tch)
        self.te_comment.textChanged.connect(self._on_te_comment_tch)
        self.te_artist.textChanged.connect(self._on_te_artist_tch)
        self.te_copyright.textEdited.connect(self._on_te_copyright_tch)
        self.dt_datetime.dateTimeChanged.connect(self._on_te_datetime_ch)

    def _on_tv_dirs_activated(self, index):
        node = self._tv_dirs_model.filePath(index)
        self._current_path = str(node)
        self.lv_files.clearSelection()
        self._lv_files_model.update(str(node))
        self.lv_files.resizeColumnsToContents()
        self._clear()

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
        self._clear()

    def _on_save_pressed(self):
        if not self._current_image:
            return
        self.statusBar().showMessage('Saving...')
        if self._current_image.save():
            self._show_image(self._current_image.path)
            self.statusBar().showMessage('Saved', 2000)
        else:
            self.statusBar().showMessage('Error...', 2000)

    def _clear(self):
        self.tv_info.reset()
        self._current_image = None
        self.g_view.setPixmap(QtGui.QPixmap())
        self._tv_info_model.update(None)
        self.te_description.setPlainText("")
        self.te_comment.setPlainText("")
        self.te_artist.setPlainText("")
        self.te_copyright.setText("")
        self.dt_datetime.setDateTime(QtCore.QDateTime.currentDateTime())

    def _show_image(self, path):
        self.statusBar().showMessage('Loading...')
        self.tv_info.reset()
        self._current_image = exif.Image(path)
        thumb = QtGui.QImage(path)
        thumb = thumb.scaled(self.g_view.size(), QtCore.Qt.KeepAspectRatio)
        self.g_view.setPixmap(QtGui.QPixmap.fromImage(thumb))
        self._update_tab_basic()
        self._update_tab_exif()
        self.statusBar().clearMessage()

    def _update_tab_basic(self):
        image = self._current_image
        if not image:
            return
        self.te_description.setPlainText(image.description)
        self.te_comment.setPlainText(image.comment)
        self.te_artist.setPlainText(image.artist)
        self.te_copyright.setText(image.copyright)
        try:
            dtime = QtCore.QDateTime.fromString(image.datetime,
                                                'yyyy:MM:dd HH:mm:ss')
            self.dt_datetime.setDateTime(dtime)
        except:
            pass

    def _update_tab_exif(self):
        self._tv_info_model.update(self._current_image)
        self.tv_info.expandAll()
        self.tv_info.resizeColumnToContents(0)
        self.tv_info.resizeColumnToContents(1)

#        pitem = QtGui.QGraphicsPixmapItem(QtGui.QPixmap.fromImage(image))
#        scene = QtGui.QGraphicsScene()
#        scene.addItem(pitem)
#        self.g_view.setScene(scene)
#        self.g_view.fitInView(scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
#        self.g_view.show()

    def _on_te_description_tch(self):
        if self._current_image:
            self._current_image.description = \
                    unicode(self.te_description.toPlainText())

    def _on_te_comment_tch(self):
        if self._current_image:
            self._current_image.comment = \
                    unicode(self.te_comment.toPlainText())

    def _on_te_artist_tch(self):
        if self._current_image:
            self._current_image.artist = \
                    unicode(self.te_artist.toPlainText())

    def _on_te_copyright_tch(self, value):
        if self._current_image:
            self._current_image.copyright = unicode(value)

    def _on_te_datetime_ch(self, value):
        if self._current_image:
            self._current_image.datetime = \
                 str(value.toString('yyyy:MM:dd HH:mm:ss'))

    def _on_tab_changed(self, idx):
        if idx == 0:
            self._update_tab_basic()
#        elif idx == 1:
#           self._update_tab_exif()
