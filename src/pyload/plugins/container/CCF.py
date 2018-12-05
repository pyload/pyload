# -*- coding: utf-8 -*-

import base64
import os
import re

import requests

from ..base.container import Container
from ..utils import encode


class CCF(Container):
    __name__ = "CCF"
    __type__ = "container"
    __version__ = "0.29"
    __status__ = "testing"

    __pyload_version__ = "0.5"

    __pattern__ = r".+\.ccf$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """CCF container decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Willnix", "Willnix@pyload.net"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    def decrypt(self, pyfile):
        fs_filename = encode(pyfile.url)

        with open(fs_filename, mode="rb") as f:
            dlc_content = requests.post(
                "http://service.jdownloader.net/dlcrypt/getDLC.php",
                data={"src": "ccf", "filename": "test.ccf"},
                files={"upload": f},
            ).read()

        dl_folder = self.pyload.config.get("general", "download_folder")
        dlc_file = os.path.join(dl_folder, "tmp_{}.dlc".format(pyfile.name))

        try:
            dlc = base64.b64decode(
                re.search(r"<dlc>(.+)</dlc>", dlc_content, re.S).group(1)
            )

        except AttributeError:
            self.fail(self._("Container is corrupted"))

        with open(dlc_file, mode="w") as tempdlc:
            tempdlc.write(dlc)

        self.links = [dlc_file]
