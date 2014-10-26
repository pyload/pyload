# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo
from module.network.RequestFactory import getURL
from random import randrange
from module.common.json_layer import json_loads


def getInfo(urls):
    for url in urls:
        headers = getURL(url, just_header=True)
        if 'HTTP/1.1 404 Not Found' in headers:
            file_info = (url, 0, 1, url)
        else:
            file_info = parseFileInfo(DodanePl, url, getURL(url))
        print(file_info)
        yield file_info


class DodanePl(SimpleHoster):
    __name__ = "DodanePl"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(www\.)?dodane\.pl/file/(?P<ID>\d+)/\S+'

    __description__ = """Dodane.pl hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("z00nx", "z00nx0@gmail.com")]

    FILE_NAME_PATTERN = r'<div\sclass="filetitle">\s+<h1>\s+(?P<N>[^<]+)</h1>\s+</div>'
    FILE_SIZE_PATTERN = r'Wielkość: <span>(?P<S>[^<]+)</span>'
    OFFLINE_PATTERN = r'Plik o podanym adresie nie został odnaleziony'

    def handleFree(self):
        # NOTE: Adapted from http://dodane.pl/static/js/Download.js's downloadFile function
        rand_str = '%030x' % randrange(16 ** 30)
        json = self.load('http://dodane.pl/transfer/create_session/%s/%s' % (self.file_info['ID'], rand_str))
        json = json_loads(json)
        self.download('http://%s/download/%s/%s/%s' % (json['downloadServerAddr'], self.file_info['ID'], json['id'], json['sessionToken']))
