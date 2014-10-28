# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class XFSPCrypter(SimpleCrypter):
    __name__    = "XFSPCrypter"
    __type__    = "crypter"
    __version__ = "0.02"

    __pattern__ = None

    __description__ = """XFileSharingPro decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_NAME = None

    URL_REPLACEMENTS = [(r'[?/&]+$', r''), (r'(.+/[^?]*)$', r'\1?'), (r'$', r'&per_page=10000')]

    COOKIES = [(HOSTER_NAME, "lang", "english")]

    LINK_PATTERN = r'<(?:td|TD) [^>]*>\s*<a href="(.+?)"[^>]*>.+?(?:</a>)?\s*</(?:td|TD)>'
    TITLE_PATTERN = r'<[tT]itle>.*?\: (.+) folder</[tT]itle>'

    OFFLINE_PATTERN = r'>\s*\w+ (Not Found|file (was|has been) removed)'
    TEMP_OFFLINE_PATTERN = r'>\s*\w+ server (is in )?(maintenance|maintainance)'
