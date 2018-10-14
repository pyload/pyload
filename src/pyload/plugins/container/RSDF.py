# -*- coding: utf-8 -*-
import binascii
import re
from builtins import _

import Cryptodome.Cipher.AES

from pyload.plugins.internal.container import Container
from pyload.plugins.utils import encode


class RSDF(Container):
    __name__ = "RSDF"
    __type__ = "container"
    __version__ = "0.37"
    __pyload_version__ = "0.5"
    __status__ = "testing"

    __pattern__ = r".+\.rsdf$"
    __config__ = [
        ("activated", "bool", "Activated", True),
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
        KEY = binascii.unhexlify(self.KEY)
        IV = binascii.unhexlify(self.IV)

        iv = Cryptodome.Cipher.AES.new(KEY, Cryptodome.Cipher.AES.MODE_ECB).encrypt(IV)
        cipher = Cryptodome.Cipher.AES.new(KEY, Cryptodome.Cipher.AES.MODE_CFB, iv)

        try:
            fs_filename = encode(pyfile.url)
            with open(fs_filename, "r") as rsdf:
                data = rsdf.read()

        except IOError as e:
            self.fail(e)

        if re.search(r"<title>404 - Not Found</title>", data):
            pyfile.setStatus("offline")

        else:
            try:
                raw_links = binascii.unhexlify("".join(data.split())).splitlines()

            except TypeError:
                self.fail(_("Container is corrupted"))

            for link in raw_links:
                if not link:
                    continue
                link = cipher.decrypt(link.decode("base64")).replace("CCF: ", "")
                self.links.append(link)
