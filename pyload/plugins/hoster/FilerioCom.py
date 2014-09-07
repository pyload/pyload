# -*- coding: utf-8 -*-

from pyload.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class FilerioCom(XFileSharingPro):
    __name__ = "FilerioCom"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?(filerio\.(in|com)|filekeen\.com)/\w{12}'

    __description__ = """FileRio.in hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    HOSTER_NAME = "filerio.in"

    OFFLINE_PATTERN = r'<b>&quot;File Not Found&quot;</b>|File has been removed due to Copyright Claim'
    FILE_URL_REPLACEMENTS = [(r'http://.*?/', 'http://filerio.in/')]


    def setup(self):
        self.resumeDownload = self.multiDL = self.premium


getInfo = create_getInfo(FilerioCom)
