# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class IFileWs(XFileSharingPro):
    __name__ = "IFileWs"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?ifile\.ws/\w+(/.+)?"
    __version__ = "0.01"
    __description__ = """Ifile.ws hoster plugin"""
    __author_name__ = ("z00nx")
    __author_mail__ = ("z00nx0@gmail.com")

    FILE_INFO_PATTERN = '<h1\s+style="display:inline;">(?P<N>[^<]+)</h1>\s+\[(?P<S>[^]]+)\]'
    FILE_OFFLINE_PATTERN = 'File Not Found|The file was removed by administrator'
    HOSTER_NAME = "ifile.ws"
    LONG_WAIT_PATTERN = "(?P<M>\d(?=\s+minutes)).*(?P<S>\d+(?=\s+seconds))"


getInfo = create_getInfo(IFileWs)
