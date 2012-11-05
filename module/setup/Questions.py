#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: RaNaN
"""
from getpass import getpass
import module.common.pylgettext as gettext
import os
from os import makedirs
from os.path import abspath, dirname, exists, join
from subprocess import PIPE, call
import sys
from sys import exit
from module.utils import get_console_encoding

class Questions():
    
    questions = [
        Ask(["Welcome to the pyLoad Configuration Assistent.",
             "It will check your system and make a basic setup in order to run pyLoad.",
             "If you don't know which value to choose, take the deafault one.",
             "Don't forget: You can always rerun this assistent with --setup or -s parameter, when you start pyLoadCore."]),
        Ask(["The value in brackets [] always is the default value",
             "When you are ready, hit Enter"], clionly=True)

        ]


class Ask():
    def __init__(self, qst, default = None, answers=[], bool=False, password=False, webonly=False, clionly=False):
        self.qst = qst
        self.default = default
        self.answers = answers
        self.bool = bool
        self. password = password


