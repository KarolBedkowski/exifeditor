# -*- coding: utf-8 -*-
""" Exif related functions.

Copyright (c) Karol Będkowski, 2014

This file is part of exifeditor
Licence: GPLv2+
"""

__author__ = u"Karol Będkowski"
__copyright__ = u"Copyright (c) Karol Będkowski, 2014"
__version__ = "2014-11-09"


import logging

from gi.repository import GExiv2

_LOG = logging.getLogger(__name__)

_EXIF_GROUP_SORTING = {
    'Exif.Image': -100,
    'Exif.Photo': -80,
    'Xmp.dc': -50,
    'Exif.GPSInfo': -30,
    'Iptc.Application2': -29,
}


class ExifUpdateError(Exception):
    pass

class ExifSaveError(Exception):
    pass


class Image(object):
    """Image file representation. """
    def __init__(self, path):
        self.path = path
        self.exif = GExiv2.Metadata(path)
        self.groups = None
        self._create_groups()
        self.updated = False

    def save(self):
        """ Save changes """
        _LOG.info("Image.save %s", self.path)
        try:
            res = self.exif.save_file()
            _LOG.info("Image.save done: res=%r", res)
        except Exception, err:
            _LOG.exception("Exif.save(%s) error", self.path)
            raise ExifSaveError(err)
            return False
        else:
            self.updated = False
        return True

    def get_value(self, tag):
        """ Get value for given tag.
        Args:
            tag: tag name
        Returns:
            (raw value, interpreted value)
        """
        val = self.exif.get(tag)
        if val is None:
            return None
        # val = val.replace('\0', '').replace('\n', '; ').strip()
        val = val.decode('utf-8', errors='replace')
        tag_type = self.exif.get_tag_type(tag)
        if tag_type in ('Ascii', 'XmpSeq', 'XmpText', 'XmpBag'):
            val_int = val
        elif tag_type == 'String':
            val_int = unicode(val)
        elif tag_type == 'LangAlt':
            if 'lang="' in val:
                val_int = val.split(' ', 1)[1]
        else:
            # interpret only non-ascii tags
            val_int = self.exif.get_tag_interpreted_string(tag)
            val_int = unicode(val_int, 'iso-8859-2', errors='replace')
        return val, val_int

    def set_value(self, tag, value):
        """ Change exif tag value.

            Returns True when value changed.

            TODO: better way to detect changes
        """
        # _LOG.debug("Exif.set_value(%s, %s, %r)", self.path, tag, value)
        old_value = self.exif.get(tag)
        self.exif[tag] = value
        if tag not in self.exif:
            raise ExifUpdateError("Error updating tag %s" % tag)
        new_value = self.exif[tag]  # because of interpretation
        self.updated |= old_value != new_value
        return self.updated

    def del_value(self, tag):
        """ Delete tag from exif. """
        if tag in self.exif:
            del self.exif[tag]
            self.updated = True
        return self.updated

    def get_tags_by_group(self, group):
        """ Get tags in given `group` """
        for key in self.exif.get_tags():
            if key.startswith(group):
                yield key

    def get_tag_label(self, tag):
        """ Get human friendly tag name. """
        label = self.exif.get_tag_label(tag)
        if label:
            label = unicode(label, 'iso-8859-2', errors='replace')
        return label or tag

    def get_tag_descr(self, tag):
        """ Get human friendly tag description. """
        descr = self.exif.get_tag_description(tag)
        if descr:
            descr = unicode(descr, 'iso-8859-2', errors='replace')
        return descr or ''

    def get_groups(self):
        """ Get groups of tags in exif """
        for group in self.groups:
            yield group, group.replace('.', ' ')

    def _create_groups(self):
        """ Find groups of tags """
        groups = {}
        for tag in self.exif.get_tags():
            prefix = tag.rsplit('.', 1)[0]
            groups[prefix] = None
        self.groups = sorted(groups.iterkeys(),
                             key=lambda x: (_EXIF_GROUP_SORTING.get(x, 0), x))

    def debug_tag(self, tag):
        """ Get given tag informations (for debugging. """
        return {
            "Label": repr(self.exif.get_tag_label(tag)),
            "Type": repr(self.exif.get_tag_type(tag)),
            "Value": repr(self.exif.get(tag))[:100],
            "Interp": repr(self.exif.get_tag_interpreted_string(tag))[:100],
        }

    def debug_tag_log(self, tag):
        _LOG.debug("Image.debug_tag_log: tag=%s; %s", tag,
                   "; ".join(key + ": " + repr(val)
                             for key, val in self.debug_tag(tag).iteritems()))

    DESCRIPTION_TAG = 'Exif.Image.ImageDescription'

    def _get_description(self):
        descr = self.exif.get(self.DESCRIPTION_TAG) or ''
        return unicode(descr, 'utf-8')

    def _set_description(self, value):
        return self.set_value(self.DESCRIPTION_TAG, value)

    """  Exif.Image.ImageDescription property """
    description = property(_get_description, _set_description)

    COMMENT_TAG = 'Exif.Photo.UserComment'

    def _get_comment(self):
        # TODO; check
        comment = self.exif.get(self.COMMENT_TAG) or ''
        if comment.startswith('\x00\x00\x00\x00\x00\x00\x00\x00'):  # undefined
            comment = comment[8:]
        elif comment.startswith('Unicode'):
            comment = comment[7:].lstrip('\x00')
            comment = unicode(comment, 'utf-8')
        elif comment.startswith('ASCII'):
            comment = comment[5:].lstrip('\x00')
        elif comment.startswith('charset="Ascii"'):
            comment = comment[15:].lstrip()
        return comment

    def _set_comment(self, value):
        if value == self._get_comment():
            return
        try:
            strvalue = str(value)
            self.exif[self.COMMENT_TAG] = 'ASCII ' + strvalue
        except UnicodeError:
            self.exif[self.COMMENT_TAG] = 'Unicode ' + value
        self.updated = True

    """  Exif.Photo.UserComment property """
    comment = property(_get_comment, _set_comment)

    ARTIST_TAG = 'Exif.Image.Artist'

    def _get_artist(self):
        artist = self.exif.get(self.ARTIST_TAG) or ''
        artist = unicode(artist, 'utf-8')
        artist = artist.replace('\x00', '\n')
        return artist

    def _set_artist(self, value):
        if self._get_artist() != value:
            self.exif[self.ARTIST_TAG] = value
            self.updated = True

    """  Exif.Image.Artist property. """
    artist = property(_get_artist, _set_artist)

    COPYRIGHT_TAG = 'Exif.Image.Copyright'

    def _get_copyright(self):
        copyr = self.exif.get(self.COPYRIGHT_TAG) or ''
        return unicode(copyr, 'utf-8')

    def _set_copyright(self, value):
        if value != self._get_copyright():
            self.exif[self.COPYRIGHT_TAG] = value
            self.updated = True

    """  Exif.Image.Copyright property. """
    copyright = property(_get_copyright, _set_copyright)

    DATETIME_TAG = 'Exif.Image.DateTime'

    def _get_datetime(self):
        dtime = self.exif.get(self.DATETIME_TAG) or ''
        return dtime

    def _set_datetime(self, value):
        if value != self._get_datetime():
            self.exif[self.DATETIME_TAG] = value
            self.updated = True

    """  Exif.Image.DateTime property. """
    datetime = property(_get_datetime, _set_datetime)
