# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleDereferer import SimpleDereferer


class Dereferer(SimpleDereferer):
    __name__    = "Dereferer"
    __type__    = "crypter"
    __version__ = "0.11"

    __pattern__ = r'https?://([^/]+)/.*?(?P<LINK>(ht|f)tps?(://|%3A%2F%2F).+)'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Crypter for dereferers"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]
