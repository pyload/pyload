# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class EasybytezComFolder(SimpleCrypter):
    __name__ = "EasybytezComFolder"
    __type__ = "crypter"
    __version__ = "0.06"

    __pattern__ = r'http://(?:www\.)?easybytez\.com/users/(?P<ID>\d+/\d+)'

    __description__ = """Easybytez.com decrypter plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    URL_REPLACEMENTS = [(__pattern__, r"http://www.easybytez.com/users/\g<ID>?per_page=10000")]

    LINK_PATTERN = r'<td><a href="(http://www\.easybytez\.com/\w+)" target="_blank">.+(?:</a>)?</td>'
    TITLE_PATTERN = r'<Title>Files of \d+: (?P<title>.+) folder</Title>'
