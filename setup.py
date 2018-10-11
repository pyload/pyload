# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    entry_points={
        'console_scripts': [
            'pyLoadCore = pyLoadCore:main',
            'pyLoadCli = pyLoadCli:main'
        ],
    },
)
