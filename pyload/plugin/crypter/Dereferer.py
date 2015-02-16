# -*- coding: utf-8 -*-

from pyload.plugin.Crypter import Crypter


class Dereferer(SimpleDereferer):
    __name    = "Dereferer"
    __type    = "crypter"
    __version = "0.11"

    __pattern = r'https?://([^/]+)/.*?(?P<LINK>(ht|f)tps?(://|%3A%2F%2F).+)'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Crypter for dereferers"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
