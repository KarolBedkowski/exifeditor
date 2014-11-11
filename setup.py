# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

import exifeditor
import exifeditor.version

CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    'License :: OSI Approved :: GNU General Public License (GPL)'
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Environment :: Win32 (MS Windows)",
    "Environment :: X11 Applications",
    "Topic :: Multimedia :: Graphics",
]

REQUIRES = [
    'setuptools',
    'gexiv2',
    'pyqt4',
]

setup(
    name='exifeditor',
    version=exifeditor.version.VERSION,
    description='exifeditor - edit exif tags in images.',
    long_description=open("README.rst").read(),
    classifiers=CLASSIFIERS,
    author='Karol Będkowski',
    author_email='karol.bedkowski at gmail.com',
    url='',
    download_url='',
    license='GPL v3',
    py_modules=['exifeditor', 'exifeditor_dbg'],
    packages=find_packages('.'),
    package_dir={'': '.'},
    include_package_data=True,
    install_requires=REQUIRES,
    entry_points="""
       [console_scripts]
       exifeditor = exifeditor.exifeditor:main
    """,
    zip_safe=False,
)
