# -*- coding: utf-8 -*-

from pyload.plugin.internal.SimpleDereferer import SimpleDereferer


class LinkSaveIn(SimpleDereferer):
    __name    = "LinkSaveIn"
    __type    = "crypter"
    __version = "2.03"

    __pattern = r'https?://(?:www\.)?linksave\.in/\w+'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """LinkSave.in decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    COOKIES = [("linksave.in", "Linksave_Language", "english")]

    OFFLINE_PATTERN = r'>(Error )?404 -'
