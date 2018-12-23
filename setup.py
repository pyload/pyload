#!/usr/bin/env python
# -*- coding: utf-8 -*-
# AUTHOR: vuolter
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

import sys
import os

from pkg_resources import VersionConflict, require
from setuptools import Command, setup

try:
    require("setuptools>=38.3")
except VersionConflict:
    print("Error: version of setuptools is too old (<38.3)!")
    sys.exit(1)


class BuildLocale(Command):
    """
    Build translations
    """
    description = "build locales"
    user_options = []
    
    def initialize_options(self):
        pass
        
    def finalize_options(self):
        pass

    def run(self):
        dirname = os.path.join(__file__, "..", "src", "pyload", "locale")
        os.makedirs(dirname, exist_ok=True)
        
        self.run_command("extract_messages")
        self.run_command("init_catalog")
        # self.run_command('download_catalog')
        self.run_command("compile_catalog")


def get_version():
    filename = os.path.join(__file__, "..", "VERSION")
    with open(filename) as file:
        version = file.read().strip()
    build = os.environ.get('TRAVIS_BUILD_NUMBER', 0)
    return f"{version}.dev{build}"


if __name__ == "__main__":
    setup(version=get_version(), cmdclass={'build_locale': BuildLocale})
