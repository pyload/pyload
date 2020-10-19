# -*- coding: utf-8 -*-
import base64
import os
import re

import Crypto.Cipher.AES

from ..base.container import BaseContainer


class RSDF(BaseContainer):
    __name__ = "RSDF"
    __type__ = "container"
    __version__ = "0.38"
    __status__ = "testing"

    __pattern__ = r".+\.rsdf$"
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

    __description__ = """RSDF container decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "RaNaN@pyload.org"),
        ("spoob", "spoob@pyload.org"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    KEY = "8C35192D964DC3182C6F84F3252239EB4A320D2500000000"
    IV = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"

    def decrypt(self, pyfile):
        KEY = bytes.fromhex(self.KEY)
        IV = bytes.fromhex(self.IV)

        iv = Crypto.Cipher.AES.new(KEY, Crypto.Cipher.AES.MODE_ECB).encrypt(IV)
        cipher = Crypto.Cipher.AES.new(KEY, Crypto.Cipher.AES.MODE_CFB, iv)

        try:
            fs_filename = os.fsdecode(pyfile.url)
            with open(fs_filename, mode="rb") as rsdf:
                data = rsdf.read()

        except IOError as exc:
            self.fail(exc)

        if re.search(r"<title>404 - Not Found</title>", data):
            pyfile.set_status("offline")

        else:
            try:
                raw_links = bytes.fromhex("".join(data.split())).splitlines()

            except TypeError:
                self.fail(self._("Container is corrupted"))

            for link in raw_links:
                if not link:
                    continue
                link = cipher.decrypt(base64.b64decode(link)).replace('CCF: ', '')
                self.links.append(link)
