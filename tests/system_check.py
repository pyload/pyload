#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from builtins import input


def main():
    print("#####   System Information   #####\n")
    print("Platform:", sys.platform)
    print("Operating System:", os.name)
    print("Python:", sys.version.replace("\n", "") + "\n")

    try:
        import pycurl

        print("pycurl:", pycurl.version)
    except Exception:
        print("pycurl:", "missing")

    try:
        import cryptography

        print("cryptography:", cryptography.__version__)
    except Exception:
        print("cryptography:", "missing")

    try:
        import OpenSSL

        print("OpenSSL:", OpenSSL.version.__version__)
    except Exception:
        print("OpenSSL:", "missing")

    try:
        from PIL import Image

        print("image library:", Image.VERSION)
    except Exception:
        try:
            import Image

            print("image library:", Image.VERSION)
        except Exception:
            print("image library:", "missing")

    try:
        import PyQt4.QtCore

        print("pyqt:", PyQt4.QtCore.PYQT_VERSION_STR)
    except Exception:
        print("pyqt:", "missing")

    print("\n\n#####   System Status   #####")
    print("\n##  pyLoad  ##")

    core_err = []
    core_info = []

    if sys.version_info < (3, 6):
        core_err.append("Your python version is to old, Please use at least Python 3.6")

    try:
        import pycurl
    except Exception:
        core_err.append("Please install py-curl to use pyLoad.")

    try:
        from pycurl import AUTOREFERER
    except Exception:
        core_err.append("Your py-curl version is to old, please upgrade!")

    try:
        from PIL import Image
    except Exception:
        try:
            import Image
        except Exception:
            core_err.append(
                "Please install py-imaging/pil/pillow to use Hoster, which uses captchas."
            )

    pipe = subprocess.PIPE
    try:
        p = subprocess.call(["tesseract"], stdout=pipe, stderr=pipe)
    except Exception:
        core_err.append("Please install tesseract to use Hoster, which uses captchas.")

    try:
        import OpenSSL
    except Exception:
        core_info.append(
            "Install OpenSSL if you want to create a secure connection to the core."
        )

    if not js:
        print("no JavaScript engine found")
        print(
            "You will need this for some Click'N'Load links. Install Spidermonkey, ossp-js, pyv8 or rhino"
        )

    if core_err:
        print("The system check has detected some errors:\n")
        for err in core_err:
            print(err)
    else:
        print("No Problems detected, pyLoad should work fine.")

    if core_info:
        print("\nPossible improvements for pyload:\n")
        for line in core_info:
            print(line)

    print("\n##  Web Interface  ##")

    web_err = []
    web_info = []

    try:
        import flup
    except Exception:
        web_info.append("Install Flup to use FastCGI or optional webservers.")

    if web_err:
        print("The system check has detected some errors:\n")
        for err in web_err:
            print(err)
    else:
        print("No Problems detected, Webinterface should work fine.")

    if web_info:
        print("\nPossible improvements for webinterface:\n")
        for line in web_info:
            print(line)


if __name__ == "__main__":
    main()
    input("Press Enter to Exit.")
