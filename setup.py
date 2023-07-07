#!/usr/bin/env python
# -*- coding: utf-8 -*-
#       ____________
#   ___/       |    \_____________ _                 _ ___
#  /        ___/    |    _ __ _  _| |   ___  __ _ __| |   \
# /    \___/  ______/   | '_ \ || | |__/ _ \/ _` / _` |    \
# \            ◯ |      | .__/\_, |____\___/\__,_\__,_|    /
#  \_______\    /_______|_|   |__/________________________/
#           \  /
#            \/

import os

import pkg_resources

# from pkg_resources import VersionConflict, require
from setuptools import Command, setup

# import sys


# try:
#     require("setuptools>=38.3")
# except VersionConflict:
#     print("Error: version of setuptools is too old (<38.3)!")
#     sys.exit(1)


class BuildLocale(Command):
    """
    Build translations
    """

    description = "build locales"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        jinja2_version = pkg_resources.get_distribution("jinja2").version
        if pkg_resources.parse_version(jinja2_version) < pkg_resources.parse_version(
            "3.0.0"
        ):
            mapping_file_version = 2
        else:
            mapping_file_version = 3
        mapping_file = f"babel_v{mapping_file_version}.cfg"

        with open(mapping_file, "r", encoding="utf-8-sig") as fp:
            mapping = fp.read()
        input_dirs = self.distribution.get_option_dict("extract_messages")[
            "input_dirs"
        ][1]

        self.distribution.message_extractors = {input_dirs: mapping}

    def _execute(self, func_name, cmd_list):
        execute = getattr(self, func_name)
        for cmd_name in cmd_list:
            execute(cmd_name)

    def run(self):
        # TODO: add "download_catalog"
        commands = ["extract_messages", "init_catalog", "compile_catalog"]

        if self.dry_run:
            self._execute("get_command_name", commands)
        else:
            dirname = os.path.join(os.path.dirname(__file__), "src", "pyload", "locale")
            self.mkpath(
                dirname
            )  # NOTE: do we have to pass dry_run value explicitly here?
            self._execute("run_command", commands)


def retrieve_version():
    version = None
    build = (
        int(os.environ["PYLOAD_BUILD"].strip()) if "PYLOAD_BUILD" in os.environ else 0
    )

    filename = os.path.join(os.path.dirname(__file__), "VERSION")
    with open(filename) as fp:
        version = os.environ.get("PYLOAD_VERSION", fp.read()).strip()

    return f"{version}.dev{build}" if build else version


# TODO: BuildDocs running `sphinx-apidoc`
if __name__ == "__main__":
    setup(
        version=retrieve_version(),
        cmdclass={"build_locale": BuildLocale},
    )
