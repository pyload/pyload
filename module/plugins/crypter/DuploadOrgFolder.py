# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class DuploadOrgFolder(SimpleCrypter):
    __name__ = "DuploadOrgFolder"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?dupload\.org/folder/\d+/'

    __description__ = """Dupload.org folder decrypter plugin"""
    __authors__ = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<td style="[^"]+"><a href="(http://[^"]+)" target="_blank">[^<]+</a></td>'
