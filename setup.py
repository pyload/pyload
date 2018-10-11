# -*- coding: utf-8 -*-
from builtins import _

from setuptools import setup

setup(
    entry_points={
        'console_scripts': [
            'pyLoadCore = pyLoadCore:main',
            'pyLoadCli = pyLoadCli:main'
        ],
    },
)
