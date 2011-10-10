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
from os.path import join, exists
from urllib import quote


ENGINE = ""

DEBUG = False
JS = False
PYV8 = False
RHINO = False


if not ENGINE:
    try:
        import subprocess

        subprocess.Popen(["js", "-v"], bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        p = subprocess.Popen(["js", "-e", "print(23+19)"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        #integrity check
        if out.strip() == "42":
            ENGINE = "js"
        JS = True
    except:
        pass

if not ENGINE or DEBUG:
    try:
        find_module("PyV8")
        ENGINE = "pyv8"
        PYV8 = True
    except:
        pass

if not ENGINE or DEBUG:
    try:
        path = "" #path where to find rhino

        if exists("/usr/share/java/js.jar"):
            path = "/usr/share/java/js.jar"
        elif exists("js.jar"):
            path = "js.jar"
        elif exists(join(pypath, "js.jar")): #may raises an exception, but js.jar wasnt found anyway
            path = join(pypath, "js.jar")

        if not path:
            raise Exception

        import subprocess

        p = subprocess.Popen(["java", "-cp", path, "org.mozilla.javascript.tools.shell.Main", "-e", "print(23+19)"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        #integrity check
        if out.strip() == "42":
            ENGINE = "rhino"
        RHINO = True
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
            if ENGINE == "pyv8" or (DEBUG and PYV8):
                import PyV8
                global PyV8

            self.init = True

        if type(script) == unicode:
            script = script.encode("utf8")

        if not ENGINE:
            raise Exception("No JS Engine")

        if not DEBUG:
            if ENGINE == "pyv8":
                return self.eval_pyv8(script)
            elif ENGINE == "js":
                return self.eval_js(script)
            elif ENGINE == "rhino":
                return self.eval_rhino(script)
        else:
            results = []
            if PYV8:
                res = self.eval_pyv8(script)
                print "PyV8:", res
                results.append(res)
            if JS:
                res = self.eval_js(script)
                print "JS:", res
                results.append(res)
            if RHINO:
                res = self.eval_rhino(script)
                print "Rhino:", res
                results.append(res)

            warning = False
            for x in results:
                for y in results:
                    if x != y:
                        warning = True

            if warning: print "### WARNING ###: Different results"

            return results[0]

    def eval_pyv8(self, script):
        rt = PyV8.JSContext()
        rt.enter()
        return rt.eval(script)

    def eval_js(self, script):
        script = "print(eval(unescape('%s')))" % quote(script)
        p = subprocess.Popen(["js", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1)
        out, err = p.communicate()
        res = out.strip()
        return res

    def eval_rhino(self, script):
        script = "print(eval(unescape('%s')))" % quote(script)
        p = subprocess.Popen(["java", "-cp", path, "org.mozilla.javascript.tools.shell.Main", "-e", script],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1)
        out, err = p.communicate()
        res = out.strip()
        return res.decode("utf8").encode("ISO-8859-1")

    def error(self):
        return _("No js engine detected, please install either Spidermonkey, ossp-js, pyv8 or rhino")

if __name__ == "__main__":
    js = JsEngine()

    test = u'"ü"+"ä"'
    js.eval(test)