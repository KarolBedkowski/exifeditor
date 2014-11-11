# -*- coding: utf-8 -*-
""" Exif related functions.

Copyright (c) Karol Będkowski, 2014

This file is part of exifeditor
Licence: GPLv2+
"""

__author__ = u"Karol Będkowski"
__copyright__ = u"Copyright (c) Karol Będkowski, 2014"
__version__ = "2014-11-09"


from gi.repository import GExiv2


_EXIF_GROUP_SORTING = {
    'Exif.Image': -100,
    'Exif.Photo': -80,
    'Xmp.dc': -50,
    'Exif.GPSInfo': -30,
    'Iptc.Application2': -29,
}


class Image(object):
    """Image file representation. """
    def __init__(self, path):
        self.path = path
        self.exif = GExiv2.Metadata(path)
        self.groups = None
        self._create_groups()

    def save(self):
        """ Save changes """
        self.exif.save_file()
        return True

    def get_value(self, tag):
        """ Get value for given tag """
        val = self.exif.get(tag)
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
        old_value = self.exif[tag]
        self.exif[tag] = value
        new_value = self.exif[tag]
        return old_value != new_value

    def get_tags_by_group(self, group):
        """ Get tags in given `group` """
        for key in self.exif.get_tags():
            if key.startswith(group):
                yield key

    def get_tag_label(self, tag):
        label = self.exif.get_tag_label(tag)
        if label:
            label = unicode(label, 'iso-8859-2', errors='replace')
        return label or tag

    def get_tag_descr(self, tag):
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
        print 'Tag:', tag, '\t\t\tLabel:', self.exif.get_tag_label(tag),
        print '\t\t\tType:', self.exif.get_tag_type(tag)
        print 'Value:', repr(self.exif.get(tag)[:100])
        print 'Interpreted:', repr(self.exif.\
                                   get_tag_interpreted_string(tag)[:100])
        print '---------------------------------------------'
