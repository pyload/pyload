# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class JunocloudMe(XFSPHoster):
    __name__ = "JunocloudMe"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:\w+\.)?junocloud\.me/\w{12}'

    __description__ = """Junoclud.me hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = ("guidobelix", "guidobelix@hotmail.it")


    HOSTER_NAME = "junocloud.me"

    FILE_URL_REPLACEMENTS = [(r'//(junocloud)', r'//dl3.\1')]
    FILE_NAME_PATTERN = r'<p class="request_file">http://junocloud.me/w{12}/(?P<N>.+?)</p>'
    FILE_SIZE_PATTERN = r'<p class="request_filesize">Size: (?P<S>[\d.]+) (?P<U>\w+)</p>'

    OFFLINE_PATTERN = r'>No such file with this filename<'
    TEMP_OFFLINE_PATTERN = r'The page may have been renamed, removed or be temporarily unavailable.<'


    def handleFree(self):
        # This line is required due to the getURL workaround. Can be removed in 0.4.10
        self.html = self.load(self.pyfile.url, decode=not self.TEXT_ENCODING)
        url = self.getDownloadLink()
        self.logDebug("Download URL: %s" % url)
        self.startDownload(url)


getInfo = create_getInfo(JunocloudMe)
