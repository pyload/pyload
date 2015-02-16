# -*- coding: utf-8 -*-

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class FilestubeCom(SimpleCrypter):
    __name    = "FilestubeCom"
    __type    = "crypter"
    __version = "0.05"

    __pattern = r'http://(?:www\.)?filestube\.(?:com|to)/\w+'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Filestube.com decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a class=\"file-link-main(?: noref)?\" [^>]* href=\"(http://[^\"]+)'
    NAME_PATTERN = r'<h1\s*> (?P<N>.+)  download\s*</h1>'
