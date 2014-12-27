# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleDereferer import SimpleDereferer


class DontKnowMe(SimpleDereferer):
    __name__    = "DontKnowMe"
    __type__    = "crypter"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?dontknow\.me/at/\?(?P<LINK>.+)'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """DontKnow.me decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("selaux", "")]
