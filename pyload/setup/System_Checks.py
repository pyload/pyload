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

class System_Checks():
    def __init__(self):
        self.result = ""

    def print_str(self, text, translate = True):
        if translate:
            self.result += _(text) + "\n"
        else:
            self.result += text + "\n"

    def print_dep(self, name, value):
        """Print Status of dependency"""
        if value:
            self.print_str(name + ": OK", False)
        else:
            self.print_str(name + ": missing", False)

    def check_basic(self):
        self.result = "" #clear result
        python = False
        if sys.version_info[:2] > (2, 7):
            self.print_str("Your python version is to new, Please use Python 2.6/2.7")
        elif sys.version_info[:2] < (2, 5):
            self.print_str("Your python version is to old, Please use at least Python 2.5")
        else:
            self.print_str("Python Version: OK")
            python = True

        curl = self.check_module("pycurl")
        self.print_dep("pycurl", curl)

        sqlite = self.check_module("sqlite3")
        self.print_dep("sqlite3", sqlite)

        beaker = self.check_module("beaker")
        self.print_dep("beaker", beaker)

        jinja = True
        try:
            import jinja2
            v = jinja2.__version__
            if v and "unknown" not in v:
                if not v.startswith("2.5") and not v.startswith("2.6"):
                    self.print_str("Your installed jinja2 version %s seems too old.") % jinja2.__version__
                    self.print_str("You can safely continue but if the webinterface is not working,")
                    self.print_str("please upgrade or deinstall it, pyLoad includes a sufficient jinja2 library.")
                    jinja = False
        except:
            pass
        self.print_dep("jinja2", jinja)
        
        return self.result, (python and curl and sqlite and (beaker or jinja))

    def check_ssl(self):
        self.result = "" #clear result
        ssl = self.check_module("OpenSSL")
        self.print_dep("py-OpenSSL", ssl)
        return self.result, ssl

    def check_crypto(self):
        self.result = "" #clear result
        crypto = self.check_module("Crypto")
        self.print_dep("pycrypto", crypto)
        return self.result, crypto

    def check_captcha(self):
        self.result = "" #clear result
        pil = self.check_module("Image")
        self.print_dep("py-imaging", pil)
        if os.name == "nt":
            tesser = self.check_prog([join(pypath, "tesseract", "tesseract.exe"), "-v"])
        else:
            tesser = self.check_prog(["tesseract", "-v"])
        self.print_dep("tesseract", tesser)
        return self.result, pil and tesser

    def check_js(self):
        self.result = "" #clear result
        from module.common import JsEngine
        js = True if JsEngine.ENGINE else False
        self.print_dep(_("JS engine"), js)
        return self.result, pil and tesser

    def check_module(self, module):
        try:
            __import__(module)
            return True
        except:
            return False

    def check_prog(self, command):
        pipe = PIPE
        try:
            call(command, stdout=pipe, stderr=pipe)
            return True
        except:
            return False
        
