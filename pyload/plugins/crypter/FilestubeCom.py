# -*- coding: utf-8 -*-

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class FilestubeCom(SimpleCrypter):
    __name__ = "FilestubeCom"
    __type__ = "crypter"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?filestube\.(?:com|to)/\w+'

    __description__ = """Filestube.com decrypter plugin"""
    __authors__ = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a class=\"file-link-main(?: noref)?\" [^>]* href=\"(http://[^\"]+)'
    TITLE_PATTERN = r'<h1\s*> (.+)  download\s*</h1>'
