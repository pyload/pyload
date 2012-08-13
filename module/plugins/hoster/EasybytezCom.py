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

import re
from random import random
from pycurl import LOW_SPEED_TIME
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class EasybytezCom(XFileSharingPro):
    __name__ = "EasybytezCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?easybytez.com/(\w+).*"
    __version__ = "0.11"
    __description__ = """easybytez.com"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>[^"]+)"'
    FILE_SIZE_PATTERN = r'You have requested <font color="red">[^<]+</font> \((?P<S>[^<]+)\)</font>'
    FILE_INFO_PATTERN = r'<tr><td align=right><b>Filename:</b></td><td nowrap>(?P<N>[^<]+)</td></tr>\s*.*?<small>\((?P<S>[^<]+)\)</small>'
    FILE_OFFLINE_PATTERN = r'<h1>File not available</h1>'    
    
    DIRECT_LINK_PATTERN = r'(http://(\w+\.easybytez\.com|\d+\.\d+\.\d+\.\d+)/files/\d+/\w+/[^"<]+)'
    OVR_DOWNLOAD_LINK_PATTERN = r'<h2>Download Link</h2>\s*<textarea[^>]*>([^<]+)'
    OVR_KILL_LINK_PATTERN = r'<h2>Delete Link</h2>\s*<textarea[^>]*>([^<]+)'
    
    HOSTER_NAME = "easybytez.com"
    
    def setup(self):
        self.resumeDownload = self.multiDL = self.premium

    def handlePremium(self):
        self.html = self.load(self.pyfile.url, post = self.getPostParameters())
        found = re.search(self.DIRECT_LINK_PATTERN, self.html)
        if not found: self.parseError('DIRECT LINK')
        self.startDownload(found.group(1))

    def handleOverriden(self):
        self.html = self.load("http://www.%s/" % self.HOSTER_NAME)
        action, inputs =  self.parseHtmlForm('')
        upload_id = "%012d" % int(random()*10**12)
        action += upload_id + "&js_on=1&utype=prem&upload_type=url"
        inputs['tos'] = '1'
        inputs['url_mass'] = self.pyfile.url
        inputs['up1oad_type'] = 'url'

        self.logDebug(action, inputs)
        #wait for file to upload to easybytez.com
        self.req.http.c.setopt(LOW_SPEED_TIME, 600)
        self.html = self.load(action, post = inputs)

        action, inputs = self.parseHtmlForm('F1')
        if not inputs: self.parseError('TEXTAREA')
        self.logDebug(inputs)
        if inputs['st'] == 'OK':
            self.html = self.load(action, post = inputs)
        elif inputs['st'] == 'Can not leech file':
            self.retry(max_tries=20, wait_time=180, reason=inputs['st'])
        else:
            self.fail(inputs['st'])    
        
        #get easybytez.com link for uploaded file
        found = re.search(self.OVR_DOWNLOAD_LINK_PATTERN, self.html)
        if not found: self.parseError('DIRECT LINK (OVR)')
        self.pyfile.url = found.group(1)
        self.retry()

getInfo = create_getInfo(EasybytezCom)