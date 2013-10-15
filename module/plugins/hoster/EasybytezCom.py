# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class EasybytezCom(XFileSharingPro):
    __name__ = "EasybytezCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?easybytez.com/(\w+).*"
    __version__ = "0.18"
    __description__ = """easybytez.com"""
    __author_name__ = ("zoidberg", "stickell", "Walter Purcaro")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it", "vuolter@gmail.com")

    FILE_INFO_PATTERN = r'<span class="name">(?P<N>.+)</span><br>\s*<span class="size">(?P<S>[^<]+)</span>'
    FILE_OFFLINE_PATTERN = r'<h1>File not available</h1>'

    DIRECT_LINK_PATTERN = r'(http://(\w+\.(easyload|easybytez|zingload)\.(com|to)|\d+\.\d+\.\d+\.\d+)/files/\d+/\w+/[^"<]+)'
    OVR_DOWNLOAD_LINK_PATTERN = r'<h2>Download Link</h2>\s*<textarea[^>]*>([^<]+)'
    OVR_KILL_LINK_PATTERN = r'<h2>Delete Link</h2>\s*<textarea[^>]*>([^<]+)'
    ERROR_PATTERN = r'(?:class=["\']err["\'][^>]*>|<Center><b>)(.*?)</'

    HOSTER_NAME = "easybytez.com"

    def setup(self):
        if self.premium:
            return
        self.resumeDownload = False
        self.chunkLimit = 1
        #: limitDL seems not working in pyload 0.4.9, so try to bypass it setting multiDL dynamically
        #self.limitDL = [True for account in self.account.getAllAccounts() if account["valid"] and account["trafficleft"]].count(True)
        #self.logDebug("DL limit = %s" % self.limitDL)
        accounts = [True for account in self.account.getAllAccounts() if account["valid"] and account["trafficleft"]].count(True)
        dl_active = [True for x in self.core.threadManager.threads if x.active and x.active.hasPlugin() and x.active.pluginname == self.__name__].count(True)
        self.multiDL = True if accounts - dl_active else False


getInfo = create_getInfo(EasybytezCom)
