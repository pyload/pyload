# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleDereferer import SimpleDereferer


class LinkSaveIn(SimpleDereferer):
    __name__    = "LinkSaveIn"
    __type__    = "crypter"
    __version__ = "2.03"

    __pattern__ = r'https?://(?:www\.)?linksave\.in/\w+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """LinkSave.in decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    COOKIES = [("linksave.in", "Linksave_Language", "english")]

    OFFLINE_PATTERN = r'>(Error )?404 -'
