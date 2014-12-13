# -*- coding: utf-8 -*-

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class XFSCrypter(SimpleCrypter):
    __name    = "XFSCrypter"
    __type    = "crypter"
    __version = "0.04"

    __pattern = r'^unmatchable$'

    __description = """XFileSharing decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = None
    HOSTER_NAME = None

    URL_REPLACEMENTS = [(r'&?per_page=\d+', ""), (r'[?/&]+$', ""), (r'(.+/[^?]+)$', r'\1?'), (r'$', r'&per_page=10000')]

    COOKIES = [(HOSTER_DOMAIN, "lang", "english")]

    LINK_PATTERN = r'<(?:td|TD).*?>\s*<a href="(.+?)".*?>.+?(?:</a>)?\s*</(?:td|TD)>'
    NAME_PATTERN = r'<[tT]itle>.*?\: (?P<N>.+) folder</[tT]itle>'

    OFFLINE_PATTERN      = r'>\s*\w+ (Not Found|file (was|has been) removed)'
    TEMP_OFFLINE_PATTERN = r'>\s*\w+ server (is in )?(maintenance|maintainance)'
