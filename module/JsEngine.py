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

from imp import find_module
ENGINE = ""

try:
    find_module("spidermonkey")
    ENGINE = "spidermonkey"
except:
    pass

if not ENGINE:
    try:
        find_module("PyV8")
        ENGINE = "pyv8"
    except:
        pass

if not ENGINE:
    try:
        import subprocess
        subprocess.Popen(["js", "-v"], bufsize=-1,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ENGINE = "js"
    except:
        pass

class JsEngine():
    def __init__(self):
        self.engine = ENGINE
        self.init = False

    def __nonzero__(self):
        return False if not ENGINE else True

    def eval(self, script):
        if not self.init:
            if ENGINE == "spidermonkey":
                import spidermonkey
                global spidermonkey
            elif ENGINE == "pyv8":
                import PyV8
                global PyV8
            self.init = True

        if not ENGINE:
            raise Exception("No JS Engine")
        elif ENGINE == "spidermonkey":
            return self.eval_spidermonkey(script)
        elif ENGINE == "pyv8":
            return self.eval_pyv8(script)
        elif ENGINE == "js":
            return self.eval_js(script)


    def eval_spidermonkey(self, script):
        rt = spidermonkey.Runtime()
        cx = rt.new_context()
        return cx.execute(script)

    def eval_pyv8(self, script):
        rt = PyV8.JSContext()
        rt.enter()
        return rt.eval(script)

    def eval_js(self, script):
        script = "print(eval('%s'))" % script.replace("'",'"')
        p = subprocess.Popen(["js", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1)
        res = p.stdout.read().strip()
        return res

    def error(self):
        return _("No js engine detected, please install either Spidermonkey, ossp-js or pyv8")

if __name__ == "__main__":
    js = JsEngine()
    import subprocess
    import spidermonkey
    import PyV8

    test = '"a"+"b"'

    print js.eval_js(test)
    print js.eval_spidermonkey(test)
    print js.eval_pyv8(test)