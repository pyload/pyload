# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FilestubeCom(SimpleCrypter):
    __name__    = "FilestubeCom"
    __type__    = "crypter"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?filestube\.(?:com|to)/\w+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Filestube.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a class=\"file-link-main(?: noref)?\" [^>]* href=\"(http://[^\"]+)'
    NAME_PATTERN = r'<h1\s*> (.+)  download\s*</h1>'
