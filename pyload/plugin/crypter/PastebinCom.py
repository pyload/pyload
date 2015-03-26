# -*- coding: utf-8 -*-

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class PastebinCom(SimpleCrypter):
    __name    = "PastebinCom"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?pastebin\.com/\w+'
    __config  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Pastebin.com decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<div class="de\d+">(https?://[^ <]+)(?:[^<]*)</div>'
    NAME_PATTERN = r'<div class="paste_box_line1" title="(?P<N>[^"]+)">'
