#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import pyload

from os import path
from setuptools import setup


PROJECT_DIR = path.abspath(path.join(__file__, ".."))

setup(
    name="pyload",

    version=pyload.__version__,

    description='Fast, lightweight and full featured download manager',

    long_description=open(path.join(PROJECT_DIR, "README.md")).read(),

    keywords=["pyload", "download-manager", "one-click-hoster", "download", "jdownloader"],

    url="http://pyload.org",

    download_url="https://github.com/pyload/pyload/releases",

    license=pyload.__license__,

    author="pyLoad Team",

    author_email="support@pyload.org",

    platforms=['Any'],

    #package_dir={'pyload': 'src'},

    packages=['pyload'],

    #package_data=find_package_data(),

    #data_files=[],

    include_package_data=True,

    exclude_package_data={'pyload': ["docs*", "locale*", "tools*"]},  #: exluced from build but not from sdist

    install_requires=[
        "Beaker >= 1.6",
        "bitmath",
        "bottle >= 0.10.0",
        "colorama",
        "Getch",
        "jinja2",
        "markupsafe",
        "MultipartPostHandler",
        "pycurl",
        "rename_process",
        "SafeEval",
        "thrift >= 0.8.0",
        "wsgiserver"
    ],

    extras_require={
        'Few plugins dependencies': ["BeautifulSoup >= 3.2, < 3.3"]
        'Colored log'             : ["colorlog"]
        'Lightweight webserver'   : ["bjoern"]
        'RSS support'             : ["feedparser"]
        'SSL support'             : ["pyOpenSSL"]
        'RSDF/CCF/DLC support'    : ["pycrypto"]
        'Captcha recognition'     : ["PIL"]
        'JSON speedup'            : ["simplejson"]
    },

    #setup_requires=["setuptools_hg"],

    #test_suite='nose.collector',

    #tests_require=['nose', 'websocket-client >= 0.8.0', 'requests >= 1.2.2'],

    entry_points={
        'console_scripts': [
            'pyload = pyload.Core:main',
            'pyload-cli = pyload.Cli:main'
        ]
    },

    zip_safe=False,

    classifiers=[
        "Development Status :: %(code)s - %(status)s" % {'code'  : pyload.__status_code__,
                                                         'status': pyload.__status__},
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: %s" % pyload.__license__,
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet :: WWW/HTTP"
    ]
)
