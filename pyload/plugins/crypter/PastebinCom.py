# -*- coding: utf-8 -*-

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class PastebinCom(SimpleCrypter):
    __name__ = "PastebinCom"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?pastebin\.com/\w+'

    __description__ = """Pastebin.com decrypter plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    LINK_PATTERN = r'<div class="de\d+">(https?://[^ <]+)(?:[^<]*)</div>'
    TITLE_PATTERN = r'<div class="paste_box_line1" title="(?P<title>[^"]+)">'
