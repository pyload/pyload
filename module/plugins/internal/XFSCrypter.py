# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo
from module.plugins.internal.utils import set_cookie


class XFSCrypter(SimpleCrypter):
    __name__    = "XFSCrypter"
    __type__    = "crypter"
    __version__ = "0.22"
    __status__  = "stable"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"            , "bool", "Activated"                                        , True),
                   ("use_premium"          , "bool", "Use premium account if available"                 , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"                        , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package"              , True),
                   ("max_wait"             , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """XFileSharing decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    PLUGIN_DOMAIN        = None

    URL_REPLACEMENTS     = [(r'&?per_page=\d+', ""), (r'[?/&]+$', ""), (r'(.+/[^?]+)$', r'\1?'), (r'$', r'&per_page=10000')]

    NAME_PATTERN         = r'<[Tt]itle>.*?\: (?P<N>.+) folder</[Tt]itle>'
    LINK_PATTERN         = r'<(?:td|TD).*?>\s*(?:<.+>\s*)?<a href="(.+?)".*?>.+?(?:</a>)?\s*(?:<.+>\s*)?</(?:td|TD)>'

    OFFLINE_PATTERN      = r'>\s*(No such user|\w+ (Not Found|file (was|has been) removed|no longer available))'
    TEMP_OFFLINE_PATTERN = r'>\s*\w+ server (is in )?(maintenance|maintainance)'


    def _set_xfs_cookie(self):
        cookie = (self.PLUGIN_DOMAIN, "lang", "english")
        if isinstance(self.COOKIES, list) and cookie not in self.COOKIES:
            self.COOKIES.insert(cookie)
        else:
            set_cookie(self.req.cj, *cookie)


    def prepare(self):
        if not self.PLUGIN_DOMAIN:
            self.fail(_("Missing PLUGIN DOMAIN"))

        if self.COOKIES:
            self._set_xfs_cookie()

        super(XFSCrypter, self).prepare()
