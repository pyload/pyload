# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import sys
from os import path

from setuptools import setup

PROJECT_DIR = path.abspath(path.dirname(__file__))

extradeps = []
if sys.version_info <= (2, 5):
    extradeps += 'simplejson'

from pyload import __version__

setup(
    name="pyload",
    version=__version__,
    description='Fast, lightweight and full featured download manager.',
    long_description=open(path.join(PROJECT_DIR, "README.md")).read(),
    keywords=('pyload', 'download-manager', 'one-click-hoster', 'download'),
    url="https://pyload.net",
    download_url='https://github.com/pyload/pyload/releases',
    license='AGPL v3',
    author="pyLoad Team",
    author_email="support@pyload.net",
    platforms=('Any',),
    #package_dir={'pyload': 'src'},
    packages=['pyload'],
    #package_data=find_package_data(),
    #data_files=[],
    include_package_data=True,
    exclude_package_data={'pyload': ['docs*', 'scripts*', 'tests*']}, #exluced from build but not from sdist
    # 'bottle >= 0.10.0' not in list, because its small and contain little modifications
    install_requires=['pycurl', 'Beaker >= 1.6'] + extradeps,
    extras_require={
        'SSL': ["pyOpenSSL"],
        'DLC': ['pycrypto'],
        'Lightweight webserver': ['bjoern'],
        'RSS plugins': ['feedparser'],
        'Few Hoster plugins': ['BeautifulSoup>=3.2, <3.3']
    },
    #setup_requires=["setuptools_hg"],
    test_suite='nose.collector',
    tests_require=['nose', 'websocket-client >= 0.8.0', 'requests >= 1.2.2'],
    entry_points={
        'console_scripts': [
            'pyload = pyload.Core:main'
        ]},
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Internet :: WWW/HTTP",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2"
    ]
)
