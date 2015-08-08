# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class FilestubeCom(SimpleCrypter):
    __name__    = "FilestubeCom"
    __type__    = "crypter"
    __version__ = "0.07"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?filestube\.(?:com|to)/\w+'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Filestube.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a class=\"file-link-main(?: noref)?\" [^>]* href=\"(http://[^\"]+)'
    NAME_PATTERN = r'<h1\s*> (?P<N>.+?)  download\s*</h1>'


getInfo = create_getInfo(FilestubeCom)
