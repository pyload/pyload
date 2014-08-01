# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FilestubeCom(SimpleCrypter):
    __name__ = "FilestubeCom"
    __type__ = "crypter"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?filestube\.(?:com|to)/\w+'

    __description__ = """Filestube.com decrypter plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    LINK_PATTERN = r'<a class=\"file-link-main(?: noref)?\" [^>]* href=\"(http://[^\"]+)'
    TITLE_PATTERN = r'<h1\s*> (?P<title>.+)  download\s*</h1>'
