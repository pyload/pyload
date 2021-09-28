# -*- coding: utf-8 -*-

import base64
import os
import re

from pyload.core.network.http.http_request import FormFile

from ..base.container import BaseContainer


class CCF(BaseContainer):
    __name__ = "CCF"
    __type__ = "container"
    __version__ = "0.30"
    __status__ = "testing"

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
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def decrypt(self, pyfile):
        fs_filename = os.fsdecode(pyfile.url)

        dlc_content = self.load(
            "http://service.jdownloader.net/dlcrypt/getDLC.php",
            post={
                "src": "ccf",
                "filename": "test.ccf",
                "upload": FormFile(fs_filename),
            },
            multipart=True,
        )

        dl_folder = self.pyload.config.get("general", "storage_folder")
        dlc_file = os.path.join(dl_folder, "tmp_{}.dlc".format(pyfile.name))

        try:
            dlc = base64.b64decode(
                re.search(r"<dlc>(.+)</dlc>", dlc_content, re.S).group(1)
            )

        except AttributeError:
            self.fail(self._("Container is corrupted"))

        with open(dlc_file, mode="wb") as fp:
            fp.write(dlc)

        self.links = [dlc_file]
