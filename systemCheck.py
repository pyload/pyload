#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from builtins import input
import os
import subprocess
import sys

#from module import InitHomeDir

def main():
    print("#####   System Information   #####\n")
    print("Platform: " + sys.platform)
    print("Operating System: " + os.name)
    print("Python: " + sys.version.replace("\n", "")+ "\n")

    try:
        import pycurl
        print("pycurl: " + pycurl.version)
    except:
        print("pycurl: missing")

    try:
        import Crypto
        print("py-crypto: " + Crypto.__version__)
    except:
        print("py-crypto: missing")


    try:
        import OpenSSL
        print("OpenSSL: " + OpenSSL.version.__version__)
    except:
        print("OpenSSL: missing")

    try:
        import Image
        print("image library: " + Image.VERSION)
    except:
        print("image library: missing")

    print("\n\n#####   System Status   #####")
    print("\n##  pyLoadCore  ##")

    core_err = []
    core_info = []

    if sys.version_info > (2, 8):
        core_err.append("Your python version is too new, Please use Python 2.6/2.7")

    if sys.version_info < (2, 5):
        core_err.append("Your python version is too old, Please use at least Python 2.5")

    try:
        import pycurl
    except:
        core_err.append("Please install py-curl to use pyLoad.")


    try:
        from pycurl import AUTOREFERER
    except:
        core_err.append("Your py-curl version is too old, please upgrade!")

    try:
        import Image
    except:
        core_err.append("Please install py-imaging/pil to use Hoster, which use captchas.")

    pipe = subprocess.PIPE
    try:
        p = subprocess.call(["tesseract"], stdout=pipe, stderr=pipe)
    except:
        core_info.append("Install tesseract to try automatic captcha resolution.")

    try:
        import OpenSSL
    except:
        core_info.append("Install OpenSSL if you want to create a secure connection to the core.")

    if core_err:
        print("The system check has detected some errors:\n")
        for err in core_err:
            print(err)
    else:
        print("No Problems detected, pyLoadCore should work fine.")

    if core_info:
        print("\nPossible improvements for pyload:\n")
        for line in core_info:
            print(line)

    print("\n##  Webinterface  ##")

    web_err = []
    web_info = []

    try:
        import flup
    except:
        web_info.append("Install Flup to use FastCGI or optional web servers.")


    if web_err:
        print("The system check has detected some errors:\n")
        for err in web_err:
            print(err)
    else:
        print("No Problems detected, web interface should work fine.")

    if web_info:
        print("\nPossible improvements for web interface:\n")
        for line in web_info:
            print(line)


if __name__ == "__main__":
    main()

    # comp. with py2 and 3
    try:
        eval(input("Press Enter to Exit."))
    except SyntaxError:  # will raise in py2
        pass
