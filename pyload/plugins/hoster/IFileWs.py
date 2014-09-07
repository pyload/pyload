# -*- coding: utf-8 -*-

from pyload.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class IFileWs(XFileSharingPro):
    __name__ = "IFileWs"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?ifile\.ws/\w+(/.+)?'

    __description__ = """Ifile.ws hoster plugin"""
    __author_name__ = "z00nx"
    __author_mail__ = "z00nx0@gmail.com"

    HOSTER_NAME = "ifile.ws"

    FILE_INFO_PATTERN = r'<h1\s+style="display:inline;">(?P<N>[^<]+)</h1>\s+\[(?P<S>[^]]+)\]'
    OFFLINE_PATTERN = r'File Not Found|The file was removed by administrator'


getInfo = create_getInfo(IFileWs)
