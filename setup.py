# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    entry_points={
        "console_scripts": [
            "pyLoad = pyLoad:main",
            "pyLoadCli = pyLoadCli:main",
        ]
    }
)
