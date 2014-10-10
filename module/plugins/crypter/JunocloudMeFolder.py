# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class JunocloudMeFolder(SimpleCrypter):
    __name__ = " JunocloudMeFolder "
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?junocloud\.me/users/(?P<ID>\d+/\d+)'

    __description__ = """ Junocloud.me folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]


    URL_REPLACEMENTS = [(__pattern__, r"http://www.junocloud.me/users/\g<ID>?per_page=10000")]

    LINK_PATTERN = r'<td><a href="(http://www\.junocloud\.me/\w+)" target="_blank">.+(?:</a>)?</td>'
    TITLE_PATTERN = r'<Title>Files of \d+: (.+) folder</Title>'

    LOGIN_ACCOUNT = True

