# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class PastebinCom(SimpleCrypter):
    __name__    = "PastebinCom"
    __type__    = "crypter"
    __version__ = "0.08"
    __status__  = "testing"

    __pattern__ = r'https://(?:www\.)?pastebin\.com/(.+i=)?(?P<ID>\w{8})'
    __config__  = [("activated"         , "bool"          , "Activated"                                        , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available"                 , True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"                   , "Default"),
                   ("max_wait"          , "int"           , "Reconnect if waiting time is greater than minutes", 10       )]

    __description__ = """Pastebin.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    URL_REPLACEMENTS = [(__pattern__ + '.*', r'http://www.pastebin.com/\g<ID>')]

    NAME_PATTERN = r'<div class="paste_box_line1" title="(?P<N>.+?)"'
    LINK_PATTERN = r'<div class="de\d+">(.+?)<'
