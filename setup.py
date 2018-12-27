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

    def _execute(self, func_name, cmd_list):
        execute = getattr(self, func_name)        
        for cmd_name in cmd_list:
            execute(cmd_name)        
        
    def run(self):
        # TODO: add "download_catalog"
        commands = ["extract_messages", "init_catalog", "compile_catalog"]
        
        if self.dry_run:
            self._execute("get_command_name", commands)
            return
            
        dirname = os.path.join(__file__, "..", "src", "pyload", "locale")
        self.mkpath(dirname)  # NOTE: do we have to pass dry_run value explicitly here?
        self._execute("run_command", commands)


def get_name():
    return "pyload-dev"

def get_version():
    filename = os.path.join(__file__, "..", "VERSION")
    with open(filename) as file:
        version = file.read().strip()
    build = os.environ.get('TRAVIS_BUILD_NUMBER', 0)
    return f"{version}.dev{build}"
        
def get_commands():
    return {'build_locale': BuildLocale}

if __name__ == "__main__":
    setup(name=get_name(), version=get_version(), cmdclass=get_commands())
