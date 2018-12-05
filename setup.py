#!/usr/bin/env python
# -*- coding: utf-8 -*-
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

import sys

from pkg_resources import VersionConflict, require
from setuptools import Command, setup

try:
    require("setuptools>=38.3")
except VersionConflict:
    print("Error: version of setuptools is too old (<38.3)!")
    sys.exit(1)


# TODO: Check if works!
class BuildLocale(Command):
    """
    Build translations
    """
    description = "build locales"
    user_options = []

    def run(self):
        self.run_command("extract_messages")
        self.run_command("init_catalog")
        # self.run_command('download_catalog')
        self.run_command("compile_catalog")


if __name__ == "__main__":
    setup(use_pyscaffold=True)
