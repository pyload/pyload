# -*- coding: utf-8 -*-
import base64
import os
import re

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from ..base.container import BaseContainer


class RSDF(BaseContainer):
    __name__ = "RSDF"
    __type__ = "container"
    __version__ = "0.37"
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
        ("RaNaN", "RaNaN@pyload.net"),
        ("spoob", "spoob@pyload.net"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    KEY = "8C35192D964DC3182C6F84F3252239EB4A320D2500000000"
    IV = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"

    def decrypt(self, pyfile):
        KEY = bytes.fromhex(self.KEY)
        IV = bytes.fromhex(self.IV)

        backend = default_backend()

        cipher = Cipher(algorithms.AES(KEY), modes.ECB, backend=backend)
        encryptor = cipher.encryptor()
        iv = encryptor.update(IV) + encryptor.finalize()

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
                cipher = Cipher(algorithms.AES(KEY), modes.CFB(iv), backend=backend)
                decryptor = cipher.decryptor()
                value = decryptor.update(base64.b64decode(link) + decryptor.finalize())
                link = value.replace("CCF: ", "")
                self.links.append(link)
