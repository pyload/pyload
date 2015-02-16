# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster


class SecureUploadEu(XFSHoster):
    __name__    = "SecureUploadEu"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'https?://(?:www\.)?secureupload\.eu/\w{12}'

    __description__ = """SecureUpload.eu hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("z00nx", "z00nx0@gmail.com")]


    INFO_PATTERN = r'<h3>Downloading (?P<N>[^<]+) \((?P<S>[^<]+)\)</h3>'
