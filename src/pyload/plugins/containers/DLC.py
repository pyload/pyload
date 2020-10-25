# -*- coding: utf-8 -*-

import base64
import os
import re
import xml.dom.minidom

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from pyload.core.utils.convert import to_str

from ..base.container import BaseContainer


class BadDLC(Exception):
    pass


class DLCDecrypter(object):
    KEY = b"cb99b5cbc24db398"
    IV = b"9bc24cb995cb8db3"
    API_URL = "http://service.jdownloader.org/dlcrypt/service.php?srcType=dlc&destType=pylo&data={}"

    def __init__(self, plugin):
        self.plugin = plugin

    def decrypt(self, data):
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes.")

        data = data.strip()

        data += b"=" * (-len(data) % 4)

        dlc_key = data[-88:]
        dlc_data = base64.b64decode(data[:-88])
        dlc_content = self.plugin.load(self.API_URL.format(to_str(dlc_key)))

        try:
            rc = base64.b64decode(
                re.search(r"<rc>(.+)</rc>", dlc_content, re.S).group(1)
            )[:16]

        except AttributeError:
            raise BadDLC

        cipher = Cipher(
            algorithms.AES(self.KEY), modes.CBC(self.IV), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        key = iv = decryptor.update(rc) + decryptor.finalize()

        cipher = Cipher(
            algorithms.AES(key), modes.CBC(iv), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        xml_data = to_str(base64.b64decode(
            decryptor.update(dlc_data) + decryptor.finalize()
        ))

        root = xml.dom.minidom.parseString(xml_data).documentElement
        content_node = root.getElementsByTagName("content")[0]

        packages = DLCDecrypter._parse_packages(content_node)

        return packages

    @staticmethod
    def _parse_packages(start_node):
        return [
            (
                to_str(base64.b64decode(node.getAttribute("name"))),
                DLCDecrypter._parse_links(node)
            )
            for node in start_node.getElementsByTagName("package")
        ]

    @staticmethod
    def _parse_links(start_node):
        return [
            to_str(base64.b64decode(node.getElementsByTagName("url")[0].firstChild.data))
            for node in start_node.getElementsByTagName("file")
        ]


class DLC(BaseContainer):
    __name__ = "DLC"
    __type__ = "container"
    __version__ = "0.34"
    __status__ = "testing"

    __pattern__ = r"(?:.+\.(?:dlc|DLC)|[\w\+^_]+==[\w\+^_/]+==)$"
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

    __description__ = """DLC container decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "RaNaN@pyload.net"),
        ("spoob", "spoob@pyload.net"),
        ("mkaay", "mkaay@mkaay.de"),
        ("Schnusch", "Schnusch@users.noreply.github.com"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def decrypt(self, pyfile):
        fs_filename = os.fsdecode(pyfile.url)
        with open(fs_filename, "rb") as dlc:
            data = dlc.read().strip()

        decrypter = DLCDecrypter(self)

        try:
            packages = decrypter.decrypt(data)

        except BadDLC:
            self.fail(_("Container is corrupted"))

        self.packages = [(name or pyfile.name, links, name or pyfile.name)
                         for name, links in packages]
